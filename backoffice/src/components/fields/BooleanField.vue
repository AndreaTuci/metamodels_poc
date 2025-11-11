<template>
  <BaseField
    :label="label"
    :help-text="helpText"
    :required="required"
    :error="error"
    :input-id="inputId"
    :show-label="false"
  >
    <label class="form-checkbox">
      <input
        :id="inputId"
        type="checkbox"
        :checked="modelValue"
        @change="$emit('update:modelValue', $event.target.checked)"
        @blur="$emit('blur')"
        @focus="$emit('focus')"
      />
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>
  </BaseField>
</template>

<script setup>
import BaseField from './BaseField.vue'

defineProps({
  modelValue: {
    type: Boolean,
    default: false
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
  }
})

defineEmits(['update:modelValue', 'blur', 'focus'])
</script>