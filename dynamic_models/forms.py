from django import forms
from django.apps import apps
from .models import MetaModel


class RelatedModelChoiceField(forms.ChoiceField):
    """
    Campo per la selezione del modello di destinazione per le relazioni
    """
    
    def __init__(self, *args, **kwargs):
        # Genera le scelte dinamicamente
        choices = self.get_model_choices()
        kwargs['choices'] = choices
        kwargs['required'] = False
        super().__init__(*args, **kwargs)
    
    def get_model_choices(self):
        """Restituisce le scelte dei modelli disponibili"""
        choices = [('', '--- Seleziona un modello ---')]
        
        # Modelli Django standard comuni
        django_models = [
            ('auth.User', 'User (Utente Django)'),
            ('auth.Group', 'Group (Gruppo Django)'),
            ('contenttypes.ContentType', 'ContentType (Tipo di Contenuto)'),
        ]
        
        # Verifica che esistano
        available_django_models = []
        for model_path, label in django_models:
            try:
                app_label, model_name = model_path.split('.')
                apps.get_model(app_label, model_name)
                available_django_models.append((model_path, label))
            except:
                pass
        
        if available_django_models:
            choices.append(('-- Modelli Django --', available_django_models))
        
        # Modelli dinamici attivi
        dynamic_models = []
        try:
            for meta_model in MetaModel.objects.filter(is_active=True).order_by('name'):
                dynamic_models.append((meta_model.name, f'{meta_model.name} (Modello Dinamico)'))
        except:
            # Database potrebbe non essere pronto
            pass
        
        if dynamic_models:
            choices.append(('-- Modelli Dinamici --', dynamic_models))
        
        return choices


class MetaFieldAdminForm(forms.ModelForm):
    """
    Form personalizzato per MetaField nell'admin
    """
    related_model = RelatedModelChoiceField(
        label="Modello di destinazione",
        help_text="Seleziona il modello per la relazione",
        required=False
    )
    
    class Meta:
        from .models import MetaField
        model = MetaField
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Nascondi i campi relazionali se non necessari inizialmente
        relational_fields = ['related_model', 'relation_type', 'on_delete', 'related_name']
        
        if self.instance and self.instance.field_type in ['foreign_key', 'many_to_many', 'one_to_one']:
            # Campo relazionale - mostra i campi
            pass
        else:
            # Non relazionale - nascondi inizialmente (il JS li mostrerà se necessario)
            for field_name in relational_fields:
                if field_name in self.fields:
                    self.fields[field_name].widget.attrs['style'] = 'display: none;'
    
    def clean(self):
        cleaned_data = super().clean()
        field_type = cleaned_data.get('field_type')
        related_model = cleaned_data.get('related_model')
        
        # Validazione per campi relazionali
        if field_type in ['foreign_key', 'many_to_many', 'one_to_one']:
            if not related_model:
                raise forms.ValidationError({
                    'related_model': 'Seleziona un modello di destinazione per i campi relazionali.'
                })
        
        return cleaned_data


class MetaFieldInlineForm(forms.ModelForm):
    """
    Form per MetaField negli inline
    """
    related_model = RelatedModelChoiceField(
        required=False,
        help_text="Modello di destinazione"
    )
    
    class Meta:
        from .models import MetaField
        model = MetaField
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        field_type = cleaned_data.get('field_type')
        related_model = cleaned_data.get('related_model')
        
        # Validazione per campi relazionali
        if field_type in ['foreign_key', 'many_to_many', 'one_to_one']:
            if not related_model:
                raise forms.ValidationError({
                    'related_model': 'Seleziona un modello per i campi relazionali.'
                })
        
        return cleaned_data