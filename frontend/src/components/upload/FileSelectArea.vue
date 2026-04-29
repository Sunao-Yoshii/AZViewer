<script setup>
import { useImageImport } from '../../composables/useImageImport'
import ErrorModal from './ErrorModal.vue'

const emit = defineEmits(['import-complete'])
const {
  isBusy,
  statusMessage,
  errorModal,
  closeErrorModal,
  handleSelectFiles,
  handleSelectFolder,
} = useImageImport({ emit })

function handleDragEvent(event) {
  const files = Array.from(event.dataTransfer?.files ?? []).map((file) => ({
    name: file.name,
    type: file.type,
    size: file.size,
  }))

  console.log('FileSelectArea drag/drop event', {
    type: event.type,
    fileCount: files.length,
    files,
  })
}
</script>

<template>
  <section class="file-select-area h-100">
    <div
      class="file-select-target"
      :class="{ 'is-busy': isBusy }"
      @dragenter="handleDragEvent"
      @dragover="handleDragEvent"
      @dragleave="handleDragEvent"
      @drop="handleDragEvent"
    >
      <div class="file-select-main">
        <i class="bi bi-images file-select-icon" aria-hidden="true"></i>
        <p class="file-select-title mb-1">画像ファイルまたはフォルダをドラッグ＆ドロップ</p>
        <p class="file-select-description mb-0">png / jpg / jpeg / webp / avif</p>
        <p class="file-select-description mb-0">フォルダは直下ファイルのみ対象</p>
      </div>

      <div class="file-select-actions" aria-label="ファイル登録操作">
        <button
          type="button"
          class="btn btn-sm btn-outline-primary file-select-action"
          title="ファイルを選択"
          :disabled="isBusy"
          @click="handleSelectFiles"
        >
          <i class="bi bi-file-earmark-image" aria-hidden="true"></i>
        </button>
        <button
          type="button"
          class="btn btn-sm btn-outline-primary file-select-action"
          title="フォルダを選択"
          :disabled="isBusy"
          @click="handleSelectFolder"
        >
          <i class="bi bi-folder2-open" aria-hidden="true"></i>
        </button>
      </div>

      <p class="file-select-status mb-0" aria-live="polite">
        {{ statusMessage }}
      </p>
    </div>
  </section>

  <ErrorModal
    :show="errorModal.show"
    :summary="errorModal.summary"
    :detail="errorModal.detail"
    :failed-files="errorModal.failedFiles"
    @close="closeErrorModal"
  />
</template>
