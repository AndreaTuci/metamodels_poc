from django.apps import apps
from django.db import connection, migrations
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.state import ProjectState
from django.core.management import call_command
from django.db.migrations.operations import CreateModel, AddField, RemoveField
import os
import sys


class DynamicModelManager:
    """
    Gestisce la creazione e registrazione di modelli Django dinamici
    """
    
    def __init__(self):
        self.app_label = 'dynamic_models'
        self.registered_models = {}
    
    def register_model(self, meta_model, register_in_admin=True):
        """
        Registra un modello dinamico nell'app registry di Django
        
        Args:
            meta_model: Istanza di MetaModel
            register_in_admin: Se True, registra anche nell'admin per la sidebar
        
        Returns:
            La classe del modello Django creata
        """
        model_class = meta_model.create_model_class()
        
        # Registra il modello nell'app
        app_config = apps.get_app_config(self.app_label)
        
        # Rimuovi il modello esistente se presente
        if meta_model.name in app_config.models:
            del app_config.models[meta_model.name.lower()]
        
        # Registra il nuovo modello
        app_config.models[meta_model.name.lower()] = model_class
        
        # Registra nell'admin per apparire in sidebar
        if register_in_admin:
            self._register_in_admin(meta_model, model_class)
        
        # Memorizza nella cache
        self.registered_models[meta_model.name] = model_class
        
        return model_class
    
    def _register_in_admin(self, meta_model, model_class):
        """
        Registra il modello dinamico nell'admin per la sidebar
        """
        from django.contrib import admin
        
        # Rimuovi registrazione esistente se presente
        if model_class in admin.site._registry:
            admin.site.unregister(model_class)
        
        # Crea una classe admin dinamica
        field_names = [field.name for field in meta_model.fields.all()]
        if 'id' not in field_names:
            list_display = ['id'] + field_names[:4]
        else:
            list_display = field_names[:5]
        
        search_fields = [field.name for field in meta_model.fields.all() 
                        if field.field_type in ['char', 'text', 'email']]
        
        list_filter = [field.name for field in meta_model.fields.all() 
                      if field.field_type in ['boolean', 'foreign_key']][:3]
        
        dynamic_admin_class = type(
            f'{meta_model.name}Admin',
            (admin.ModelAdmin,),
            {
                'list_display': list_display,
                'search_fields': search_fields,
                'list_filter': list_filter,
                'list_per_page': 25,
                'ordering': ['-id'],
                'readonly_fields': ['id'] if 'id' in field_names else [],
            }
        )
        
        # Registra nell'admin
        admin.site.register(model_class, dynamic_admin_class)
    
    def create_table(self, meta_model):
        """
        Crea fisicamente la tabella nel database
        
        Args:
            meta_model: Istanza di MetaModel
        """
        model_class = self.register_model(meta_model)
        
        # Crea la migrazione a runtime
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(model_class)
        
        return model_class
    
    def update_table(self, meta_model):
        """
        Aggiorna la struttura della tabella esistente
        
        Args:
            meta_model: Istanza di MetaModel
        """
        model_class = self.register_model(meta_model)
        
        # Qui dovremmo confrontare lo stato attuale con quello desiderato
        # e applicare le modifiche necessarie (add/remove/alter fields)
        # Per il PoC, ricreiamo la tabella
        
        with connection.schema_editor() as schema_editor:
            # In produzione, qui faresti un confronto intelligente
            # Per ora, drop e recreate (ATTENZIONE: perde i dati!)
            try:
                schema_editor.delete_model(model_class)
            except:
                pass
            
            schema_editor.create_model(model_class)
        
        return model_class
    
    def drop_table(self, meta_model):
        """
        Elimina la tabella dal database
        
        Args:
            meta_model: Istanza di MetaModel
        """
        model_class = meta_model.get_model_class()
        
        if model_class:
            with connection.schema_editor() as schema_editor:
                schema_editor.delete_model(model_class)
            
            # Rimuovi dall'app registry
            app_config = apps.get_app_config(self.app_label)
            if meta_model.name.lower() in app_config.models:
                del app_config.models[meta_model.name.lower()]
            
            if meta_model.name in self.registered_models:
                del self.registered_models[meta_model.name]
    
    def get_model(self, meta_model_name):
        """
        Ottiene la classe del modello dinamico per nome
        
        Args:
            meta_model_name: Nome del MetaModel
        
        Returns:
            Classe del modello Django o None
        """
        try:
            return apps.get_model(self.app_label, meta_model_name)
        except LookupError:
            return None
    
    def load_all_models(self):
        """
        Carica tutti i modelli dinamici definiti nel database
        Questo dovrebbe essere chiamato all'avvio dell'app
        """
        from .models import MetaModel
        
        for meta_model in MetaModel.objects.filter(is_active=True):
            try:
                self.register_model(meta_model)
            except Exception as e:
                print(f"Errore nel caricamento del modello {meta_model.name}: {e}")
    
    def add_field_to_table(self, meta_field):
        """
        Aggiunge un campo a una tabella esistente
        
        Args:
            meta_field: Istanza di MetaField
        """
        model_class = self.get_model(meta_field.meta_model.name)
        
        if not model_class:
            raise ValueError(f"Modello {meta_field.meta_model.name} non trovato")
        
        django_field = meta_field.get_django_field()
        
        with connection.schema_editor() as schema_editor:
            schema_editor.add_field(model_class, django_field)
        
        # Ricarica il modello per includere il nuovo campo
        self.register_model(meta_field.meta_model)
    
    def remove_field_from_table(self, meta_field):
        """
        Rimuove un campo da una tabella esistente
        
        Args:
            meta_field: Istanza di MetaField
        """
        model_class = self.get_model(meta_field.meta_model.name)
        
        if not model_class:
            raise ValueError(f"Modello {meta_field.meta_model.name} non trovato")
        
        field = model_class._meta.get_field(meta_field.name)
        
        with connection.schema_editor() as schema_editor:
            schema_editor.remove_field(model_class, field)
        
        # Ricarica il modello senza il campo rimosso
        self.register_model(meta_field.meta_model)


# Istanza singleton
dynamic_model_manager = DynamicModelManager()