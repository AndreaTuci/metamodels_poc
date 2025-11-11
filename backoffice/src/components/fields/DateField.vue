<template>
  <div class="form-group">
    <label :for="fieldId" class="form-label">
      {{ field.verbose_name || field.name }}
      <span v-if="field.required" class="required">*</span>
    </label>
    
    <input
      :id="fieldId"
      :type="inputType"
      v-model="modelValue"
      @input="updateValue"
      class="form-input"
      :class="{ 'error': error }"
      :required="field.required"
    />
    
    <p v-if="field.help_text" class="help-text">{{ field.help_text }}</p>
    <p v-if="error" class="error-text">{{ error }}</p>
  </div>
</template>

<script>
import { defineComponent, computed } from 'vue'
import BaseField from './BaseField.vue'

export default defineComponent({
  name: 'DateField',
  extends: BaseField,
  props: {
    field: {
      type: Object,
      required: true
    },
    modelValue: {
      default: ''
    },
    error: {
      type: String,
      default: ''
    }
  },
  setup(props, { emit }) {
    const fieldId = computed(() => `date-${props.field.name}`)
    
    const inputType = computed(() => {
      return props.field.field_type === 'DateTimeField' ? 'datetime-local' : 'date'
    })

    const updateValue = (event) => {
      emit('update:modelValue', event.target.value)
    }

    return {
      fieldId,
      inputType,
      updateValue
    }
  }
})
</script>

<style scoped>
.form-input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  transition: border-color 0.2s, box-shadow 0.2s;
  cursor: pointer;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-input.error {
  border-color: #ef4444;
}

.form-input.error:focus {
  border-color: #ef4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
}

/* Miglioramenti per il date picker */
.form-input[type="date"]::-webkit-calendar-picker-indicator,
.form-input[type="datetime-local"]::-webkit-calendar-picker-indicator {
  cursor: pointer;
  color: #3b82f6;
  font-size: 1.1rem;
  margin-left: 0.5rem;
}

.form-input[type="date"]::-webkit-inner-spin-button,
.form-input[type="datetime-local"]::-webkit-inner-spin-button {
  -webkit-appearance: none;
}

.help-text {
  margin-top: 0.25rem;
  font-size: 0.75rem;
  color: #6b7280;
}

.error-text {
  margin-top: 0.25rem;
  font-size: 0.75rem;
  color: #ef4444;
}

.required {
  color: #ef4444;
}

.form-label {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.form-group {
  margin-bottom: 1rem;
}
</style>