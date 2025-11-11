<template>
  <component
    :is="fieldComponent"
    v-model="internalValue"
    :label="field.verbose_name || field.name"
    :help-text="field.help_text"
    :required="field.required"
    :error="fieldError"
    :input-id="`field_${field.name}`"
    :field-type="field.field_type"
    :placeholder="getPlaceholder(field)"
    :max-length="getMaxLength(field)"
    :min="getMin(field)"
    :max="getMax(field)"
    :step="getStep(field)"
    :rows="getRows(field)"
    @blur="$emit('blur', field.name)"
    @focus="$emit('focus', field.name)"
  />
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { getFieldComponent } from './index.js'

const props = defineProps({
  field: {
    type: Object,
    required: true
  },
  modelValue: {
    type: [String, Number, Boolean, Date],
    default: null
  },
  error: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue', 'blur', 'focus'])

// Reactive value per gestire il v-model
const internalValue = ref(props.modelValue)

// Watcher per sincronizzare con il prop
watch(() => props.modelValue, (newValue) => {
  internalValue.value = newValue
})

// Watcher per emettere aggiornamenti
watch(internalValue, (newValue) => {
  emit('update:modelValue', newValue)
})

// Computed per ottenere il componente corretto
const fieldComponent = computed(() => {
  return getFieldComponent(props.field.field_type)
})

// Computed per l'errore del campo
const fieldError = computed(() => {
  return props.error
})

// Helper functions per le props specifiche
function getPlaceholder(field) {
  if (field.help_text) return field.help_text
  
  switch (field.field_type) {
    case 'CharField':
      return `Inserisci ${field.verbose_name || field.name}`
    case 'TextField':
      return `Inserisci testo per ${field.verbose_name || field.name}`
    case 'IntegerField':
      return 'Inserisci un numero intero'
    case 'FloatField':
      return 'Inserisci un numero decimale'
    case 'EmailField':
      return 'esempio@email.com'
    case 'URLField':
      return 'https://esempio.com'
    default:
      return ''
  }
}

function getMaxLength(field) {
  // Estrai max_length dai field_params se presente
  if (field.field_params && field.field_params.max_length) {
    return field.field_params.max_length
  }
  
  // Default basati sul tipo
  switch (field.field_type) {
    case 'CharField':
      return 255
    default:
      return null
  }
}

function getMin(field) {
  if (field.field_params && field.field_params.min_value !== undefined) {
    return field.field_params.min_value
  }
  return null
}

function getMax(field) {
  if (field.field_params && field.field_params.max_value !== undefined) {
    return field.field_params.max_value
  }
  return null
}

function getStep(field) {
  if (field.field_type === 'FloatField') {
    return field.field_params?.step || '0.01'
  }
  return 1
}

function getRows(field) {
  if (field.field_type === 'TextField') {
    return field.field_params?.rows || 3
  }
  return 3
}
</script>