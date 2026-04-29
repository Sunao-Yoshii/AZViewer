<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  item: {
    type: Object,
    default: null,
  },
  imageUrl: {
    type: String,
    default: '',
  },
  isLoadingImage: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['close', 'open-folder'])

const isActualSize = ref(false)

watch(
  () => props.item,
  () => {
    isActualSize.value = false
  }
)
</script>

<template>
  <div v-if="item" class="modal-backdrop-shell" role="presentation">
    <div
      class="modal d-block"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
      aria-labelledby="imageDetailTitle"
    >
      <div class="modal-dialog modal-xl modal-dialog-centered image-detail-dialog">
        <div class="modal-content image-detail-content">
          <div class="modal-header">
            <h1
              id="imageDetailTitle"
              class="modal-title fs-5 detail-modal-title"
              role="button"
              tabindex="0"
              title="フォルダを開く"
              @click="$emit('open-folder', item.path)"
              @keydown.enter.prevent="$emit('open-folder', item.path)"
              @keydown.space.prevent="$emit('open-folder', item.path)"
            >
              {{ item.path }}
            </h1>
            <button type="button" class="btn-close" aria-label="閉じる" @click="$emit('close')"></button>
          </div>

          <div class="modal-body image-detail-body">
            <div class="image-detail-preview">
              <div v-if="isLoadingImage" class="text-secondary">読み込み中</div>
              <img
                v-else-if="imageUrl"
                class="image-detail-image"
                :class="{ 'is-actual-size': isActualSize }"
                :src="imageUrl"
                :alt="item.filename"
                @click="isActualSize = !isActualSize"
              />
              <div v-else class="text-secondary">画像を表示できません</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop show"></div>
  </div>
</template>
