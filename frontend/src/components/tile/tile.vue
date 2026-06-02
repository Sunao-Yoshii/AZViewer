<script setup>
import { onBeforeUnmount, ref, watch } from 'vue'
import placeholderUrl from '../../assets/images/placeholder.svg'
import { useImageMetadata } from '../../composables/useImageMetadata'
import { fetchLocalImageThumb } from '../../services/backendApi'
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
  editingImageId: {
    type: Number,
    default: null,
  },
})

const emit = defineEmits(['edit-finished', 'open-detail', 'save-detail', 'selection-change'])

const isEditing = ref(false)
const editRef = ref(null)
const thumbnailUrl = ref(props.item.thumbnailUrl || placeholderUrl)
let thumbnailLoadToken = 0
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

watch(
  () => props.editingImageId,
  (value) => {
    if (value === props.item.id) {
      isEditing.value = true
    }
  }
)

watch(
  () => props.item.id,
  () => {
    loadThumbnail(props.item)
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  thumbnailLoadToken += 1
})

async function loadThumbnail(item) {
  const token = ++thumbnailLoadToken
  thumbnailUrl.value = item?.thumbnailUrl || placeholderUrl

  if (!item?.id || item.thumbnailUrl) {
    return
  }

  const result = await fetchLocalImageThumb(item.id)
  if (token !== thumbnailLoadToken) {
    return
  }

  thumbnailUrl.value = result.success
    ? result.data?.dataUrl || placeholderUrl
    : placeholderUrl
}

function handleSave(payload) {
  emit('save-detail', payload)
  emit('edit-finished', props.item.id)
}

function handleCancelEdit() {
  isEditing.value = false
  emit('edit-finished', props.item.id)
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
    <article :id="`image-tile-${item.id}`" class="card image-tile">
      <img
        class="image-tile-thumb"
        :src="thumbnailUrl"
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
            aria-label="画像を選択"
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
          @cancel="handleCancelEdit"
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
