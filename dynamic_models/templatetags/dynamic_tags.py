from django import template

register = template.Library()


@register.filter
def lookup(obj, attr):
    """
    Template filter per accedere dinamicamente agli attributi di un oggetto.
    Uso: {{ object|lookup:"field_name" }}
    """
    try:
        return getattr(obj, attr)
    except AttributeError:
        return None


@register.filter
def field_type_icon(field_type):
    """
    Restituisce un'icona CSS appropriata per il tipo di campo
    """
    icons = {
        'char': 'text',
        'text': 'align-left',
        'integer': 'hash',
        'decimal': 'calculator',
        'boolean': 'check-square',
        'date': 'calendar',
        'datetime': 'calendar-alt',
        'email': 'at',
        'url': 'link',
        'foreign_key': 'arrow-right',
    }
    return icons.get(field_type, 'question')


@register.filter
def field_widget_class(field_type):
    """
    Restituisce la classe CSS appropriata per il widget del campo
    """
    classes = {
        'text': 'vLargeTextField',
        'email': 'vTextField',
        'url': 'vURLField',
        'integer': 'vIntegerField',
        'decimal': 'vFloatField',
        'date': 'vDateField',
        'datetime': 'vDateTimeField',
        'boolean': 'vCheckboxField',
        'foreign_key': 'vForeignKeyField',
    }
    return classes.get(field_type, 'vTextField')


@register.simple_tag
def field_display_value(record, field):
    """
    Formatta il valore di un campo per la visualizzazione
    """
    value = getattr(record, field.name, None)
    
    if value is None:
        return '-'
    
    if field.field_type == 'boolean':
        return '✓' if value else '✗'
    elif field.field_type == 'url' and value:
        return f'<a href="{value}" target="_blank">{value}</a>'
    elif field.field_type == 'email' and value:
        return f'<a href="mailto:{value}">{value}</a>'
    elif isinstance(value, str) and len(value) > 50:
        return value[:47] + '...'
    
    return str(value)


@register.inclusion_tag('admin/dynamic_models/field_help.html')
def field_help(field):
    """
    Mostra l'help per un campo specifico
    """
    return {
        'field': field,
        'help_text': field.help_text,
        'field_type': field.field_type,
        'required': field.required,
    }