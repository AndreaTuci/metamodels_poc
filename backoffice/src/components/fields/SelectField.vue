<template>
  <div class="form-group">
    <label :for="fieldId" class="form-label">
      {{ field.verbose_name || field.name }}
      <span v-if="field.required" class="required">*</span>
    </label>
    
    <select
      :id="fieldId"
      v-model="modelValue"
      @change="updateValue"
      class="form-select"
      :class="{ 'error': error }"
      :required="field.required"
    >
      <option value="" disabled>
        Seleziona {{ field.verbose_name || field.name }}...
      </option>
      <option v-for="option in options" :key="option.value" :value="option.value">
        {{ option.label }}
      </option>
    </select>
    
    <p v-if="field.help_text" class="help-text">{{ field.help_text }}</p>
    <p v-if="error" class="error-text">{{ error }}</p>
  </div>
</template>

<script>
import { defineComponent, ref, computed, onMounted } from 'vue'
import BaseField from './BaseField.vue'

export default defineComponent({
  name: 'SelectField',
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
    const options = ref([])
    const loading = ref(false)

    const fieldId = computed(() => `select-${props.field.name}`)

    const updateValue = (event) => {
      emit('update:modelValue', event.target.value)
    }

    // Carica le opzioni per ForeignKey
    const loadOptions = async () => {
      if (props.field.field_type !== 'ForeignKey') return

      try {
        loading.value = true
        const token = localStorage.getItem('authToken')
        
        // Determina il modello di riferimento dalla configurazione del campo
        let relatedModel = props.field.related_model || props.field.to
        
        // Se non specificato, prova a dedurlo dal nome del campo
        if (!relatedModel) {
          // Esempio: 'page' -> 'Page', 'category' -> 'Category'
          relatedModel = props.field.name.charAt(0).toUpperCase() + props.field.name.slice(1)
        }

        const response = await fetch(`http://localhost:8000/api/data/${relatedModel}/`, {
          headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json'
          }
        })

        if (response.ok) {
          const data = await response.json()
          const records = data.results || data
          
          options.value = records.map(record => ({
            value: record.id,
            label: record.title || record.name || record.toString || `${relatedModel} #${record.id}`
          }))
        } else {
          console.warn(`Impossibile caricare le opzioni per ${props.field.name}`)
        }
      } catch (error) {
        console.error('Errore nel caricamento delle opzioni:', error)
      } finally {
        loading.value = false
      }
    }

    onMounted(loadOptions)

    return {
      fieldId,
      options,
      loading,
      updateValue
    }
  }
})
</script>

<style scoped>
.form-select {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-select.error {
  border-color: #ef4444;
}

.form-select.error:focus {
  border-color: #ef4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
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
</style>