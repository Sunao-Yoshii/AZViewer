<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

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
])

const isActualSize = ref(false)
const displayPosition = computed(() => {
  if (props.totalCount <= 0 || props.currentIndex < 0) {
    return ''
  }
  return `${props.currentIndex + 1} / ${props.totalCount}`
})

watch(
  () => [props.item?.id, props.imageSrc],
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

function toggleActualSize() {
  if (props.isLoadingImage || !props.imageSrc) {
    return
  }
  isActualSize.value = !isActualSize.value
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div
    v-if="show && item"
    class="image-detail-viewer"
    role="dialog"
    aria-modal="true"
    aria-labelledby="imageDetailTitle"
  >
    <aside class="image-detail-viewer-sidebar">
      <section class="image-detail-viewer-section">
        <div class="small text-muted">ファイル情報</div>
        <h1
          id="imageDetailTitle"
          class="image-detail-viewer-filename"
        >
          {{ item.filename }}
        </h1>
        <div
          v-if="item.folder || item.path"
          class="image-detail-viewer-path small"
        >
          {{ item.folder || item.path }}
        </div>
        <div
          v-if="displayPosition"
          class="image-detail-viewer-position small"
        >
          {{ displayPosition }}
        </div>
      </section>

      <section class="image-detail-viewer-section">
        <div class="small text-muted">移動</div>
        <div class="d-grid gap-2">
          <button
            type="button"
            class="btn btn-sm btn-outline-light"
            :disabled="isBusy || !hasPrevious"
            @click="$emit('previous')"
          >
            前へ
          </button>
          <button
            type="button"
            class="btn btn-sm btn-outline-light"
            :disabled="isBusy || !hasNext"
            @click="$emit('next')"
          >
            次へ
          </button>
        </div>
      </section>

      <section class="image-detail-viewer-section">
        <div class="small text-muted">表示</div>
        <div class="d-grid gap-2">
          <button
            type="button"
            class="btn btn-sm btn-outline-light"
            :disabled="isLoadingImage || !imageSrc"
            @click="toggleActualSize"
          >
            {{ isActualSize ? '画面に合わせる' : '実寸表示' }}
          </button>
        </div>
      </section>

      <section class="image-detail-viewer-section">
        <div class="small text-muted">操作</div>
        <div class="d-grid gap-2">
          <button
            type="button"
            class="btn btn-sm btn-outline-light"
            :disabled="isBusy || !item"
            @click="$emit('edit-current', item)"
          >
            属性編集
          </button>
          <button
            type="button"
            class="btn btn-sm btn-outline-light"
            :disabled="isBusy || !item"
            @click="$emit('rename', item)"
          >
            リネーム
          </button>
        </div>
      </section>

      <section class="image-detail-viewer-section image-detail-viewer-danger-section">
        <div class="d-grid gap-2">
          <button
            type="button"
            class="btn btn-sm btn-outline-warning"
            :disabled="isBusy || !item"
            @click="$emit('move-to-trash', item)"
          >
            ごみ箱へ移動
          </button>
        </div>
      </section>

      <section class="image-detail-viewer-section">
        <div class="d-grid gap-2">
          <button
            type="button"
            class="btn btn-sm btn-outline-light"
            :disabled="isBusy"
            @click="$emit('close')"
          >
            閉じる
          </button>
        </div>
      </section>
    </aside>

    <main class="image-detail-viewer-main">
      <div
        class="image-detail-viewer-image-stage"
        :class="{ 'is-actual-size': isActualSize }"
      >
        <div v-if="isLoadingImage" class="image-detail-viewer-message">
          画像を読み込んでいます...
        </div>
        <img
          v-else-if="imageSrc"
          class="image-detail-viewer-image-fit"
          :class="{ 'image-detail-viewer-image-actual': isActualSize }"
          :src="imageSrc"
          :alt="item.filename"
          @click="toggleActualSize"
        />
        <div v-else class="image-detail-viewer-message">
          画像を表示できませんでした。
        </div>
      </div>
    </main>
  </div>
</template>
