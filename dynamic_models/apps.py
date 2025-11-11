from django.apps import AppConfig


class DynamicModelsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dynamic_models'
    verbose_name = 'Modelli Dinamici'
    
    def ready(self):
        """
        Chiamato quando l'app è pronta
        Qui carichiamo tutti i modelli dinamici definiti nel database
        """
        # Import qui per evitare circular imports
        from .dynamic_manager import dynamic_model_manager
        
        # Carica tutti i modelli dinamici all'avvio
        try:
            dynamic_model_manager.load_all_models()
            print("✓ Modelli dinamici caricati con successo")
        except Exception as e:
            # Non fallire se il database non è ancora pronto (es. prima migrazione)
            print(f"⚠ Impossibile caricare i modelli dinamici: {e}")