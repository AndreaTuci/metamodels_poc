from django.apps import apps
from django.db import connection, migrations
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.state import ProjectState
from django.core.management import call_command
from django.db.migrations.operations import CreateModel, AddField, RemoveField
import os
import sys
import shutil
import datetime
import json


class DynamicModelManager:
    """
    Gestisce la creazione e registrazione di modelli Django dinamici
    """
    
    def __init__(self):
        self.app_label = 'dynamic_models'  # Torna al normale app_label
        self.registered_models = {}
        self._backup_dir = "db_backups"
        self._ensure_backup_dir()

    def _ensure_backup_dir(self):
        """Assicura che la directory di backup esista"""
        if not os.path.exists(self._backup_dir):
            os.makedirs(self._backup_dir)

    def _cleanup_old_backups(self, keep_days=7):
        """Rimuove i backup più vecchi di keep_days giorni"""
        if not os.path.exists(self._backup_dir):
            return
            
        cutoff_time = datetime.datetime.now() - datetime.timedelta(days=keep_days)
        
        for filename in os.listdir(self._backup_dir):
            filepath = os.path.join(self._backup_dir, filename)
            if os.path.isfile(filepath):
                file_time = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_time < cutoff_time:
                    try:
                        os.remove(filepath)
                        print(f"🗑️  Backup obsoleto rimosso: {filename}")
                    except OSError:
                        pass

    def _create_backup(self, operation_type, model_name=None):
        """Crea un backup del database prima delle modifiche"""
        # Cleanup dei backup vecchi
        self._cleanup_old_backups()
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Nome del file di backup
        if model_name:
            backup_filename = f"backup_{operation_type}_{model_name}_{timestamp}.sqlite3"
        else:
            backup_filename = f"backup_{operation_type}_{timestamp}.sqlite3"
        
        backup_path = os.path.join(self._backup_dir, backup_filename)
        
        # Copia il database
        db_path = None
        db_settings = connection.settings_dict
        
        if db_settings['ENGINE'] == 'django.db.backends.sqlite3':
            db_path = db_settings['NAME']
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_path)
                print(f"✅ Backup creato: {backup_path}")
                
                # Salva metadati del backup
                metadata = {
                    'timestamp': timestamp,
                    'operation': operation_type,
                    'model_name': model_name,
                    'db_path': str(db_path),
                    'backup_path': str(backup_path)
                }
                
                metadata_path = backup_path.replace('.sqlite3', '_metadata.json')
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                return backup_path
        
        print(f"⚠️  Backup non disponibile per questo tipo di database: {db_settings['ENGINE']}")
        return None
    
    def register_model(self, meta_model, register_in_admin=False):  # Default False per evitare duplicati
        """
        Registra un modello dinamico nell'app registry di Django
        
        Args:
            meta_model: Istanza di MetaModel
            register_in_admin: Se True, registra anche nell'admin per la sidebar
        
        Returns:
            La classe del modello Django creata
        """
        model_class = meta_model.create_model_class()
        
        # Registra il modello nell'app - prima rimuovi se esiste
        app_config = apps.get_app_config(self.app_label)
        
        # Rimuovi il modello esistente se presente
        model_key = meta_model.name.lower()
        if model_key in app_config.models:
            old_model = app_config.models[model_key]
            # Rimuovi dall'admin se registrato
            from django.contrib import admin
            if old_model in admin.site._registry:
                admin.site.unregister(old_model)
            del app_config.models[model_key]
        
        # Registra il nuovo modello
        app_config.models[model_key] = model_class
        
        # Registra nell'admin solo se esplicitamente richiesto
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
        print(f"🔧 Creazione tabella per {meta_model.name}...")
        
        # Crea backup prima di creare la tabella
        backup_path = self._create_backup("create_table", meta_model.name)
        
        try:
            model_class = self.register_model(meta_model)
            
            # Crea la migrazione a runtime
            with connection.schema_editor() as schema_editor:
                schema_editor.create_model(model_class)
            
            print(f"✅ Tabella {meta_model.table_name} creata con successo!")
            return model_class
            
        except Exception as e:
            print(f"❌ Errore durante la creazione della tabella: {e}")
            if backup_path:
                print(f"💾 Backup disponibile in: {backup_path}")
            raise
    
    def update_table(self, meta_model):
        """
        Aggiorna la struttura della tabella esistente senza perdere dati
        
        Args:
            meta_model: Istanza di MetaModel
        """
        print(f"🔧 Aggiornamento sicuro tabella per {meta_model.name}...")
        
        # Crea backup prima di modificare
        backup_path = self._create_backup("update_table", meta_model.name)
        
        try:
            model_class = self.register_model(meta_model)
            
            # Controllo se la tabella esiste
            table_exists = self._table_exists(meta_model.table_name)
            
            if not table_exists:
                # Se la tabella non esiste, creala
                return self.create_table(meta_model)
            
            # Confronta lo schema esistente con quello desiderato
            current_schema = self._get_current_table_schema(meta_model.table_name)
            desired_schema = self._get_desired_schema(meta_model)
            
            # Calcola le differenze
            schema_diff = self._calculate_schema_diff(current_schema, desired_schema)
            
            # Applica le modifiche incrementali
            self._apply_schema_changes(meta_model, model_class, schema_diff)
            
            print(f"✅ Tabella {meta_model.table_name} aggiornata con successo!")
            return model_class
            
        except Exception as e:
            print(f"❌ Errore durante l'aggiornamento della tabella: {e}")
            if backup_path:
                print(f"💾 Backup disponibile in: {backup_path}")
            raise
    
    def _table_exists(self, table_name):
        """Controlla se una tabella esiste nel database"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=%s;
            """, [table_name])
            return cursor.fetchone() is not None
    
    def _get_current_table_schema(self, table_name):
        """Ottiene lo schema corrente della tabella"""
        with connection.cursor() as cursor:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            schema = {}
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                not_null = bool(col[3])
                default_value = col[4]
                is_pk = bool(col[5])
                
                schema[col_name] = {
                    'type': col_type,
                    'not_null': not_null,
                    'default': default_value,
                    'primary_key': is_pk
                }
            
            return schema
    
    def _get_desired_schema(self, meta_model):
        """Costruisce lo schema desiderato dal MetaModel"""
        schema = {
            'id': {
                'type': 'integer',
                'not_null': True,
                'default': None,
                'primary_key': True
            }
        }
        
        for field in meta_model.fields.all():
            django_field = field.get_django_field()
            
            # Mappa i tipi Django a SQLite
            field_info = self._django_field_to_db_info(django_field, field)
            schema[field.name] = field_info
        
        return schema
    
    def _django_field_to_db_info(self, django_field, meta_field):
        """Converte un campo Django in informazioni DB"""
        from django.db import models
        
        if isinstance(django_field, models.CharField):
            return {
                'type': f'varchar({django_field.max_length})',
                'not_null': not django_field.null,
                'default': django_field.default if django_field.default != models.NOT_PROVIDED else None,
                'primary_key': False
            }
        elif isinstance(django_field, models.TextField):
            return {
                'type': 'text',
                'not_null': not django_field.null,
                'default': django_field.default if django_field.default != models.NOT_PROVIDED else None,
                'primary_key': False
            }
        elif isinstance(django_field, models.IntegerField):
            return {
                'type': 'integer',
                'not_null': not django_field.null,
                'default': django_field.default if django_field.default != models.NOT_PROVIDED else None,
                'primary_key': False
            }
        elif isinstance(django_field, models.DecimalField):
            return {
                'type': 'decimal',
                'not_null': not django_field.null,
                'default': django_field.default if django_field.default != models.NOT_PROVIDED else None,
                'primary_key': False
            }
        elif isinstance(django_field, models.BooleanField):
            return {
                'type': 'bool',
                'not_null': not django_field.null,
                'default': django_field.default if django_field.default != models.NOT_PROVIDED else None,
                'primary_key': False
            }
        elif isinstance(django_field, (models.DateField, models.DateTimeField)):
            return {
                'type': 'datetime',
                'not_null': not django_field.null,
                'default': django_field.default if django_field.default != models.NOT_PROVIDED else None,
                'primary_key': False
            }
        elif isinstance(django_field, models.EmailField):
            return {
                'type': f'varchar({django_field.max_length})',
                'not_null': not django_field.null,
                'default': django_field.default if django_field.default != models.NOT_PROVIDED else None,
                'primary_key': False
            }
        elif isinstance(django_field, models.URLField):
            return {
                'type': f'varchar({django_field.max_length})',
                'not_null': not django_field.null,
                'default': django_field.default if django_field.default != models.NOT_PROVIDED else None,
                'primary_key': False
            }
        elif isinstance(django_field, (models.ForeignKey, models.OneToOneField)):
            return {
                'type': 'integer',  # Foreign key sono integer
                'not_null': not django_field.null,
                'default': None,
                'primary_key': False,
                'foreign_key': True,
                'related_table': django_field.remote_field.model._meta.db_table if hasattr(django_field.remote_field.model._meta, 'db_table') else None
            }
        else:
            # Default fallback
            return {
                'type': 'text',
                'not_null': not django_field.null,
                'default': None,
                'primary_key': False
            }
    
    def _calculate_schema_diff(self, current_schema, desired_schema):
        """Calcola le differenze tra schema corrente e desiderato"""
        diff = {
            'add_columns': [],
            'drop_columns': [],
            'modify_columns': []
        }
        
        # Campi da aggiungere
        for field_name, field_info in desired_schema.items():
            if field_name not in current_schema:
                diff['add_columns'].append({
                    'name': field_name,
                    'info': field_info
                })
        
        # Campi da rimuovere
        for field_name in current_schema:
            if field_name not in desired_schema and field_name != 'id':
                diff['drop_columns'].append(field_name)
        
        # Campi da modificare (per ora solo rinominazione)
        # Note: SQLite non supporta ALTER COLUMN, quindi modifiche complesse
        # richiederebbero ricreazione tabella
        
        return diff
    
    def _apply_schema_changes(self, meta_model, model_class, schema_diff):
        """Applica le modifiche schema alla tabella"""
        with connection.schema_editor() as schema_editor:
            
            # Aggiungi nuovi campi
            for add_col in schema_diff['add_columns']:
                field_name = add_col['name']
                
                # Trova il MetaField corrispondente
                try:
                    meta_field = meta_model.fields.get(name=field_name)
                    django_field = meta_field.get_django_field()
                    
                    # IMPORTANTE: Imposta il nome del campo
                    django_field.name = field_name
                    django_field.set_attributes_from_name(field_name)
                    
                    # Aggiungi il campo alla tabella
                    schema_editor.add_field(model_class, django_field)
                    print(f"✓ Aggiunto campo '{field_name}' alla tabella '{meta_model.table_name}'")
                    
                except Exception as e:
                    print(f"✗ Errore aggiungendo campo '{field_name}': {e}")
            
            # Rimuovi campi (ATTENZIONE: cancella dati!)
            for drop_col_name in schema_diff['drop_columns']:
                try:
                    # Per SQLite, rimuovere colonne è complesso
                    # Per ora skippiamo, ma in produzione serve backup
                    print(f"⚠ Skipping rimozione campo '{drop_col_name}' (richiede backup)")
                    # schema_editor.remove_field(model_class, old_field)
                    
                except Exception as e:
                    print(f"✗ Errore rimuovendo campo '{drop_col_name}': {e}")
        
        print(f"✓ Schema aggiornato per tabella '{meta_model.table_name}'")
    
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

    def list_backups(self):
        """Lista tutti i backup disponibili con i loro metadati"""
        if not os.path.exists(self._backup_dir):
            return []
            
        backups = []
        for filename in os.listdir(self._backup_dir):
            if filename.endswith('_metadata.json'):
                metadata_path = os.path.join(self._backup_dir, filename)
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                        backups.append(metadata)
                except (json.JSONDecodeError, IOError):
                    continue
        
        # Ordina per timestamp (più recenti prima)
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        return backups

    def restore_backup(self, backup_path):
        """
        Ripristina un backup del database
        
        ATTENZIONE: Questa operazione sovrascriverà il database corrente!
        
        Args:
            backup_path: Percorso al file di backup da ripristinare
        """
        db_settings = connection.settings_dict
        
        if db_settings['ENGINE'] != 'django.db.backends.sqlite3':
            raise ValueError("Il ripristino dei backup è supportato solo per SQLite")
        
        current_db_path = db_settings['NAME']
        
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup non trovato: {backup_path}")
        
        # Crea un backup del database corrente prima del ripristino
        safety_backup = self._create_backup("before_restore")
        
        try:
            # Chiudi tutte le connessioni al database
            from django.db import connections
            connections.close_all()
            
            # Sostituisci il database corrente con il backup
            shutil.copy2(backup_path, current_db_path)
            
            print(f"✅ Database ripristinato da: {backup_path}")
            print(f"💾 Backup di sicurezza creato: {safety_backup}")
            
            return True
            
        except Exception as e:
            print(f"❌ Errore durante il ripristino: {e}")
            if safety_backup:
                print(f"💾 Backup di sicurezza disponibile in: {safety_backup}")
            raise


# Istanza singleton
dynamic_model_manager = DynamicModelManager()