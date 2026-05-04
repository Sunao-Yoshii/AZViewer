<script setup>
import { ref, watch } from 'vue'
import placeholderUrl from '../../assets/images/placeholder.svg'
import { useImageMetadata } from '../../composables/useImageMetadata'
import ImageMetadataModal from './ImageMetadataModal.vue'
import TileDisplay from './display.vue'
import TileEdit from './edit.vue'

const props = defineProps({
  item: {
    type: Object,
    required: true,
  },
  isSearching: {
    type: Boolean,
    default: false,
  },
  selected: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['open-detail', 'request-delete', 'save-detail', 'selection-change'])

const isEditing = ref(false)
const editRef = ref(null)
const {
  metadataModal,
  openMetadataModal,
  closeMetadataModal,
  handleCopyMetadataText,
  handleApplyMetadataTags,
} = useImageMetadata()

watch(
  () => props.item,
  () => {
    isEditing.value = false
  }
)

function handleSave(payload) {
  emit('save-detail', payload)
}

function handleOpenMetadataFromDisplay() {
  openMetadataModal(props.item, 'display')
}

function handleOpenMetadataFromEdit() {
  openMetadataModal(props.item, 'edit')
}

function applyMetadataTextToTagInput(value) {
  editRef.value?.applyTextToTagInput(value)
}
</script>

<template>
  <div>
    <article class="card image-tile">
      <button
        type="button"
        class="btn-close image-tile-delete"
        aria-label="削除"
        :disabled="isSearching"
        @click.stop="$emit('request-delete', item.id)"
      ></button>
      <img
        class="image-tile-thumb"
        :src="item.thumbnailUrl || placeholderUrl"
        :alt="item.filename"
        role="button"
        @click="$emit('open-detail', item)"
      />
      <div class="card-body image-tile-body">
        <div class="image-tile-title-row small fw-semibold">
          <input
            type="checkbox"
            class="form-check-input image-tile-select-checkbox"
            :checked="selected"
            :disabled="isSearching"
            aria-label="削除対象として選択"
            @change="$emit('selection-change', { id: item.id, selected: $event.target.checked })"
          />
          <span class="image-tile-title text-truncate" :title="item.filename">
            {{ item.filename }}
          </span>
        </div>
        <div class="image-tile-folder small text-secondary text-truncate" :title="item.folder">
          {{ item.folder }}
        </div>
        <TileEdit
          v-if="isEditing"
          ref="editRef"
          :item="item"
          @cancel="isEditing = false"
          @save="handleSave"
          @open-metadata="handleOpenMetadataFromEdit"
        />
        <TileDisplay
          v-else
          :item="item"
          @edit="isEditing = true"
          @open-metadata="handleOpenMetadataFromDisplay"
        />
      </div>
    </article>
    <ImageMetadataModal
      :show="metadataModal.show"
      :item="metadataModal.item"
      :metadata-text="metadataModal.metadataText"
      :mode="metadataModal.mode"
      :is-loading="metadataModal.isLoading"
      @close="closeMetadataModal"
      @copy="handleCopyMetadataText"
      @apply-tags="(payload) => handleApplyMetadataTags(payload, applyMetadataTextToTagInput)"
    />
  </div>
</template>
