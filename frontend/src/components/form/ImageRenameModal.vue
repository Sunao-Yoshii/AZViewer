<script setup>
import { computed } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    required: true,
  },
  item: {
    type: Object,
    default: null,
  },
  filename: {
    type: String,
    default: '',
  },
  isSaving: {
    type: Boolean,
    default: false,
  },
  errorMessage: {
    type: String,
    default: '',
  },
})

const emit = defineEmits([
  'close',
  'save',
  'update:filename',
])

const currentExtension = computed(() => {
  const filename = props.item?.filename || ''
  const dotIndex = filename.lastIndexOf('.')
  return dotIndex >= 0 ? filename.slice(dotIndex) : ''
})

const validationMessage = computed(() => {
  const filename = props.filename.trim()
  if (!filename) {
    return 'ファイル名を入力してください。'
  }
  if (/[\\/]/.test(filename)) {
    return 'ファイル名にパス区切り文字は使用できません。'
  }
  if (/[<>:"|?*]/.test(filename)) {
    return 'ファイル名に使用できない文字が含まれています。'
  }
  if (!filename.toLowerCase().endsWith(currentExtension.value.toLowerCase())) {
    return '拡張子は変更できません。'
  }
  if (filename === props.item?.filename) {
    return '現在と同じファイル名です。'
  }
  return ''
})

const canSave = computed(() => !props.isSaving && !validationMessage.value)
</script>

<template>
  <div v-if="show" class="modal-backdrop-shell" role="presentation">
    <div
      class="modal d-block"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
      aria-labelledby="imageRenameTitle"
    >
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h1 id="imageRenameTitle" class="modal-title fs-5">ファイル名を変更</h1>
            <button
              type="button"
              class="btn-close"
              aria-label="閉じる"
              :disabled="isSaving"
              @click="$emit('close')"
            ></button>
          </div>
          <div class="modal-body vstack gap-3">
            <div>
              <div class="small text-secondary mb-1">現在のファイル名</div>
              <div class="rename-current-filename">{{ item?.filename }}</div>
            </div>
            <div>
              <label class="form-label" for="imageRenameFilename">新しいファイル名</label>
              <input
                id="imageRenameFilename"
                class="form-control"
                type="text"
                :value="filename"
                :disabled="isSaving"
                autofocus
                @input="$emit('update:filename', $event.target.value)"
                @keydown.enter.prevent="canSave && $emit('save')"
              />
              <div class="form-text">拡張子は変更できません。</div>
            </div>
            <div v-if="validationMessage || errorMessage" class="alert alert-warning py-2 mb-0">
              {{ errorMessage || validationMessage }}
            </div>
          </div>
          <div class="modal-footer">
            <button
              type="button"
              class="btn btn-outline-secondary"
              :disabled="isSaving"
              @click="$emit('close')"
            >
              キャンセル
            </button>
            <button
              type="button"
              class="btn btn-primary"
              :disabled="!canSave"
              @click="$emit('save')"
            >
              変更
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop show"></div>
  </div>
</template>
