from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.core.paginator import Paginator
from django.db import transaction
from django.forms.models import modelform_factory
from .models import MetaModel, MetaField
from .dynamic_manager import dynamic_model_manager
import json


@staff_member_required
def dynamic_data_list(request, meta_model_id):
    """
    Vista per visualizzare la lista dei dati di un modello dinamico
    """
    meta_model = get_object_or_404(MetaModel, pk=meta_model_id, is_active=True)
    model_class = dynamic_model_manager.get_model(meta_model.name)
    
    if not model_class:
        messages.error(request, f'Modello "{meta_model.name}" non trovato. Crea prima la tabella.')
        return redirect('admin:dynamic_models_metamodel_changelist')
    
    # Ottieni tutti i record
    search_query = request.GET.get('q', '')
    queryset = model_class.objects.all()
    
    # Cerca nei campi di testo se c'è una query
    if search_query:
        from django.db.models import Q
        q_objects = Q()
        
        for field in meta_model.fields.filter(field_type__in=['char', 'text', 'email']):
            q_objects |= Q(**{f"{field.name}__icontains": search_query})
        
        if q_objects:
            queryset = queryset.filter(q_objects)
    
    # Paginazione
    paginator = Paginator(queryset, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Ottieni i campi per la visualizzazione
    fields = meta_model.fields.all()
    
    context = {
        'meta_model': meta_model,
        'fields': fields,
        'page_obj': page_obj,
        'search_query': search_query,
        'total_count': queryset.count(),
    }
    
    return render(request, 'admin/dynamic_models/data_list.html', context)


@staff_member_required
def dynamic_data_add(request, meta_model_id):
    """
    Vista per aggiungere un nuovo record a un modello dinamico
    """
    meta_model = get_object_or_404(MetaModel, pk=meta_model_id, is_active=True)
    model_class = dynamic_model_manager.get_model(meta_model.name)
    
    if not model_class:
        messages.error(request, f'Modello "{meta_model.name}" non trovato. Crea prima la tabella.')
        return redirect('admin:dynamic_models_metamodel_changelist')
    
    # Crea un form dinamicamente
    DynamicForm = modelform_factory(
        model_class,
        fields='__all__',
        exclude=['id']
    )
    
    if request.method == 'POST':
        form = DynamicForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    instance = form.save()
                    messages.success(request, f'Record creato con successo (ID: {instance.pk})')
                    
                    # Redirect alla lista o continua ad aggiungere
                    if '_save_and_add_another' in request.POST:
                        return redirect('dynamic_data_add', meta_model_id=meta_model.pk)
                    else:
                        return redirect('dynamic_data_list', meta_model_id=meta_model.pk)
            except Exception as e:
                messages.error(request, f'Errore durante il salvataggio: {str(e)}')
    else:
        form = DynamicForm()
    
    context = {
        'meta_model': meta_model,
        'form': form,
        'fields': meta_model.fields.all(),
        'title': f'Aggiungi {meta_model.name}',
    }
    
    return render(request, 'admin/dynamic_models/data_form.html', context)


@staff_member_required
def dynamic_data_edit(request, meta_model_id, object_id):
    """
    Vista per modificare un record esistente
    """
    meta_model = get_object_or_404(MetaModel, pk=meta_model_id, is_active=True)
    model_class = dynamic_model_manager.get_model(meta_model.name)
    
    if not model_class:
        messages.error(request, f'Modello "{meta_model.name}" non trovato. Crea prima la tabella.')
        return redirect('admin:dynamic_models_metamodel_changelist')
    
    instance = get_object_or_404(model_class, pk=object_id)
    
    # Crea un form dinamicamente
    DynamicForm = modelform_factory(
        model_class,
        fields='__all__',
        exclude=['id']
    )
    
    if request.method == 'POST':
        form = DynamicForm(request.POST, instance=instance)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    messages.success(request, 'Record aggiornato con successo')
                    return redirect('dynamic_data_list', meta_model_id=meta_model.pk)
            except Exception as e:
                messages.error(request, f'Errore durante il salvataggio: {str(e)}')
    else:
        form = DynamicForm(instance=instance)
    
    context = {
        'meta_model': meta_model,
        'form': form,
        'instance': instance,
        'fields': meta_model.fields.all(),
        'title': f'Modifica {meta_model.name} #{instance.pk}',
    }
    
    return render(request, 'admin/dynamic_models/data_form.html', context)


@staff_member_required
def dynamic_data_delete(request, meta_model_id, object_id):
    """
    Vista per eliminare un record
    """
    meta_model = get_object_or_404(MetaModel, pk=meta_model_id, is_active=True)
    model_class = dynamic_model_manager.get_model(meta_model.name)
    
    if not model_class:
        messages.error(request, f'Modello "{meta_model.name}" non trovato.')
        return redirect('admin:dynamic_models_metamodel_changelist')
    
    instance = get_object_or_404(model_class, pk=object_id)
    
    if request.method == 'POST':
        try:
            instance.delete()
            messages.success(request, 'Record eliminato con successo')
        except Exception as e:
            messages.error(request, f'Errore durante l\'eliminazione: {str(e)}')
        
        return redirect('dynamic_data_list', meta_model_id=meta_model.pk)
    
    context = {
        'meta_model': meta_model,
        'instance': instance,
        'fields': meta_model.fields.all(),
    }
    
    return render(request, 'admin/dynamic_models/data_delete.html', context)


@staff_member_required
def dynamic_data_export(request, meta_model_id):
    """
    Vista per esportare i dati in formato JSON/CSV
    """
    meta_model = get_object_or_404(MetaModel, pk=meta_model_id, is_active=True)
    model_class = dynamic_model_manager.get_model(meta_model.name)
    
    if not model_class:
        return JsonResponse({'error': 'Modello non trovato'}, status=404)
    
    format_type = request.GET.get('format', 'json')
    
    # Ottieni tutti i record
    records = model_class.objects.all()
    fields = meta_model.fields.all()
    
    if format_type == 'json':
        data = []
        for record in records:
            record_data = {'id': record.pk}
            for field in fields:
                value = getattr(record, field.name)
                # Converte datetime e altri tipi non serializzabili
                if hasattr(value, 'isoformat'):
                    value = value.isoformat()
                record_data[field.name] = value
            data.append(record_data)
        
        response = JsonResponse({
            'meta_model': meta_model.name,
            'count': len(data),
            'data': data
        }, json_dumps_params={'indent': 2})
        response['Content-Disposition'] = f'attachment; filename="{meta_model.name}_export.json"'
        return response
    
    # Aggiungi altri formati di export qui (CSV, Excel, etc.)
    return JsonResponse({'error': 'Formato non supportato'}, status=400)