<script setup>
defineProps({
  show: {
    type: Boolean,
    required: true,
  },
  summary: {
    type: String,
    default: '',
  },
  detail: {
    type: String,
    default: '',
  },
  failedFiles: {
    type: Array,
    default: () => [],
  },
})

defineEmits(['close'])
</script>

<template>
  <div v-if="show" class="modal-backdrop-shell" role="presentation">
    <div
      class="modal d-block"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
      aria-labelledby="imageImportErrorTitle"
    >
      <div class="modal-dialog modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h1 id="imageImportErrorTitle" class="modal-title fs-5">登録エラー</h1>
            <button
              type="button"
              class="btn-close"
              aria-label="閉じる"
              @click="$emit('close')"
            ></button>
          </div>

          <div class="modal-body">
            <p class="fw-semibold mb-2">{{ summary || 'データ登録中にエラーが発生しました。' }}</p>
            <p v-if="detail" class="small text-muted mb-3">{{ detail }}</p>

            <div v-if="failedFiles.length > 0">
              <p class="small fw-semibold mb-2">登録失敗ファイル</p>
              <ul class="list-group failed-file-list">
                <li
                  v-for="file in failedFiles"
                  :key="file"
                  class="list-group-item small text-break"
                >
                  {{ file }}
                </li>
              </ul>
            </div>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn btn-primary" @click="$emit('close')">
              閉じる
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop show"></div>
  </div>
</template>
