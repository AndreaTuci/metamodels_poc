from django.db import models
from django.contrib.postgres.fields import JSONField
from django.apps import apps
from django.db import connection
from django.core.management import call_command
import importlib


class MetaModel(models.Model):
    """Definizione di un modello dinamico"""
    
    FIELD_TYPES = [
        ('char', 'Testo breve'),
        ('text', 'Testo lungo'),
        ('integer', 'Numero intero'),
        ('decimal', 'Numero decimale'),
        ('boolean', 'Booleano'),
        ('date', 'Data'),
        ('datetime', 'Data e ora'),
        ('foreign_key', 'Relazione'),
        ('email', 'Email'),
        ('url', 'URL'),
        ('file', 'File'),
        ('image', 'Immagine'),
    ]
    
    name = models.CharField(max_length=100, unique=True, help_text="Nome del modello (es. 'Product')")
    table_name = models.CharField(max_length=100, unique=True, help_text="Nome della tabella nel database")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Meta Model"
        verbose_name_plural = "Meta Models"
    
    def __str__(self):
        return self.name
    
    def get_model_class(self):
        """Restituisce la classe del modello dinamico"""
        app_label = 'dynamic_models'
        
        # Controlla se il modello è già registrato
        try:
            return apps.get_model(app_label, self.name)
        except LookupError:
            return None
    
    def create_model_class(self):
        """Crea la classe del modello Django a runtime"""
        app_label = 'dynamic_models'
        
        # Costruisci gli attributi del modello
        attrs = {
            '__module__': f'{app_label}.models',
            'Meta': type('Meta', (), {
                'db_table': self.table_name,
                'app_label': app_label,
            }),
            '__str__': lambda self: f"{self.__class__.__name__} #{self.pk}",
        }
        
        # Aggiungi i campi definiti
        for field in self.fields.all():
            attrs[field.name] = field.get_django_field()
        
        # Crea la classe del modello
        model_class = type(self.name, (models.Model,), attrs)
        
        return model_class


class MetaField(models.Model):
    """Definizione di un campo di un modello dinamico"""
    
    FIELD_TYPES = [
        ('char', 'Testo breve'),
        ('text', 'Testo lungo'),
        ('integer', 'Numero intero'),
        ('decimal', 'Numero decimale'),
        ('boolean', 'Booleano'),
        ('date', 'Data'),
        ('datetime', 'Data e ora'),
        ('foreign_key', 'Chiave esterna (1 a molti)'),
        ('many_to_many', 'Relazione molti a molti'),
        ('one_to_one', 'Relazione uno a uno'),
        ('email', 'Email'),
        ('url', 'URL'),
        ('file', 'File'),
        ('image', 'Immagine'),
    ]
    
    RELATION_DELETE_OPTIONS = [
        ('CASCADE', 'CASCADE - Elimina record collegati'),
        ('PROTECT', 'PROTECT - Impedisce eliminazione'),
        ('SET_NULL', 'SET_NULL - Imposta NULL'),
        ('SET_DEFAULT', 'SET_DEFAULT - Imposta valore default'),
        ('DO_NOTHING', 'DO_NOTHING - Non fa nulla'),
    ]
    
    meta_model = models.ForeignKey(MetaModel, on_delete=models.CASCADE, related_name='fields')
    name = models.CharField(max_length=100, help_text="Nome del campo (es. 'title')")
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    
    # Parametri comuni
    verbose_name = models.CharField(max_length=200, blank=True)
    help_text = models.TextField(blank=True)
    required = models.BooleanField(default=False)
    unique = models.BooleanField(default=False)
    default_value = models.CharField(max_length=500, blank=True)
    
    # Parametri specifici per tipo di campo (stored as JSON)
    field_params = models.JSONField(default=dict, blank=True, help_text="""
        Parametri specifici per tipo:
        - char: max_length
        - decimal: max_digits, decimal_places
        - foreign_key: related_model
    """)
    
    # Campi specifici per relazioni
    related_model = models.CharField(
        max_length=100, 
        blank=True, 
        help_text="Nome del modello di destinazione (es. 'User' per auth.User o 'Product' per modello dinamico)"
    )
    relation_type = models.CharField(
        max_length=20,
        choices=[
            ('foreign_key', 'Foreign Key (1 a molti)'),
            ('many_to_many', 'Many to Many'),
            ('one_to_one', 'One to One'),
        ],
        blank=True,
        help_text="Tipo di relazione (solo per campi relazionali)"
    )
    on_delete = models.CharField(
        max_length=20,
        choices=RELATION_DELETE_OPTIONS,
        default='CASCADE',
        blank=True,
        help_text="Comportamento alla cancellazione (solo per ForeignKey e OneToOne)"
    )
    related_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Nome per la relazione inversa (opzionale)"
    )
    
    # Ordinamento
    order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Meta Field"
        verbose_name_plural = "Meta Fields"
        ordering = ['order', 'id']
        unique_together = [['meta_model', 'name']]
    
    def __str__(self):
        return f"{self.meta_model.name}.{self.name}"
    
    def get_django_field(self):
        """Restituisce un'istanza del campo Django appropriato"""
        field_kwargs = {
            'verbose_name': self.verbose_name or self.name,
            'help_text': self.help_text,
        }
        
        # Per i campi relazionali, gestisci null/blank diversamente
        is_relational = self.field_type in ['foreign_key', 'many_to_many', 'one_to_one']
        
        if not is_relational:
            field_kwargs.update({
                'null': not self.required,
                'blank': not self.required,
                'unique': self.unique,
            })
        
        # Aggiungi default se specificato (non per relazioni)
        if self.default_value and not is_relational:
            field_kwargs['default'] = self._parse_default_value()
        
        # Crea il campo in base al tipo
        if self.field_type == 'char':
            max_length = self.field_params.get('max_length', 255)
            return models.CharField(max_length=max_length, **field_kwargs)
        
        elif self.field_type == 'text':
            return models.TextField(**field_kwargs)
        
        elif self.field_type == 'integer':
            return models.IntegerField(**field_kwargs)
        
        elif self.field_type == 'decimal':
            max_digits = self.field_params.get('max_digits', 10)
            decimal_places = self.field_params.get('decimal_places', 2)
            return models.DecimalField(
                max_digits=max_digits,
                decimal_places=decimal_places,
                **field_kwargs
            )
        
        elif self.field_type == 'boolean':
            return models.BooleanField(**field_kwargs)
        
        elif self.field_type == 'date':
            return models.DateField(**field_kwargs)
        
        elif self.field_type == 'datetime':
            return models.DateTimeField(**field_kwargs)
        
        elif self.field_type == 'email':
            return models.EmailField(**field_kwargs)
        
        elif self.field_type == 'url':
            return models.URLField(**field_kwargs)
        
        elif self.field_type == 'file':
            upload_to = self.field_params.get('upload_to', 'uploads/')
            return models.FileField(upload_to=upload_to, **field_kwargs)
        
        elif self.field_type == 'image':
            upload_to = self.field_params.get('upload_to', 'images/')
            return models.ImageField(upload_to=upload_to, **field_kwargs)
        
        elif self.field_type in ['foreign_key', 'one_to_one', 'many_to_many']:
            return self._create_relational_field(field_kwargs)
        
        # Default fallback
        return models.CharField(max_length=255, **field_kwargs)
    
    def _create_relational_field(self, field_kwargs):
        """Crea un campo relazionale Django"""
        if not self.related_model:
            raise ValueError(f"Campo {self.name}: related_model è obbligatorio per i campi relazionali")
        
        # Ottieni il modello di destinazione
        target_model = self._get_target_model()
        if not target_model:
            raise ValueError(f"Campo {self.name}: modello di destinazione '{self.related_model}' non trovato")
        
        # Se è un placeholder model (modello dinamico non ancora registrato),
        # usa una stringa lazy che verrà risolta quando il modello sarà disponibile
        if hasattr(target_model, '__name__') and target_model.__name__.startswith('Placeholder_'):
            # Usa lazy reference per modelli dinamici non ancora registrati
            target_reference = f'dynamic_models.{self.related_model}'
        else:
            # Usa il modello direttamente se è già registrato
            target_reference = target_model
        
        # Configurazioni specifiche per relazioni
        if self.field_type in ['foreign_key', 'one_to_one']:
            field_kwargs.update({
                'null': not self.required,
                'blank': not self.required,
                'on_delete': getattr(models, self.on_delete, models.CASCADE),
            })
            
            if self.related_name:
                field_kwargs['related_name'] = self.related_name
        
        elif self.field_type == 'many_to_many':
            field_kwargs.update({
                'blank': True,  # M2M sono sempre blank=True
            })
            
            if self.related_name:
                field_kwargs['related_name'] = self.related_name
        
        # Crea il campo appropriato
        if self.field_type == 'foreign_key':
            return models.ForeignKey(target_reference, **field_kwargs)
        elif self.field_type == 'one_to_one':
            return models.OneToOneField(target_reference, **field_kwargs)
        elif self.field_type == 'many_to_many':
            return models.ManyToManyField(target_reference, **field_kwargs)
    
    def _get_target_model(self):
        """Ottiene la classe del modello di destinazione"""
        if not self.related_model:
            return None
        
        # Controlla se è un modello Django standard (formato: app_label.ModelName o ModelName)
        if '.' in self.related_model:
            try:
                app_label, model_name = self.related_model.split('.', 1)
                return apps.get_model(app_label, model_name)
            except (LookupError, ValueError):
                pass
        else:
            # Prova prima nei modelli Django standard comuni
            common_models = [
                ('auth', 'User'),
                ('auth', 'Group'),
                ('contenttypes', 'ContentType'),
            ]
            
            for app_label, model_name in common_models:
                if model_name.lower() == self.related_model.lower():
                    try:
                        return apps.get_model(app_label, model_name)
                    except LookupError:
                        pass
        
        # Controlla se è un modello dinamico già registrato
        try:
            return apps.get_model('dynamic_models', self.related_model)
        except LookupError:
            pass
        
        # Se non è registrato, controlla se esiste un MetaModel con quel nome
        # Questo serve per la validazione durante la creazione dei campi
        try:
            meta_model_exists = MetaModel.objects.filter(
                name=self.related_model, 
                is_active=True
            ).exists()
            
            if meta_model_exists:
                # Restituisci una classe placeholder che indica che il modello esiste
                # ma non è ancora registrato
                return type(f'Placeholder_{self.related_model}', (), {
                    '__module__': 'dynamic_models.models',
                    '_meta': type('Meta', (), {
                        'app_label': 'dynamic_models',
                        'model_name': self.related_model.lower(),
                        'verbose_name': self.related_model,
                    })()
                })
        except:
            # Potrebbe fallire se il database non è pronto
            pass
        
        return None
    
    def get_available_models(self):
        """Restituisce una lista dei modelli disponibili per le relazioni"""
        available_models = []
        
        # Modelli Django standard comuni
        common_models = [
            ('auth.User', 'Utente'),
            ('auth.Group', 'Gruppo'),
            ('contenttypes.ContentType', 'Tipo di Contenuto'),
        ]
        available_models.extend(common_models)
        
        # Modelli dinamici attivi
        for meta_model in MetaModel.objects.filter(is_active=True):
            if meta_model != self.meta_model:  # Evita auto-referenza
                available_models.append((meta_model.name, f"{meta_model.name} (Dinamico)"))
        
        return available_models
    
    def clean(self):
        """Validazione personalizzata del campo"""
        from django.core.exceptions import ValidationError
        errors = {}
        
        # Validazione per campi relazionali
        if self.field_type in ['foreign_key', 'many_to_many', 'one_to_one']:
            if not self.related_model:
                errors['related_model'] = 'Il campo related_model è obbligatorio per i campi relazionali'
            
            # Verifica che il modello di destinazione esista
            if self.related_model:
                target_model = self._get_target_model()
                if not target_model:
                    errors['related_model'] = f'Modello "{self.related_model}" non trovato. Usa il formato "app_label.ModelName" per modelli Django o "ModelName" per modelli dinamici.'
                elif hasattr(target_model, '__name__') and target_model.__name__.startswith('Placeholder_'):
                    # È un placeholder per un modello dinamico valido - OK
                    pass
            
            # Validazione on_delete per ForeignKey e OneToOne
            if self.field_type in ['foreign_key', 'one_to_one']:
                if not self.on_delete:
                    errors['on_delete'] = 'Il comportamento on_delete è obbligatorio per ForeignKey e OneToOne'
            
            # I campi M2M non possono essere required
            if self.field_type == 'many_to_many' and self.required:
                errors['required'] = 'I campi ManyToMany non possono essere obbligatori'
        else:
            # Per campi non relazionali, pulisci i campi relazionali
            if self.related_model:
                self.related_model = ''
            if self.relation_type:
                self.relation_type = ''
            if self.related_name:
                self.related_name = ''
        
        # Validazione nome campo
        if not self.name.isidentifier():
            errors['name'] = 'Il nome del campo deve essere un identificatore Python valido'
        
        if self.name in ['id', 'pk', 'Meta', 'objects', 'save', 'delete']:
            errors['name'] = 'Il nome del campo non può essere una parola riservata di Django'
        
        # Validazione parametri specifici
        if self.field_type == 'char':
            max_length = self.field_params.get('max_length')
            if max_length is not None:
                try:
                    max_length = int(max_length)
                    if max_length <= 0:
                        errors['field_params'] = 'max_length deve essere un numero positivo'
                except (ValueError, TypeError):
                    errors['field_params'] = 'max_length deve essere un numero'
        
        if self.field_type == 'decimal':
            max_digits = self.field_params.get('max_digits')
            decimal_places = self.field_params.get('decimal_places')
            
            if max_digits is not None:
                try:
                    max_digits = int(max_digits)
                    if max_digits <= 0:
                        errors['field_params'] = 'max_digits deve essere un numero positivo'
                except (ValueError, TypeError):
                    errors['field_params'] = 'max_digits deve essere un numero'
            
            if decimal_places is not None:
                try:
                    decimal_places = int(decimal_places)
                    if decimal_places < 0:
                        errors['field_params'] = 'decimal_places non può essere negativo'
                    if max_digits and decimal_places > max_digits:
                        errors['field_params'] = 'decimal_places non può essere maggiore di max_digits'
                except (ValueError, TypeError):
                    errors['field_params'] = 'decimal_places deve essere un numero'
        
        # Validazione parametri per campi file
        if self.field_type in ['file', 'image']:
            upload_to = self.field_params.get('upload_to')
            if upload_to is not None and not isinstance(upload_to, str):
                errors['field_params'] = 'upload_to deve essere una stringa (percorso cartella)'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """Override del save per validazione aggiuntiva"""
        self.clean()
        
        # Sincronizza relation_type con field_type
        if self.field_type in ['foreign_key', 'many_to_many', 'one_to_one']:
            self.relation_type = self.field_type
        
        super().save(*args, **kwargs)
    
    def _parse_default_value(self):
        """Converte il default_value string nel tipo appropriato"""
        if not self.default_value:
            return None
        
        if self.field_type == 'integer':
            return int(self.default_value)
        elif self.field_type == 'decimal':
            return float(self.default_value)
        elif self.field_type == 'boolean':
            return self.default_value.lower() in ('true', '1', 'yes')
        else:
            return self.default_value