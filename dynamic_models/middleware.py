from django.utils.deprecation import MiddlewareMixin
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import MetaModel, MetaField
from .dynamic_manager import dynamic_model_manager


class SchemaChangeMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware per monitorare le modifiche ai MetaModel e attivare backup automatici
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.setup_signals()
    
    def setup_signals(self):
        """Configura i segnali per monitorare le modifiche"""
        
        @receiver(post_save, sender=MetaModel)
        def on_metamodel_change(sender, instance, created, **kwargs):
            """Gestisce le modifiche ai MetaModel"""
            if created:
                print(f"📊 Nuovo MetaModel creato: {instance.name}")
            else:
                print(f"📝 MetaModel modificato: {instance.name}")
                # Il backup viene già creato nei metodi create_table/update_table
        
        @receiver(post_save, sender=MetaField)
        def on_metafield_change(sender, instance, created, **kwargs):
            """Gestisce le modifiche ai MetaField"""
            if created:
                print(f"🔧 Nuovo campo creato: {instance.name} in {instance.meta_model.name}")
            else:
                print(f"✏️  Campo modificato: {instance.name} in {instance.meta_model.name}")
                
            # Attiva l'aggiornamento della tabella quando un campo viene modificato
            try:
                dynamic_model_manager.update_table(instance.meta_model)
            except Exception as e:
                print(f"❌ Errore durante l'aggiornamento della tabella: {e}")
        
        @receiver(pre_delete, sender=MetaField)
        def on_metafield_delete(sender, instance, **kwargs):
            """Gestisce la cancellazione di MetaField"""
            print(f"🗑️  Campo in cancellazione: {instance.name} da {instance.meta_model.name}")
            
            # Crea backup prima della cancellazione del campo
            try:
                backup_path = dynamic_model_manager._create_backup(
                    "delete_field", 
                    f"{instance.meta_model.name}_{instance.name}"
                )
                if backup_path:
                    print(f"💾 Backup creato prima della cancellazione: {backup_path}")
            except Exception as e:
                print(f"⚠️  Errore durante il backup prima della cancellazione: {e}")
        
        @receiver(pre_delete, sender=MetaModel)
        def on_metamodel_delete(sender, instance, **kwargs):
            """Gestisce la cancellazione di MetaModel"""
            print(f"🗑️  MetaModel in cancellazione: {instance.name}")
            
            # Crea backup prima della cancellazione del modello
            try:
                backup_path = dynamic_model_manager._create_backup(
                    "delete_model", 
                    instance.name
                )
                if backup_path:
                    print(f"💾 Backup creato prima della cancellazione: {backup_path}")
            except Exception as e:
                print(f"⚠️  Errore durante il backup prima della cancellazione: {e}")


def register_schema_monitoring():
    """
    Funzione helper per registrare il monitoraggio delle modifiche allo schema
    Può essere chiamata durante l'inizializzazione dell'app
    """
    middleware = SchemaChangeMonitoringMiddleware(None)
    middleware.setup_signals()
    print("🔍 Monitoraggio delle modifiche allo schema attivato")