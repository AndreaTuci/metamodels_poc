Setup Sistema Modelli Dinamici Django
Guida completa per configurare il sistema di creazione modelli dinamici.

📋 Prerequisiti
Python 3.8+
Django 4.0+
Django REST Framework 3.14+
PostgreSQL (consigliato) o MySQL/SQLite
🚀 Installazione
1. Crea un nuovo progetto Django (o usa uno esistente)
bash
# Crea progetto
django-admin startproject metamodel_poc
cd metamodel_poc

# Crea virtual environment
python -m venv venv
source venv/bin/activate  # Su Windows: venv\Scripts\activate

# Installa dipendenze
pip install django djangorestframework psycopg2-binary
2. Crea l'app dynamic_models
bash
python manage.py startapp dynamic_models
3. Struttura dei file
Organizza i file creati in questa struttura:

metamodel_poc/
├── manage.py
├── metamodel_poc/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── dynamic_models/
    ├── __init__.py
    ├── models.py              # Codice "models.py - Meta Model System"
    ├── admin.py               # Codice "admin.py - Django Admin Integration"
    ├── apps.py                # Codice "apps.py - App Configuration"
    ├── dynamic_manager.py     # Codice "dynamic_manager.py"
    ├── api_views.py           # Codice "api_views.py - DRF Dynamic API"
    ├── urls.py                # Codice "urls.py - URL Configuration"
    └── esempio_utilizzo.py    # Codice "esempio_utilizzo.py"
4. Configura settings.py
python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',
    
    # Local apps
    'dynamic_models.apps.DynamicModelsConfig',  # IMPORTANTE: usa DynamicModelsConfig
]

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50
}

# Database - Esempio con PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'metamodel_db',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Se usi SQLite per test (più semplice per PoC)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
5. Configura urls.py principale
python
# metamodel_poc/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dynamic_models.urls')),
    path('api-auth/', include('rest_framework.urls')),
]
6. Applica le migrazioni
bash
# Crea le migrazioni per dynamic_models
python manage.py makemigrations dynamic_models

# Applica tutte le migrazioni
python manage.py migrate

# Crea un superuser
python manage.py createsuperuser
7. Avvia il server
bash
python manage.py runserver
🎯 Test del sistema
Opzione A: Via Django Admin
Vai su http://localhost:8000/admin/
Login con le credenziali superuser
Vai su "Meta Models" → "Add Meta Model"
Crea un modello (es: "Product")
Aggiungi campi al modello
Clicca su "Crea Tabella"
Clicca su "Gestisci Dati" per inserire record
Opzione B: Via Django Shell
bash
python manage.py shell
python
from dynamic_models.esempio_utilizzo import run_complete_example
run_complete_example()
Opzione C: Via API REST
Usa Postman, curl o qualsiasi client HTTP:

bash
# 1. Login per ottenere il token (se usi token authentication)
# oppure usa session authentication

# 2. Crea un MetaModel
curl -X POST http://localhost:8000/api/meta-models/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Product",
    "table_name": "dynamic_products",
    "description": "Modello prodotti"
  }'

# 3. Ottieni l'ID del modello creato, poi crea la tabella
curl -X POST http://localhost:8000/api/meta-models/1/create_table/

# 4. Inserisci dati
curl -X POST http://localhost:8000/api/data/Product/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Laptop",
    "price": 999.99
  }'
🔧 Troubleshooting
Problema: "No such table: dynamic_models_metamodel"
Soluzione: Hai dimenticato di eseguire le migrazioni:

bash
python manage.py makemigrations dynamic_models
python manage.py migrate
Problema: "Modello non trovato dopo la creazione"
Soluzione: Riavvia il server Django:

bash
# Ctrl+C per fermare
python manage.py runserver
Il sistema carica i modelli dinamici all'avvio dell'app (in apps.py).

Problema: Errore nel JSONField
Soluzione: Se usi versioni vecchie di Django, usa:

python
from django.db.models import JSONField  # Django 3.1+
# oppure
from django.contrib.postgres.fields import JSONField  # Django < 3.1 con PostgreSQL
Problema: "Permission denied" sulle API
Soluzione: Assicurati di essere autenticato come admin. Modifica temporaneamente:

python
# In api_views.py
permission_classes = [IsAdminUser]  # Cambia in []
🎨 Personalizzazioni
Aggiungere nuovi tipi di campo
In models.py, aggiungi alla lista FIELD_TYPES:

python
FIELD_TYPES = [
    # ... campi esistenti ...
    ('file', 'File Upload'),
    ('image', 'Immagine'),
]
Poi in MetaField.get_django_field() aggiungi il case:

python
elif self.field_type == 'file':
    return models.FileField(upload_to='uploads/', **field_kwargs)
Personalizzare l'Admin dinamico
In admin.py, nella funzione manage_data_view(), personalizza:

python
dynamic_admin = type(
    f'{meta_model.name}Admin',
    (admin.ModelAdmin,),
    {
        'list_display': [...],
        'list_filter': [...],
        'search_fields': [...],
        # Aggiungi altre opzioni
    }
)
📚 Prossimi Passi
Validazione avanzata: Aggiungi validatori custom ai campi
Relazioni: Implementa ForeignKey tra modelli dinamici
Permessi: Aggiungi controllo accessi granulare
History: Traccia modifiche con django-simple-history
API GraphQL: Integra con Graphene-Django
Export/Import: Aggiungi funzionalità di backup/restore
⚠️ Limitazioni attuali
Migrazioni manuali: Serve restart dopo creazione modelli
Nessun rollback: Le modifiche alla struttura sono destructive
Performance: Query su modelli con molti campi potrebbero essere lente
Relazioni complesse: ForeignKey tra modelli dinamici non completamente implementato
🔄 Integrazione con Camomilla
Per integrare nel tuo CMS:

Copia i file nella struttura di Camomilla
Registra l'app in INSTALLED_APPS
Crea migrazioni nel database di Camomilla
Adatta l'admin di Camomilla per includere questi modelli
Eventualmente, crea widget custom per il pannello di Camomilla
📧 Supporto
Per domande o problemi, apri un issue o contatta il team di sviluppo.

Versione: 1.0.0
Data: Novembre 2025
Licenza: MIT

