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
      :required="field.required && !currentImage"
      accept="image/*"
    />
    
    <!-- Current image display -->
    <div v-if="currentImage" class="current-image">
      <div class="image-preview">
        <img 
          :src="getImageUrl(currentImage)" 
          :alt="getImageName(currentImage)"
          class="preview-img"
          @error="handleImageError"
        />
        <div class="image-overlay">
          <button 
            type="button" 
            @click="viewFullImage" 
            class="view-btn"
            title="Visualizza immagine"
          >
            👁️
          </button>
          <button 
            type="button" 
            @click="removeImage" 
            class="remove-btn"
            title="Rimuovi immagine"
          >
            🗑️
          </button>
        </div>
      </div>
      <div class="image-info">
        <span class="image-name">{{ getImageName(currentImage) }}</span>
        <span class="image-size" v-if="imageSize">{{ imageSize }}</span>
      </div>
    </div>
    
    <!-- New image preview -->
    <div v-if="newImage" class="new-image">
      <div class="image-preview">
        <img 
          :src="newImagePreview" 
          :alt="newImage.name"
          class="preview-img"
        />
        <div class="image-overlay">
          <button 
            type="button" 
            @click="viewNewImage" 
            class="view-btn"
            title="Visualizza immagine"
          >
            👁️
          </button>
          <button 
            type="button" 
            @click="clearNewImage" 
            class="remove-btn"
            title="Annulla caricamento"
          >
            ✕
          </button>
        </div>
      </div>
      <div class="image-info">
        <span class="image-name new">{{ newImage.name }}</span>
        <span class="image-size">{{ formatFileSize(newImage.size) }}</span>
      </div>
    </div>
    
    <p v-if="field.help_text" class="help-text">{{ field.help_text }}</p>
    <p v-if="error" class="error-text">{{ error }}</p>
    
    <!-- Modal per visualizzazione immagine -->
    <div v-if="showModal" class="image-modal" @click="closeModal">
      <div class="modal-content" @click.stop>
        <button @click="closeModal" class="modal-close">✕</button>
        <img :src="modalImageSrc" :alt="modalImageAlt" class="modal-image" />
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent, ref, computed, watch } from 'vue'

export default defineComponent({
  name: 'ImageField',
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
    }
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const fileInput = ref(null)
    const newImage = ref(null)
    const newImagePreview = ref(null)
    const currentImage = ref(props.modelValue)
    const imageSize = ref(null)
    const showModal = ref(false)
    const modalImageSrc = ref('')
    const modalImageAlt = ref('')

    const fieldId = computed(() => `image-${props.field.name}`)

    // Gestisce il cambio di immagine
    const handleFileChange = (event) => {
      const file = event.target.files[0]
      if (file && file.type.startsWith('image/')) {
        newImage.value = file
        
        // Crea anteprima dell'immagine
        const reader = new FileReader()
        reader.onload = (e) => {
          newImagePreview.value = e.target.result
        }
        reader.readAsDataURL(file)
        
        emit('update:modelValue', file)
      }
    }

    // Rimuove l'immagine corrente
    const removeImage = () => {
      currentImage.value = null
      imageSize.value = null
      emit('update:modelValue', null)
    }

    // Cancella la nuova immagine selezionata
    const clearNewImage = () => {
      newImage.value = null
      newImagePreview.value = null
      if (fileInput.value) {
        fileInput.value.value = ''
      }
      emit('update:modelValue', currentImage.value)
    }

    // Ottiene l'URL dell'immagine
    const getImageUrl = (image) => {
      if (typeof image === 'string') {
        // È un percorso dal backend
        if (image.startsWith('http')) {
          return image
        } else {
          return `http://localhost:8000/media/${image}`
        }
      }
      return image
    }

    // Ottiene il nome dell'immagine
    const getImageName = (image) => {
      if (typeof image === 'string') {
        return image.split('/').pop()
      }
      return image?.name || 'Immagine sconosciuta'
    }

    // Formatta la dimensione del file
    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    // Gestisce errori di caricamento immagine
    const handleImageError = (event) => {
      event.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTIxIDNWMjFIMTlWNUg1VjNIMjFaIiBmaWxsPSIjOUNBM0FGIi8+CjxwYXRoIGQ9Ik0xOSA1SDVWMTlIMTlWNVoiIGZpbGw9IiNGM0Y0RjYiLz4KPHBhdGggZD0iTTE0IDEwQzE0IDExLjEwNDYgMTMuMTA0NiAxMiAxMiAxMkMxMC44OTU0IDEyIDEwIDExLjEwNDYgMTAgMTBDMTAgOC44OTU0MyAxMC44OTU0IDggMTIgOEMxMy4xMDQ2IDggMTQgOC44OTU0MyAxNCAxMFoiIGZpbGw9IiM5Q0EzQUYiLz4KPHBhdGggZD0iTTE3IDE3SDdMMTAgMTNMMTIgMTVMMTUgMTJMMTcgMTdaIiBmaWxsPSIjOUNBM0FGIi8+Cjwvc3ZnPgo='
    }

    // Mostra l'immagine nel modal
    const viewFullImage = () => {
      modalImageSrc.value = getImageUrl(currentImage.value)
      modalImageAlt.value = getImageName(currentImage.value)
      showModal.value = true
    }

    // Mostra la nuova immagine nel modal
    const viewNewImage = () => {
      modalImageSrc.value = newImagePreview.value
      modalImageAlt.value = newImage.value.name
      showModal.value = true
    }

    // Chiude il modal
    const closeModal = () => {
      showModal.value = false
      modalImageSrc.value = ''
      modalImageAlt.value = ''
    }

    // Watch per aggiornare currentImage quando modelValue cambia
    watch(() => props.modelValue, (newValue) => {
      if (newValue && typeof newValue === 'string') {
        currentImage.value = newValue
      } else if (!newValue) {
        currentImage.value = null
        newImage.value = null
        newImagePreview.value = null
      }
    }, { immediate: true })

    return {
      fileInput,
      fieldId,
      newImage,
      newImagePreview,
      currentImage,
      imageSize,
      showModal,
      modalImageSrc,
      modalImageAlt,
      handleFileChange,
      removeImage,
      clearNewImage,
      getImageUrl,
      getImageName,
      formatFileSize,
      handleImageError,
      viewFullImage,
      viewNewImage,
      closeModal
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

.current-image, .new-image {
  margin-top: 0.75rem;
  padding: 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  background-color: #f9fafb;
}

.new-image {
  border-color: #3b82f6;
  background-color: #eff6ff;
}

.image-preview {
  position: relative;
  display: inline-block;
  margin-bottom: 0.5rem;
}

.preview-img {
  max-width: 200px;
  max-height: 150px;
  object-fit: cover;
  border-radius: 0.375rem;
  border: 1px solid #e5e7eb;
}

.image-overlay {
  position: absolute;
  top: 0;
  right: 0;
  display: flex;
  gap: 0.25rem;
  padding: 0.25rem;
  opacity: 0;
  transition: opacity 0.2s;
}

.image-preview:hover .image-overlay {
  opacity: 1;
}

.view-btn, .remove-btn {
  background: rgba(0, 0, 0, 0.7);
  color: white;
  border: none;
  border-radius: 0.25rem;
  width: 1.5rem;
  height: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 0.75rem;
  transition: background-color 0.2s;
}

.view-btn:hover {
  background: rgba(0, 0, 0, 0.8);
}

.remove-btn:hover {
  background: #ef4444;
}

.image-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.image-name {
  font-weight: 500;
  color: #374151;
  word-break: break-all;
}

.image-name.new {
  color: #3b82f6;
}

.image-size {
  font-size: 0.75rem;
  color: #6b7280;
}

.image-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
  background: white;
  border-radius: 0.5rem;
  padding: 1rem;
}

.modal-close {
  position: absolute;
  top: -0.5rem;
  right: -0.5rem;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 50%;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 1rem;
  font-weight: bold;
}

.modal-close:hover {
  background: #dc2626;
}

.modal-image {
  max-width: 100%;
  max-height: 80vh;
  object-fit: contain;
  border-radius: 0.375rem;
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