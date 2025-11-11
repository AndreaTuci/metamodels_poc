# Generated migration for relation fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dynamic_models', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='metafield',
            name='related_model',
            field=models.CharField(blank=True, help_text="Nome del modello di destinazione (es. 'User' per auth.User o 'Product' per modello dinamico)", max_length=100),
        ),
        migrations.AddField(
            model_name='metafield',
            name='relation_type',
            field=models.CharField(blank=True, choices=[('foreign_key', 'Foreign Key (1 a molti)'), ('many_to_many', 'Many to Many'), ('one_to_one', 'One to One')], help_text='Tipo di relazione (solo per campi relazionali)', max_length=20),
        ),
        migrations.AddField(
            model_name='metafield',
            name='on_delete',
            field=models.CharField(blank=True, choices=[('CASCADE', 'CASCADE - Elimina record collegati'), ('PROTECT', 'PROTECT - Impedisce eliminazione'), ('SET_NULL', 'SET_NULL - Imposta NULL'), ('SET_DEFAULT', 'SET_DEFAULT - Imposta valore default'), ('DO_NOTHING', 'DO_NOTHING - Non fa nulla')], default='CASCADE', help_text='Comportamento alla cancellazione (solo per ForeignKey e OneToOne)', max_length=20),
        ),
        migrations.AddField(
            model_name='metafield',
            name='related_name',
            field=models.CharField(blank=True, help_text='Nome per la relazione inversa (opzionale)', max_length=100),
        ),
        migrations.AlterField(
            model_name='metafield',
            name='field_type',
            field=models.CharField(choices=[('char', 'Testo breve'), ('text', 'Testo lungo'), ('integer', 'Numero intero'), ('decimal', 'Numero decimale'), ('boolean', 'Booleano'), ('date', 'Data'), ('datetime', 'Data e ora'), ('foreign_key', 'Chiave esterna (1 a molti)'), ('many_to_many', 'Relazione molti a molti'), ('one_to_one', 'Relazione uno a uno'), ('email', 'Email'), ('url', 'URL')], max_length=20),
        ),
    ]