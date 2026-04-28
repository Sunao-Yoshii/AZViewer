<script setup>
import { ref, watch } from 'vue'
import placeholderUrl from '../../assets/images/placeholder.svg'
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
})

const emit = defineEmits(['open-detail', 'request-delete', 'save-detail'])

const isEditing = ref(false)

watch(
  () => props.item,
  () => {
    isEditing.value = false
  }
)

function handleSave(payload) {
  emit('save-detail', payload)
}
</script>

<template>
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
      <div class="small fw-semibold text-truncate" :title="item.filename">{{ item.filename }}</div>
      <div class="image-tile-folder small text-secondary text-truncate" :title="item.folder">
        {{ item.folder }}
      </div>
      <TileEdit
        v-if="isEditing"
        :item="item"
        @cancel="isEditing = false"
        @save="handleSave"
      />
      <TileDisplay
        v-else
        :item="item"
        @edit="isEditing = true"
      />
    </div>
  </article>
</template>
