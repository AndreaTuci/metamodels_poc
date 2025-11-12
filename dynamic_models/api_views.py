from rest_framework import viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Model
from .models import MetaModel, MetaField
from .dynamic_manager import dynamic_model_manager


class MetaModelSerializer(serializers.ModelSerializer):
    meta_fields = serializers.SerializerMethodField()
    
    class Meta:
        model = MetaModel
        fields = ['id', 'name', 'table_name', 'description', 'is_active', 
                  'meta_fields', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_meta_fields(self, obj):
        return MetaFieldSerializer(obj.fields.all(), many=True).data


class MetaFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetaField
        fields = ['id', 'name', 'field_type', 'verbose_name', 'help_text',
                  'required', 'unique', 'default_value', 'field_params', 'order']


class MetaModelViewSet(viewsets.ModelViewSet):
    """
    ViewSet per gestire i MetaModel (definizioni dei modelli)
    """
    queryset = MetaModel.objects.all()
    serializer_class = MetaModelSerializer
    
    def get_permissions(self):
        """
        Istanzia e restituisce la lista delle permissions richieste per questa view.
        """
        if self.action in ['list', 'retrieve', 'schema']:
            # Per la lettura basta essere autenticati
            permission_classes = [IsAuthenticated]
        else:
            # Per le operazioni di scrittura serve essere admin
            permission_classes = [IsAdminUser]
        
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['post'])
    def create_table(self, request, pk=None):
        """
        Crea fisicamente la tabella nel database
        
        POST /api/meta-models/{id}/create_table/
        """
        meta_model = self.get_object()
        
        try:
            model_class = dynamic_model_manager.create_table(meta_model)
            return Response({
                'status': 'success',
                'message': f'Tabella "{meta_model.table_name}" creata con successo',
                'model': meta_model.name
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def update_table(self, request, pk=None):
        """
        Aggiorna la struttura della tabella
        
        POST /api/meta-models/{id}/update_table/
        """
        meta_model = self.get_object()
        
        try:
            model_class = dynamic_model_manager.update_table(meta_model)
            return Response({
                'status': 'success',
                'message': f'Tabella "{meta_model.table_name}" aggiornata con successo'
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'])
    def drop_table(self, request, pk=None):
        """
        Elimina la tabella dal database
        
        DELETE /api/meta-models/{id}/drop_table/
        """
        meta_model = self.get_object()
        
        try:
            dynamic_model_manager.drop_table(meta_model)
            return Response({
                'status': 'success',
                'message': f'Tabella "{meta_model.table_name}" eliminata con successo'
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def schema(self, request):
        """
        Restituisce lo schema di tutti i modelli dinamici
        
        GET /api/meta-models/schema/
        """
        active_models = self.queryset.filter(is_active=True)
        schema = {}
        
        for meta_model in active_models:
            schema[meta_model.name] = {
                'table_name': meta_model.table_name,
                'description': meta_model.description,
                'api_endpoints': {
                    'list': f'/api/data/{meta_model.name}/',
                    'detail': f'/api/data/{meta_model.name}/{{id}}/',
                    'admin_interface': f'/dynamic_models/data/{meta_model.id}/',
                },
                'fields': {
                    field.name: {
                        'type': field.field_type,
                        'required': field.required,
                        'unique': field.unique,
                        'verbose_name': field.verbose_name or field.name,
                        'help_text': field.help_text,
                        'default_value': field.default_value,
                        'params': field.field_params
                    }
                    for field in meta_model.fields.all()
                }
            }
        
        return Response({
            'models': schema,
            'endpoints': {
                'meta_models': '/api/meta-models/',
                'schema': '/api/meta-models/schema/',
            }
        })


class DynamicModelViewSet(viewsets.ModelViewSet):
    """
    ViewSet generico per gestire i dati dei modelli dinamici
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # Supporto per file upload
    
    def get_permissions(self):
        """
        Istanzia e restituisce la lista delle permissions richieste per questa view.
        """
        if self.action in ['list', 'retrieve']:
            # Per la lettura basta essere autenticati
            permission_classes = [IsAuthenticated]
        else:
            # Per le operazioni di scrittura serve essere admin
            permission_classes = [IsAdminUser]
        
        return [permission() for permission in permission_classes]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.meta_model = None
        self.model_class = None
    
    def initial(self, request, *args, **kwargs):
        """
        Inizializza il viewset caricando il modello dinamico
        """
        super().initial(request, *args, **kwargs)
        
        # Ottieni il nome del modello dall'URL
        model_name = kwargs.get('model_name')
        
        if model_name:
            try:
                self.meta_model = MetaModel.objects.get(name=model_name, is_active=True)
                self.model_class = dynamic_model_manager.get_model(model_name)
                
                if not self.model_class:
                    raise ValueError(f"Modello '{model_name}' non caricato")
                    
            except MetaModel.DoesNotExist:
                raise serializers.ValidationError(f"MetaModel '{model_name}' non trovato")
    
    def get_queryset(self):
        """Restituisce il queryset del modello dinamico"""
        if self.model_class:
            return self.model_class.objects.all()
        return Model.objects.none()
    
    def get_serializer_class(self):
        """Crea dinamicamente un serializer per il modello"""
        if not self.model_class:
            return serializers.Serializer
        
        # Controlla se ci sono campi file/image nel modello
        has_file_fields = False
        if self.meta_model:
            has_file_fields = any(field.field_type in ['file', 'image'] 
                                for field in self.meta_model.fields.all())
        
        # Crea un serializer dinamico
        meta_class = type('Meta', (), {
            'model': self.model_class,
            'fields': '__all__'
        })
        
        serializer_attrs = {'Meta': meta_class}
        
        # Se ci sono campi file, aggiungi metodi per gestirli correttamente
        if has_file_fields:
            def to_representation(self, instance):
                """Override per gestire la rappresentazione dei file"""
                ret = super(type(self), self).to_representation(instance)
                
                # Converti i percorsi dei file in URL complete
                from django.conf import settings
                from django.utils.html import format_html
                
                for field in self.Meta.model._meta.get_fields():
                    if hasattr(field, 'upload_to') and field.name in ret:
                        file_value = ret[field.name]
                        if file_value:
                            if not file_value.startswith('http'):
                                ret[field.name] = settings.MEDIA_URL + file_value
                
                return ret
            
            serializer_attrs['to_representation'] = to_representation
        
        serializer_class = type(
            f'{self.model_class.__name__}Serializer',
            (serializers.ModelSerializer,),
            serializer_attrs
        )
        
        return serializer_class
    
    def get_serializer(self, *args, **kwargs):
        """Override per gestire validazione dei campi"""
        serializer_class = self.get_serializer_class()
        kwargs.setdefault('context', self.get_serializer_context())
        return serializer_class(*args, **kwargs)


# Factory function per creare viewset per modello specifico
def create_dynamic_viewset(meta_model_name):
    """
    Crea un ViewSet specifico per un modello dinamico
    
    Args:
        meta_model_name: Nome del MetaModel
    
    Returns:
        Classe ViewSet configurata
    """
    class SpecificDynamicViewSet(DynamicModelViewSet):
        def initial(self, request, *args, **kwargs):
            super().initial(request, *args, **kwargs)
            kwargs['model_name'] = meta_model_name
            super().initial(request, *args, **kwargs)
    
    return SpecificDynamicViewSet