<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    required: true,
  },
  item: {
    type: Object,
    default: null,
  },
  imageSrc: {
    type: String,
    default: '',
  },
  hasPrevious: {
    type: Boolean,
    default: false,
  },
  hasNext: {
    type: Boolean,
    default: false,
  },
  currentIndex: {
    type: Number,
    default: 0,
  },
  totalCount: {
    type: Number,
    default: 0,
  },
  isBusy: {
    type: Boolean,
    default: false,
  },
  isLoadingImage: {
    type: Boolean,
    default: false,
  },
  isKeyboardBlocked: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits([
  'close',
  'previous',
  'next',
  'move-to-trash',
  'rename',
  'edit-current',
  'open-folder',
])

const isActualSize = ref(false)

watch(
  () => props.item,
  () => {
    isActualSize.value = false
  }
)

function isEditableTarget(target) {
  if (!(target instanceof Element)) {
    return false
  }
  const tagName = target.tagName.toLowerCase()
  return ['input', 'textarea', 'select'].includes(tagName) || target.isContentEditable
}

function handleKeydown(event) {
  if (!props.show || props.isKeyboardBlocked || event.isComposing || isEditableTarget(event.target)) {
    return
  }

  if (event.key === 'Escape') {
    event.preventDefault()
    emit('close')
    return
  }

  if (event.key === 'ArrowLeft' && props.hasPrevious && !props.isBusy) {
    event.preventDefault()
    emit('previous')
    return
  }

  if (event.key === 'ArrowRight' && props.hasNext && !props.isBusy) {
    event.preventDefault()
    emit('next')
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div v-if="show && item" class="modal-backdrop-shell" role="presentation">
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
            >
              <span>{{ item.filename }}</span>
              <span class="detail-modal-position text-secondary">
                {{ currentIndex + 1 }} / {{ totalCount }}
              </span>
            </h1>
            <button
              type="button"
              class="btn-close"
              aria-label="閉じる"
              :disabled="isBusy"
              @click="$emit('close')"
            ></button>
          </div>

          <div class="modal-body image-detail-body">
            <div class="image-detail-preview" :class="{ 'is-actual-size': isActualSize }">
              <div v-if="isLoadingImage" class="text-secondary">読み込み中</div>
              <img
                v-else-if="imageSrc"
                class="image-detail-image"
                :class="{ 'is-actual-size': isActualSize }"
                :src="imageSrc"
                :alt="item.filename"
                @click="isActualSize = !isActualSize"
              />
              <div v-else class="text-secondary">画像を表示できません</div>
            </div>
          </div>

          <div class="modal-footer image-detail-modal-footer">
            <div class="image-detail-modal-nav-actions">
              <button
                type="button"
                class="btn btn-outline-secondary"
                :disabled="isBusy || !hasPrevious"
                @click="$emit('previous')"
              >
                前へ
              </button>
              <button
                type="button"
                class="btn btn-outline-secondary"
                :disabled="isBusy || !hasNext"
                @click="$emit('next')"
              >
                次へ
              </button>
            </div>
            <div class="image-detail-modal-main-actions">
              <button
                type="button"
                class="btn btn-outline-primary"
                :disabled="isBusy || !item"
                @click="$emit('edit-current', item)"
              >
                属性編集
              </button>
              <button
                type="button"
                class="btn btn-outline-secondary"
                :disabled="isBusy || !item"
                @click="$emit('open-folder', item.path)"
              >
                エクスプローラで開く
              </button>
              <button
                type="button"
                class="btn btn-outline-secondary"
                :disabled="isBusy || !item"
                @click="$emit('rename', item)"
              >
                リネーム
              </button>
              <button
                type="button"
                class="btn btn-outline-warning"
                :disabled="isBusy || !item"
                @click="$emit('move-to-trash', item)"
              >
                ごみ箱へ移動
              </button>
              <button
                type="button"
                class="btn btn-secondary"
                :disabled="isBusy"
                @click="$emit('close')"
              >
                閉じる
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop show"></div>
  </div>
</template>
