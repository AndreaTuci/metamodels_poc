<template>
  <BaseField
    :label="label"
    :help-text="helpText"
    :required="required"
    :error="error"
    :input-id="inputId"
  >
    <input
      :id="inputId"
      type="number"
      class="form-input"
      :value="modelValue"
      :required="required"
      :placeholder="placeholder"
      :min="min"
      :max="max"
      :step="step"
      @input="handleInput"
      @blur="$emit('blur')"
      @focus="$emit('focus')"
    />
  </BaseField>
</template>

<script setup>
import BaseField from './BaseField.vue'

const props = defineProps({
  modelValue: {
    type: [Number, String],
    default: null
  },
  label: {
    type: String,
    required: true
  },
  helpText: {
    type: String,
    default: ''
  },
  required: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  },
  inputId: {
    type: String,
    required: true
  },
  placeholder: {
    type: String,
    default: ''
  },
  min: {
    type: Number,
    default: null
  },
  max: {
    type: Number,
    default: null
  },
  step: {
    type: [Number, String],
    default: 1
  },
  fieldType: {
    type: String,
    default: 'IntegerField' // IntegerField o FloatField
  }
})

const emit = defineEmits(['update:modelValue', 'blur', 'focus'])

function handleInput(event) {
  const value = event.target.value
  
  if (value === '') {
    emit('update:modelValue', null)
    return
  }
  
  if (props.fieldType === 'FloatField') {
    const floatValue = parseFloat(value)
    emit('update:modelValue', isNaN(floatValue) ? null : floatValue)
  } else {
    const intValue = parseInt(value, 10)
    emit('update:modelValue', isNaN(intValue) ? null : intValue)
  }
}
</script>