<template>
  <BaseField
    :label="label"
    :help-text="helpText"
    :required="required"
    :error="error"
    :input-id="inputId"
  >
    <textarea
      :id="inputId"
      class="form-textarea"
      :value="modelValue"
      :required="required"
      :placeholder="placeholder"
      :rows="rows"
      @input="$emit('update:modelValue', $event.target.value)"
      @blur="$emit('blur')"
      @focus="$emit('focus')"
    ></textarea>
  </BaseField>
</template>

<script setup>
import BaseField from './BaseField.vue'

defineProps({
  modelValue: {
    type: String,
    default: ''
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
  rows: {
    type: Number,
    default: 3
  }
})

defineEmits(['update:modelValue', 'blur', 'focus'])
</script>