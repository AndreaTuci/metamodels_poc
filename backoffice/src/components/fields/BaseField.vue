<template>
  <div class="form-group">
    <label v-if="showLabel" class="form-label" :for="inputId">
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>
    <slot />
    <p v-if="helpText" class="text-xs text-muted mt-1">{{ helpText }}</p>
    <p v-if="error" class="text-xs text-red-500 mt-1">{{ error }}</p>
  </div>
</template>

<script setup>
defineProps({
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
  showLabel: {
    type: Boolean,
    default: true
  }
})
</script>