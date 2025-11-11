from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .dynamic_manager import dynamic_model_manager
import json
import os


@staff_member_required
def backup_management_view(request):
    """Vista per gestire i backup dall'interfaccia admin"""
    
    context = {
        'title': 'Gestione Backup Database',
        'backups': dynamic_model_manager.list_backups(),
    }
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create_backup':
            model_name = request.POST.get('model_name', '')
            try:
                backup_path = dynamic_model_manager._create_backup('manual', model_name or None)
                if backup_path:
                    messages.success(request, f'Backup creato con successo: {backup_path}')
                else:
                    messages.error(request, 'Impossibile creare il backup')
            except Exception as e:
                messages.error(request, f'Errore durante la creazione del backup: {e}')
        
        elif action == 'cleanup_backups':
            days = int(request.POST.get('days', 7))
            try:
                dynamic_model_manager._cleanup_old_backups(days)
                messages.success(request, f'Cleanup completato. Rimossi i backup più vecchi di {days} giorni.')
            except Exception as e:
                messages.error(request, f'Errore durante il cleanup: {e}')
        
        return redirect('admin:backup_management')
    
    return render(request, 'admin/backup_management.html', context)


@staff_member_required
@require_POST
def restore_backup_view(request):
    """Vista per ripristinare un backup"""
    backup_path = request.POST.get('backup_path')
    
    if not backup_path:
        return JsonResponse({'error': 'Percorso backup non specificato'}, status=400)
    
    if not os.path.exists(backup_path):
        return JsonResponse({'error': 'File di backup non trovato'}, status=404)
    
    try:
        dynamic_model_manager.restore_backup(backup_path)
        return JsonResponse({
            'success': True, 
            'message': f'Database ripristinato da: {backup_path}'
        })
    except Exception as e:
        return JsonResponse({
            'error': f'Errore durante il ripristino: {e}'
        }, status=500)


@staff_member_required
def backup_status_api(request):
    """API per ottenere lo stato dei backup"""
    try:
        backups = dynamic_model_manager.list_backups()
        backup_dir = dynamic_model_manager._backup_dir
        
        # Calcola dimensione totale dei backup
        total_size = 0
        if os.path.exists(backup_dir):
            for filename in os.listdir(backup_dir):
                filepath = os.path.join(backup_dir, filename)
                if os.path.isfile(filepath):
                    total_size += os.path.getsize(filepath)
        
        # Converte dimensione in MB
        total_size_mb = round(total_size / (1024 * 1024), 2)
        
        return JsonResponse({
            'total_backups': len(backups),
            'total_size_mb': total_size_mb,
            'backup_dir': backup_dir,
            'backups': backups[:5]  # Ultimi 5 backup
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)