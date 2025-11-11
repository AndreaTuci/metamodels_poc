DOCUMENTAZIONE - App `dynamic_models`
===================================

Indice
------

- Scopo del progetto
- Panoramica architetturale
- Componenti principali (file e responsabilità)
  - `models.py`
  - `admin.py`
  - `dynamic_manager.py`
  - `api_views.py`
  - `data_views.py`
  - `forms.py`
  - `templates/` e `static/`
  - `templatetags/`
  - `migrations/`
- Flussi principali
  - Creazione di un MetaModel (definizione)
  - Creazione fisica della tabella (Create Table)
  - Aggiornamento struttura (Update Table)
  - Gestione dati (Admin UI personalizzata e API)
  - Relazioni tra modelli dinamici e modelli Django
- Come funzionano le migrazioni (stato attuale e raccomandazioni)
- Caratteristiche ORM supportate
- Note su sicurezza, backup e produzione
- Come estendere e punti di attenzione
- Esempi rapidi di utilizzo (Admin + API)


Scopo del progetto
------------------

L'app `dynamic_models` è una proof-of-concept per la gestione di "meta-modelli": definizioni di modelli che possono essere create e modificate a runtime dall'interfaccia amministrativa. L'obiettivo è permettere ad un superadmin di definire strutture dati (modelli) da pannello e successivamente creare tabelle, inserire dati e esporre API per un backoffice headless.


Panoramica architetturale
-------------------------

L'app è composta da codice Django standard esteso con logica dinamica che genera classi `Model` a runtime, registra queste classi nell'app registry e crea (o aggiorna) le tabelle usando `connection.schema_editor()`.

Flusso essenziale:
- Definisci MetaModel e MetaField via Admin (o API)
- Premi "Crea Tabella" per generare la tabella fisica nel database
- I modelli vengono registrati in `apps` e possono essere usati dall'ORM e dalle API


Componenti principali
---------------------

### `models.py`

Responsabilità:
- `MetaModel`: rappresenta la definizione di un modello dinamico (nome, table_name, description, is_active, timestamp)
- `MetaField`: rappresenta i campi del MetaModel (nome, tipo, parametri, opzioni relazionali e ordinamento)
- Logica per convertire `MetaField` in istanze di campi Django (`get_django_field()`)
- Gestione dei tipi relazionali (ForeignKey, ManyToMany, OneToOne) con supporto a placeholder quando il modello di destinazione è definito ma non ancora registrato

Note tecniche:
- Per relazioni, `related_model` può contenere `app_label.ModelName` (per modelli Django esistenti) o `ModelName` (per modelli dinamici)
- `MetaField.clean()` valida i parametri e permette di salvare campi relazionali anche quando il modello di destinazione è ancora solo un `MetaModel` non registrato (usa un "placeholder" internamente)


### `admin.py`

Responsabilità:
- Personalizza l'interfaccia admin per `MetaModel` e `MetaField`
- Aggiunge pulsanti per azioni custom: `Crea Tabella`, `Aggiorna Tabella`, `Gestisci Dati`
- Integra un mixin per aggiungere una sezione "Modelli Dinamici" nella sidebar dell'admin
- Usa form personalizzati (`forms.py`) per fornire una select/autocompletamento dei modelli disponibili per i campi relazionali
- Include JS statico (`static/admin/js/dynamic_field_admin.js`) che mostra/nasconde i campi relazionali e abilita/disabilita campi nel form


### `dynamic_manager.py`

Responsabilità:
- Core della gestione dinamica dei modelli
- `register_model(meta_model)`: costruisce la classe Python `type` del modello, la registra nell'app config (`apps.get_app_config`) e (opzionalmente) la registra nell'admin
- `create_table(meta_model)`: crea fisicamente la tabella via `connection.schema_editor().create_model(model_class)`
- `update_table(meta_model)`: attualmente ricrea la tabella (drop + create), commentato come PoC; in produzione bisogna implementare un confronto e migrazioni incrementali
- `drop_table(meta_model)`: elimina la tabella e rimuove il modello dall'app registry
- `get_model(name)`: recupera la classe registrata dall'`apps` registry
- `load_all_models()`: carica tutti i MetaModel attivi all'avvio

Limitazioni note:
- Attualmente non vengono generate file di migrazione Django. Viene usato direttamente `schema_editor`.
- `update_table` fa drop+create (perdita dati) — da sostituire con un motore di migrazione (vedi raccomandazioni)


### `api_views.py`

Responsabilità:
- Espone API per gestire MetaModel (via `MetaModelViewSet`) e per operare sui dati dinamici (via `DynamicModelViewSet`)
- `MetaModelViewSet` offre azioni aggiuntive: `create_table`, `update_table`, `drop_table`, `schema`
- `DynamicModelViewSet` costruisce dinamicamente un `ModelSerializer` basato sulla classe del modello generata a runtime e usa `self.model_class.objects` per le operazioni CRUD


### `data_views.py`

Responsabilità:
- Fornisce views admin-like per gestire i record dei modelli dinamici (list, add, edit, delete, export)
- Usa `modelform_factory` per generare form runtime basati sul modello registrato
- Implementa ricerca sui campi di tipo testo definiti nel `MetaModel`
- Usa template dedicati dentro `templates/admin/dynamic_models/`


### `forms.py`

Responsabilità:
- Form admin custom per `MetaField` e inline
- `RelatedModelChoiceField` crea dinamicamente scelte per modelli Django comuni e per MetaModel dinamici attivi
- Garantisce che i campi relazionali non possano essere salvati senza una destinazione selezionata


### `templates/` e `static/`

- Template per l'interfaccia di gestione dati: `data_list.html`, `data_form.html`, `data_delete.html`
- Static JS: `static/admin/js/dynamic_field_admin.js` per UX nell'admin
- `templatetags/dynamic_tags.py` con utilità per i template (lookup dinamico, formatting)


Flussi principali (dettagliati)
------------------------------

### 1) Creazione di un MetaModel (definizione)

1. Dal pannello admin (o API) il superadmin crea un `MetaModel` (nome, table_name, description).
2. Aggiunge `MetaField` tramite l'inline. Per i campi relazionali seleziona `related_model` dalla dropdown.
3. I `MetaField` vengono validati tramite `clean()`; se la destinazione è un `MetaModel` non ancora registrato, la validazione accetta un placeholder.
4. Il `MetaModel` rimmarrà fino a quando l'admin non clicca `Crea Tabella`.


### 2) Creazione fisica della tabella ("Crea Tabella")

1. L'admin clicca "Crea Tabella" dal pannello `MetaModel`.
2. `dynamic_manager.create_table(meta_model)`:
   - chiama `register_model(meta_model)` per costruire la classe Python e registrarla in `apps`
   - entra in `connection.schema_editor()` e chiama `schema_editor.create_model(model_class)`
3. La tabella viene creata immediatamente nel DB. Il modello è ora disponibile a `apps.get_model('dynamic_models', ModelName)` e l'ORM può essere usato su di esso.


### 3) Aggiornamento struttura ("Aggiorna Tabella")

- Stato PoC: `update_table()` rimuove e ricrea la tabella (DROP + CREATE). Questo causa perdita di dati.
- Raccomandazione: implementare un differenziatore di schema (compare old/new) e usare `AddField`, `AlterField`, `RemoveField` con migrazioni generate o usare `schema_editor` per cambi incrementali.


### 4) Gestione dati

- Admin: `Gestisci Dati` apre una UI personalizzata che usa `modelform_factory` per generare form based-on runtime model
- API: `DynamicModelViewSet` espone CRUD che usa la `model_class` runtime e serializers costruiti dinamicamente. È possibile usare filtri, ricerca, ordering e paginazione.


### 5) Relazioni tra modelli dinamici e modelli Django

- Per relazioni verso modelli Django esistenti, usa `app_label.ModelName` (es. `auth.User`).
- Per relazioni verso altri meta-modelli dinamici, usa `ModelName` (es. `Product`).
- Se il modello dinamico target esiste come `MetaModel` ma non è registrato, il sistema crea un placeholder per permettere il salvataggio del `MetaField`.
- Quando poi viene creata la tabella target, la relazione viene risolta tramite riferimento lazy (`'dynamic_models.ModelName'`).


Migrazioni: stato attuale e raccomandazioni
-----------------------------------------

Stato attuale:
- Non vengono generati file di migrazione per i modelli dinamici.
- Le modifiche al DB avvengono tramite `schema_editor` al momento della chiamata `create_table()` o `update_table()`.

Conseguenze:
- Nessuna traccia storica delle modifiche schema in `migrations/` (tracciabilità ridotta)
- `update_table()` può causare perdita di dati (implementazione attuale)

Raccomandazioni per produzione:
- Implementare un generatore di migrazioni dinamiche (es. usare `MigrationWriter` o `migrations.Migration` API) e applicare con `MigrationExecutor`/`call_command('migrate')`.
- Oppure implementare un differenziatore schema che applichi operazioni `AddField`, `AlterField`, `RemoveField` tramite `schema_editor` senza drop della tabella.
- Tenere backup automatici DB prima di ogni modifica struttura.


Compatibilità ORM
-----------------

I modelli dinamici registrati sono vere classi Django `Model` e supportano tutte le API dell'ORM: `objects`, `filter`, `get`, `annotate`, `aggregate`, `select_related`, `prefetch_related`, ecc.


Note su sicurezza, backup e produzione
-------------------------------------

- Esegui backup DB automatici prima di applicare cambi strutturali
- Proteggi gli endpoint API con permessi (attualmente molte view sono limitate a staff/admin)
- Valida input JSON nei parametri `field_params` per evitare injection o valori non validi
- Gestisci i permessi CRUD sui meta-modelli (es. solo superadmin può creare modelli) e su chi può creare tabelle


Come estendere e punti di attenzione
-----------------------------------

- Migrazioni dinamiche: progettare un meccanismo che generi migration files e li applichi con `migrate` per storicizzare le modifiche
- Locking: evitare race condition quando più admin modificano lo stesso MetaModel
- Transactional schema changes: alcune DB (es. PostgreSQL) supportano alcune operazioni in transaction; pianifica rollback
- UI: aggiungere autocomplete per `related_model`, preview dello schema SQL generato, approvazioni workflow


Esempi rapidi
-------------

1) Dal pannello Admin, crea `MetaModel` "Product" con `table_name = products` e aggiungi campi `title (char)`, `price (decimal)`.
2) Clicca "Crea Tabella". La tabella `products` verrà creata.
3) Usa `/api/data/Product/` per creare record. Usa ORM `Product = dynamic_model_manager.get_model('Product')` per operare in Python.


Contatti e next steps
---------------------

- Per trasformare il PoC in soluzione di produzione consiglio di iniziare dal meccanismo di migrazione dinamica. Posso fornire una proposta di implementazione per:
  - generazione di migration files
  - applicazione incrementale delle modifiche
  - safe-updates per campi esistenti


---

File creato da automazione: `dynamic_models/DOCUMENTATION.md`