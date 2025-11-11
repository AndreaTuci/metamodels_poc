from django.contrib import admin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import path
from django.utils.html import format_html
from django.contrib.admin import AdminSite
from .models import MetaModel, MetaField
from .dynamic_manager import dynamic_model_manager
from .forms import MetaFieldAdminForm, MetaFieldInlineForm


# Personalizza l'admin site per aggiungere una sezione "Modelli Dinamici"
class DynamicModelsAdminMixin:
    """
    Mixin per personalizzare l'admin con i modelli dinamici
    """
    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)
        
        # Crea una sezione per i modelli dinamici
        dynamic_models_section = {
            'name': 'Modelli Dinamici',
            'app_label': 'dynamic_models',
            'app_url': '/admin/dynamic_models/',
            'has_module_perms': True,
            'models': []
        }
        
        # Aggiungi i modelli dinamici attivi
        for meta_model in MetaModel.objects.filter(is_active=True):
            model_class = dynamic_model_manager.get_model(meta_model.name)
            if model_class:
                dynamic_models_section['models'].append({
                    'name': meta_model.verbose_name if hasattr(meta_model, 'verbose_name') else meta_model.name,
                    'object_name': meta_model.name,
                    'perms': {'add': True, 'change': True, 'delete': True, 'view': True},
                    'admin_url': f'/dynamic_models/data/{meta_model.id}/',
                    'add_url': f'/dynamic_models/data/{meta_model.id}/add/',
                })
        
        # Aggiungi la sezione se ci sono modelli dinamici
        if dynamic_models_section['models']:
            app_list.append(dynamic_models_section)
        
        return app_list


# Applica il mixin all'admin site principale
admin.site.__class__ = type('DynamicAdminSite', (DynamicModelsAdminMixin, admin.site.__class__), {})


class MetaFieldInline(admin.TabularInline):
    model = MetaField
    form = MetaFieldInlineForm
    extra = 1
    fields = ['name', 'field_type', 'required', 'unique', 'verbose_name', 'help_text', 
             'related_model', 'relation_type', 'on_delete', 'related_name', 'field_params', 'order']
    
    class Media:
        js = ('admin/js/dynamic_field_admin.js',)
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        return formset


@admin.register(MetaModel)
class MetaModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'table_name', 'is_active', 'created_at', 'action_buttons']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'table_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [MetaFieldInline]
    
    fieldsets = (
        ('Informazioni Base', {
            'fields': ('name', 'table_name', 'description', 'is_active')
        }),
        ('Metadati', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def action_buttons(self, obj):
        """Bottoni per azioni personalizzate"""
        if not obj.pk:
            return ''
        
        return format_html(
            '<a class="button" href="{}">Crea Tabella</a> '
            '<a class="button" href="{}">Aggiorna Tabella</a> '
            '<a class="button" href="{}">Gestisci Dati</a>',
            f'create-table/{obj.pk}/',
            f'update-table/{obj.pk}/',
            f'manage-data/{obj.pk}/'
        )
    action_buttons.short_description = 'Azioni'
    
    def get_urls(self):
        """Aggiunge URL personalizzati per le azioni"""
        urls = super().get_urls()
        custom_urls = [
            path('create-table/<int:pk>/', 
                 self.admin_site.admin_view(self.create_table_view),
                 name='metamodel_create_table'),
            path('update-table/<int:pk>/', 
                 self.admin_site.admin_view(self.update_table_view),
                 name='metamodel_update_table'),
            path('manage-data/<int:pk>/', 
                 self.admin_site.admin_view(self.manage_data_view),
                 name='metamodel_manage_data'),
        ]
        return custom_urls + urls
    
    def create_table_view(self, request, pk):
        """Vista per creare la tabella fisica nel database"""
        meta_model = MetaModel.objects.get(pk=pk)
        
        try:
            dynamic_model_manager.create_table(meta_model)
            messages.success(request, f'Tabella "{meta_model.table_name}" creata con successo!')
        except Exception as e:
            messages.error(request, f'Errore nella creazione della tabella: {str(e)}')
        
        return redirect('admin:dynamic_models_metamodel_changelist')
    
    def update_table_view(self, request, pk):
        """Vista per aggiornare la struttura della tabella"""
        meta_model = MetaModel.objects.get(pk=pk)
        
        try:
            dynamic_model_manager.update_table(meta_model)
            messages.success(request, f'Tabella "{meta_model.table_name}" aggiornata con successo!')
        except Exception as e:
            messages.error(request, f'Errore nell\'aggiornamento della tabella: {str(e)}')
        
        return redirect('admin:dynamic_models_metamodel_changelist')
    
    def manage_data_view(self, request, pk):
        """Vista per gestire i dati della tabella dinamica"""
        meta_model = MetaModel.objects.get(pk=pk)
        model_class = dynamic_model_manager.get_model(meta_model.name)
        
        if not model_class:
            messages.error(request, f'Modello "{meta_model.name}" non trovato. Crea prima la tabella.')
            return redirect('admin:dynamic_models_metamodel_changelist')
        
        # Redirect alla nostra interfaccia personalizzata per la gestione dati
        return redirect('dynamic_data_list', meta_model_id=meta_model.pk)
    
    def save_model(self, request, obj, form, change):
        """Override per gestire il salvataggio"""
        super().save_model(request, obj, form, change)
        
        # Suggerisci di creare la tabella se è un nuovo modello
        if not change:
            messages.info(request, 
                         'Modello salvato! Usa il bottone "Crea Tabella" per creare la tabella nel database.')
    
    class Media:
        css = {
            'all': ('admin/css/custom_metamodel.css',)
        }


@admin.register(MetaField)
class MetaFieldAdmin(admin.ModelAdmin):
    form = MetaFieldAdminForm
    list_display = ['name', 'meta_model', 'field_type', 'required', 'unique', 'related_model', 'relation_type', 'order']
    list_filter = ['field_type', 'required', 'unique', 'meta_model', 'relation_type']
    search_fields = ['name', 'meta_model__name', 'verbose_name', 'related_model']
    
    fieldsets = (
        ('Campo Base', {
            'fields': ('meta_model', 'name', 'field_type', 'verbose_name', 'help_text')
        }),
        ('Vincoli', {
            'fields': ('required', 'unique', 'default_value')
        }),
        ('Relazioni', {
            'fields': ('related_model', 'relation_type', 'on_delete', 'related_name'),
            'classes': ('collapse',),
            'description': 'Configurazione per campi relazionali (ForeignKey, ManyToMany, OneToOne)'
        }),
        ('Parametri Specifici', {
            'fields': ('field_params',),
            'classes': ('collapse',),
            'description': 'JSON con parametri specifici per tipo di campo. Es: {"max_length": 100}'
        }),
        ('Ordinamento', {
            'fields': ('order',)
        }),
    )
    
    class Media:
        js = ('admin/js/dynamic_field_admin.js',)


# Aggiungi link personalizzato per gestione backup nell'admin
def backup_management_link():
    """Link per accedere alla gestione backup"""
    from django.urls import reverse
    from django.utils.html import format_html
    
    return format_html(
        '<a href="{}">💾 Gestione Backup Database</a>',
        reverse('backup_management')
    )

# Personalizza l'admin per aggiungere link alla gestione backup
from django.contrib.admin import AdminSite
from django.contrib import admin

# Override del template admin per aggiungere link backup
def custom_admin_index(request):
    """Vista personalizzata per l'indice admin"""
    context = admin.site.each_context(request)
    context['backup_management_url'] = '/dynamic_models/backup-management/'
    return admin.site.index(request, extra_context=context)