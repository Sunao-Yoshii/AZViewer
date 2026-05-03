<script setup>
import { nextTick, ref, watch } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    required: true,
  },
  item: {
    type: Object,
    default: null,
  },
  metadataText: {
    type: String,
    default: '',
  },
  mode: {
    type: String,
    default: 'display',
    validator: (value) => ['display', 'edit'].includes(value),
  },
  isLoading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close', 'copy', 'apply-tags'])

const metadataTextarea = ref(null)
const TEXTAREA_MIN_REM = 6
const TEXTAREA_MAX_REM = 20

watch(
  () => [props.show, props.metadataText, props.isLoading],
  async () => {
    await nextTick()
    resizeMetadataTextarea()
  },
  { immediate: true }
)

function resizeMetadataTextarea() {
  const element = metadataTextarea.value
  if (!element) {
    return
  }

  const minHeight = remToPixels(TEXTAREA_MIN_REM)
  const maxHeight = remToPixels(TEXTAREA_MAX_REM)
  element.style.height = `${minHeight}px`
  element.style.height = `${Math.min(Math.max(element.scrollHeight, minHeight), maxHeight)}px`
}

function remToPixels(value) {
  const rootFontSize = Number.parseFloat(window.getComputedStyle(document.documentElement).fontSize)
  return value * (rootFontSize || 16)
}

function getSelectedText() {
  const element = metadataTextarea.value
  if (!element) {
    return ''
  }

  const start = element.selectionStart ?? 0
  const end = element.selectionEnd ?? 0
  if (start === end) {
    return ''
  }

  return element.value.slice(start, end)
}

function handleCopy() {
  emit('copy', {
    text: getSelectedText(),
  })
}

function handleApplyTags() {
  emit('apply-tags', {
    text: getSelectedText().replaceAll('BREAK', ''),
  })
}
</script>

<template>
  <div v-if="show" class="modal-backdrop-shell" role="presentation">
    <div
      class="modal d-block"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
      aria-labelledby="imageMetadataTitle"
    >
      <div class="modal-dialog modal-xl modal-dialog-centered metadata-modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h1 id="imageMetadataTitle" class="modal-title fs-5 metadata-modal-title">
              {{ item ? `メタ情報: ${item.filename}` : 'メタ情報' }}
            </h1>
            <button type="button" class="btn-close" aria-label="閉じる" @click="$emit('close')"></button>
          </div>

          <div class="modal-body">
            <textarea
              ref="metadataTextarea"
              class="form-control metadata-textarea"
              :value="isLoading ? 'メタ情報を読み込んでいます...' : metadataText"
              :disabled="isLoading"
              readonly
            ></textarea>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn btn-outline-secondary" @click="handleCopy">
              コピー
            </button>
            <button
              v-if="mode === 'edit'"
              type="button"
              class="btn btn-primary"
              @click="handleApplyTags"
            >
              タグ付け
            </button>
            <button type="button" class="btn btn-secondary" @click="$emit('close')">
              閉じる
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop show"></div>
  </div>
</template>
