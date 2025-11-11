<template>
  <form @submit.prevent="handleSubmit" class="dynamic-form">
    <div v-for="field in fields" :key="field.name" class="form-group">
      <component
        :is="getFieldComponent(field.field_type)"
        :field="field"
        v-model="formValues[field.name]"
        :error="errors[field.name]"
      />
    </div>
    
    <div class="form-actions">
      <button type="button" @click="$emit('cancel')" class="btn btn-secondary">
        Annulla
      </button>
      <button type="submit" class="btn btn-primary" :disabled="isSubmitting">
        <span v-if="isSubmitting">💾 Salvataggio...</span>
        <span v-else>💾 {{ isEditing ? 'Aggiorna' : 'Salva' }}</span>
      </button>
    </div>
  </form>
</template>

<script>
import { defineComponent, ref, reactive, watch } from 'vue'
import CharField from './CharField.vue'
import TextField from './TextField.vue'
import NumberField from './NumberField.vue'
import BooleanField from './BooleanField.vue'
import DateField from './DateField.vue'
import EmailField from './EmailField.vue'
import URLField from './URLField.vue'
import SelectField from './SelectField.vue'

export default defineComponent({
  name: 'DynamicForm',
  components: {
    CharField,
    TextField,
    NumberField,
    BooleanField,
    DateField,
    EmailField,
    URLField,
    SelectField
  },
  emits: ['submit', 'cancel'],
  props: {
    fields: {
      type: Array,
      required: true
    },
    initialValues: {
      type: Object,
      default: () => ({})
    },
    isEditing: {
      type: Boolean,
      default: false
    }
  },
  setup(props, { emit }) {
    const isSubmitting = ref(false)
    const errors = reactive({})
    const formValues = reactive({})

    // Mapping tra Django field types e componenti Vue
    const FIELD_COMPONENT_MAP = {
      'CharField': 'CharField',
      'TextField': 'TextField',  
      'IntegerField': 'NumberField',
      'FloatField': 'NumberField',
      'BooleanField': 'BooleanField',
      'DateField': 'DateField',
      'DateTimeField': 'DateField',
      'EmailField': 'EmailField',
      'URLField': 'URLField',
      'ForeignKey': 'SelectField'
    }

    // Ottiene il componente Vue corretto
    const getFieldComponent = (fieldType) => {
      return FIELD_COMPONENT_MAP[fieldType] || 'CharField'
    }

    // Inizializza i valori del form
    const initFormValues = () => {
      props.fields.forEach(field => {
        formValues[field.name] = props.initialValues[field.name] || getDefaultValue(field.field_type)
      })
    }

    // Ottiene il valore di default per ogni tipo di campo
    const getDefaultValue = (fieldType) => {
      switch (fieldType) {
        case 'BooleanField':
          return false
        case 'IntegerField':
        case 'FloatField':
          return null
        case 'DateField':
        case 'DateTimeField':
          return ''
        default:
          return ''
      }
    }

    // Valida i campi
    const validateForm = () => {
      const newErrors = {}

      props.fields.forEach(field => {
        const value = formValues[field.name]
        if (field.required && (value === null || value === undefined || value === '')) {
          newErrors[field.name] = `Il campo ${field.verbose_name || field.name} è obbligatorio`
        }
      })

      // Copia gli errori nell'oggetto reattivo
      Object.keys(errors).forEach(key => delete errors[key])
      Object.assign(errors, newErrors)

      return Object.keys(newErrors).length === 0
    }

    // Gestisce l'invio del form
    const handleSubmit = async () => {
      if (!validateForm()) return

      isSubmitting.value = true
      try {
        const formData = { ...formValues }
        emit('submit', formData)
      } finally {
        isSubmitting.value = false
      }
    }

    // Osserva i cambiamenti nei valori iniziali
    watch(() => props.initialValues, initFormValues, { immediate: true })

    return {
      formValues,
      errors,
      isSubmitting,
      handleSubmit,
      getFieldComponent
    }
  }
})
</script>

<style scoped>
.dynamic-form {
  max-width: 100%;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background-color: #3b82f6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #2563eb;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: #f1f5f9;
  color: #475569;
  border: 1px solid #cbd5e1;
}

.btn-secondary:hover {
  background-color: #e2e8f0;
}
</style>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import DynamicField from './DynamicField.vue'

const props = defineProps({
  fields: {
    type: Array,
    required: true
  },
  initialData: {
    type: Object,
    default: () => ({})
  },
  isSubmitting: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['submit', 'cancel', 'field-change'])

// Reactive form data
const formData = reactive({})
const errors = reactive({})

// Initialize form data
function initializeFormData() {
  props.fields.forEach(field => {
    formData[field.name] = props.initialData[field.name] || getDefaultValue(field)
  })
}

// Get default value based on field type
function getDefaultValue(field) {
  switch (field.field_type) {
    case 'BooleanField':
      return false
    case 'IntegerField':
    case 'FloatField':
      return null
    case 'DateField':
    case 'DateTimeField':
      return null
    default:
      return ''
  }
}

// Validation
const isValid = computed(() => {
  // Check required fields
  for (const field of props.fields) {
    if (field.required) {
      const value = formData[field.name]
      if (value === null || value === undefined || value === '') {
        return false
      }
    }
  }
  
  // Check for errors
  return Object.keys(errors).length === 0
})

// Validate single field
function validateField(field, value) {
  const fieldErrors = []
  
  // Required validation
  if (field.required && (value === null || value === undefined || value === '')) {
    fieldErrors.push(`${field.verbose_name || field.name} è obbligatorio`)
  }
  
  // Type-specific validation
  if (value !== null && value !== undefined && value !== '') {
    switch (field.field_type) {
      case 'EmailField':
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
          fieldErrors.push('Inserisci un indirizzo email valido')
        }
        break
      case 'URLField':
        try {
          new URL(value)
        } catch {
          fieldErrors.push('Inserisci un URL valido')
        }
        break
      case 'IntegerField':
        if (!Number.isInteger(Number(value))) {
          fieldErrors.push('Deve essere un numero intero')
        }
        break
      case 'FloatField':
        if (isNaN(Number(value))) {
          fieldErrors.push('Deve essere un numero valido')
        }
        break
    }
  }
  
  return fieldErrors
}

// Event handlers
function handleSubmit() {
  // Validate all fields
  let hasErrors = false
  
  props.fields.forEach(field => {
    const fieldErrors = validateField(field, formData[field.name])
    if (fieldErrors.length > 0) {
      errors[field.name] = fieldErrors[0]
      hasErrors = true
    } else {
      delete errors[field.name]
    }
  })
  
  if (!hasErrors) {
    emit('submit', { ...formData })
  }
}

function handleFieldBlur(fieldName) {
  const field = props.fields.find(f => f.name === fieldName)
  if (field) {
    const fieldErrors = validateField(field, formData[fieldName])
    if (fieldErrors.length > 0) {
      errors[fieldName] = fieldErrors[0]
    } else {
      delete errors[fieldName]
    }
  }
}

function handleFieldFocus(fieldName) {
  // Clear error on focus
  delete errors[fieldName]
}

// Watch for changes in formData and emit
watch(formData, (newData) => {
  emit('field-change', { ...newData })
}, { deep: true })

// Watch for changes in initialData
watch(() => props.initialData, () => {
  initializeFormData()
}, { deep: true, immediate: true })

// Initialize on mount
initializeFormData()

// Expose data for parent access
defineExpose({
  formData,
  errors,
  isValid,
  validateField
})
</script>