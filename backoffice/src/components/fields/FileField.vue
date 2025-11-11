<template>
  <div class="form-group">
    <label :for="fieldId" class="form-label">
      {{ field.verbose_name || field.name }}
      <span v-if="field.required" class="required">*</span>
    </label>
    
    <!-- File input -->
    <input
      :id="fieldId"
      ref="fileInput"
      type="file"
      @change="handleFileChange"
      class="form-input file-input"
      :class="{ 'error': error }"
      :required="field.required && !currentFile"
      :accept="acceptedTypes"
    />
    
    <!-- Current file display -->
    <div v-if="currentFile" class="current-file">
      <div class="file-info">
        <span class="file-icon">📄</span>
        <div class="file-details">
          <a :href="getFileUrl(currentFile)" target="_blank" class="file-link">
            {{ getFileName(currentFile) }}
          </a>
          <span class="file-size" v-if="fileSize">{{ fileSize }}</span>
        </div>
        <button 
          type="button" 
          @click="removeFile" 
          class="remove-file-btn"
          title="Rimuovi file"
        >
          ✕
        </button>
      </div>
    </div>
    
    <!-- New file preview -->
    <div v-if="newFile" class="new-file">
      <div class="file-info new">
        <span class="file-icon">📄</span>
        <div class="file-details">
          <span class="file-name">{{ newFile.name }}</span>
          <span class="file-size">{{ formatFileSize(newFile.size) }}</span>
        </div>
        <button 
          type="button" 
          @click="clearNewFile" 
          class="remove-file-btn"
          title="Annulla caricamento"
        >
          ✕
        </button>
      </div>
    </div>
    
    <p v-if="field.help_text" class="help-text">{{ field.help_text }}</p>
    <p v-if="error" class="error-text">{{ error }}</p>
  </div>
</template>

<script>
import { defineComponent, ref, computed, watch } from 'vue'

export default defineComponent({
  name: 'FileField',
  props: {
    field: {
      type: Object,
      required: true
    },
    modelValue: {
      default: null
    },
    error: {
      type: String,
      default: ''
    },
    accept: {
      type: String,
      default: '*/*'
    }
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const fileInput = ref(null)
    const newFile = ref(null)
    const currentFile = ref(props.modelValue)
    const fileSize = ref(null)

    const fieldId = computed(() => `file-${props.field.name}`)
    
    const acceptedTypes = computed(() => {
      return props.accept || '*/*'
    })

    // Gestisce il cambio di file
    const handleFileChange = (event) => {
      const file = event.target.files[0]
      if (file) {
        newFile.value = file
        emit('update:modelValue', file)
      }
    }

    // Rimuove il file corrente
    const removeFile = () => {
      currentFile.value = null
      fileSize.value = null
      emit('update:modelValue', null)
    }

    // Cancella il nuovo file selezionato
    const clearNewFile = () => {
      newFile.value = null
      if (fileInput.value) {
        fileInput.value.value = ''
      }
      emit('update:modelValue', currentFile.value)
    }

    // Ottiene l'URL del file
    const getFileUrl = (file) => {
      if (typeof file === 'string') {
        // È un percorso dal backend
        if (file.startsWith('http')) {
          return file
        } else {
          return `http://localhost:8000/media/${file}`
        }
      }
      return file
    }

    // Ottiene il nome del file
    const getFileName = (file) => {
      if (typeof file === 'string') {
        return file.split('/').pop()
      }
      return file?.name || 'File sconosciuto'
    }

    // Formatta la dimensione del file
    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    // Watch per aggiornare currentFile quando modelValue cambia
    watch(() => props.modelValue, (newValue) => {
      if (newValue && typeof newValue === 'string') {
        currentFile.value = newValue
      } else if (!newValue) {
        currentFile.value = null
        newFile.value = null
      }
    }, { immediate: true })

    return {
      fileInput,
      fieldId,
      newFile,
      currentFile,
      fileSize,
      acceptedTypes,
      handleFileChange,
      removeFile,
      clearNewFile,
      getFileUrl,
      getFileName,
      formatFileSize
    }
  }
})
</script>

<style scoped>
.file-input {
  width: 100%;
  padding: 0.5rem;
  border: 2px dashed #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  transition: border-color 0.2s, background-color 0.2s;
  background-color: #f9fafb;
}

.file-input:hover {
  border-color: #9ca3af;
  background-color: #f3f4f6;
}

.file-input:focus {
  outline: none;
  border-color: #3b82f6;
  background-color: white;
}

.file-input.error {
  border-color: #ef4444;
}

.current-file, .new-file {
  margin-top: 0.75rem;
  padding: 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  background-color: #f9fafb;
}

.new-file {
  border-color: #3b82f6;
  background-color: #eff6ff;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.file-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.file-details {
  flex: 1;
  min-width: 0;
}

.file-link {
  display: block;
  color: #3b82f6;
  text-decoration: none;
  font-weight: 500;
  word-break: break-all;
}

.file-link:hover {
  text-decoration: underline;
}

.file-name {
  display: block;
  font-weight: 500;
  color: #374151;
  word-break: break-all;
}

.file-size {
  display: block;
  font-size: 0.75rem;
  color: #6b7280;
  margin-top: 0.25rem;
}

.remove-file-btn {
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 50%;
  width: 1.5rem;
  height: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 0.75rem;
  flex-shrink: 0;
  transition: background-color 0.2s;
}

.remove-file-btn:hover {
  background: #dc2626;
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