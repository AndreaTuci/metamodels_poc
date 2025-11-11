from django.core.management.base import BaseCommand, CommandError
from dynamic_models.dynamic_manager import dynamic_model_manager
from django.utils import timezone
import os


class Command(BaseCommand):
    help = 'Gestisce i backup del database per i modelli dinamici'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['list', 'create', 'restore', 'cleanup'],
            help='Azione da eseguire'
        )
        
        parser.add_argument(
            '--backup-path',
            help='Percorso del backup da ripristinare (per restore)'
        )
        
        parser.add_argument(
            '--model-name',
            help='Nome del modello per cui creare un backup (per create)'
        )
        
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Numero di giorni di backup da mantenere (per cleanup)'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'list':
            self._list_backups()
        elif action == 'create':
            self._create_backup(options.get('model_name'))
        elif action == 'restore':
            self._restore_backup(options.get('backup_path'))
        elif action == 'cleanup':
            self._cleanup_backups(options['days'])

    def _list_backups(self):
        """Lista tutti i backup disponibili"""
        self.stdout.write(self.style.SUCCESS('📋 Lista backup disponibili:'))
        self.stdout.write('')
        
        backups = dynamic_model_manager.list_backups()
        
        if not backups:
            self.stdout.write(self.style.WARNING('Nessun backup trovato.'))
            return
        
        for i, backup in enumerate(backups, 1):
            self.stdout.write(f"{i}. {backup['backup_path']}")
            self.stdout.write(f"   📅 Data: {backup['timestamp']}")
            self.stdout.write(f"   🔧 Operazione: {backup['operation']}")
            if backup.get('model_name'):
                self.stdout.write(f"   📊 Modello: {backup['model_name']}")
            self.stdout.write('')

    def _create_backup(self, model_name):
        """Crea un nuovo backup"""
        try:
            backup_path = dynamic_model_manager._create_backup('manual', model_name)
            if backup_path:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Backup creato con successo: {backup_path}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Impossibile creare il backup')
                )
        except Exception as e:
            raise CommandError(f'Errore durante la creazione del backup: {e}')

    def _restore_backup(self, backup_path):
        """Ripristina un backup"""
        if not backup_path:
            raise CommandError('Specificare il percorso del backup con --backup-path')
        
        # Conferma dall'utente
        confirm = input(
            f"⚠️  ATTENZIONE: Questa operazione sovrascriverà il database corrente!\n"
            f"Ripristinare il backup {backup_path}? (sì/no): "
        )
        
        if confirm.lower() not in ['sì', 'si', 'yes', 'y']:
            self.stdout.write(self.style.WARNING('Operazione annullata.'))
            return
        
        try:
            dynamic_model_manager.restore_backup(backup_path)
            self.stdout.write(
                self.style.SUCCESS(f'✅ Database ripristinato da: {backup_path}')
            )
        except Exception as e:
            raise CommandError(f'Errore durante il ripristino: {e}')

    def _cleanup_backups(self, days):
        """Pulisce i backup più vecchi di N giorni"""
        try:
            dynamic_model_manager._cleanup_old_backups(days)
            self.stdout.write(
                self.style.SUCCESS(f'🗑️  Cleanup completato. Rimossi i backup più vecchi di {days} giorni.')
            )
        except Exception as e:
            raise CommandError(f'Errore durante il cleanup: {e}')