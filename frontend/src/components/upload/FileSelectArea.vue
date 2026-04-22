<script setup>
import { ref } from 'vue'
import {
  importSelectedItems,
  selectFilesDialog,
  selectFolderDialog,
} from '../../services/backendApi'
import ErrorModal from './ErrorModal.vue'

const isBusy = ref(false)
const statusMessage = ref('')
const errorModal = ref({
  show: false,
  summary: '',
  detail: '',
  failedFiles: [],
})

function closeErrorModal() {
  errorModal.value = {
    show: false,
    summary: '',
    detail: '',
    failedFiles: [],
  }
}

async function importItems(items) {
  if (items.length === 0) {
    statusMessage.value = '登録対象がありません'
    return
  }

  isBusy.value = true
  statusMessage.value = '登録中'

  const result = await importSelectedItems(items)

  if (result.success) {
    const importedCount = result.data?.importedCount ?? 0
    const skippedCount = result.data?.skippedCount ?? 0
    statusMessage.value = `登録 ${importedCount} 件 / 除外 ${skippedCount} 件`
  } else {
    errorModal.value = {
      show: true,
      summary: result.data?.errorSummary ?? 'データ登録中にエラーが発生しました。',
      detail: result.message ?? '',
      failedFiles: result.data?.failedFiles ?? items.map((item) => item.path),
    }
    statusMessage.value = '登録失敗'
  }

  isBusy.value = false
}

async function handleSelectFiles() {
  isBusy.value = true
  statusMessage.value = 'ファイル選択中'
  const result = await selectFilesDialog()
  isBusy.value = false

  if (!result.success) {
    errorModal.value = {
      show: true,
      summary: 'ファイル選択中にエラーが発生しました。',
      detail: result.message ?? '',
      failedFiles: [],
    }
    statusMessage.value = '選択失敗'
    return
  }

  await importItems(result.data?.items ?? [])
}

async function handleSelectFolder() {
  isBusy.value = true
  statusMessage.value = 'フォルダ選択中'
  const result = await selectFolderDialog()
  isBusy.value = false

  if (!result.success) {
    errorModal.value = {
      show: true,
      summary: 'フォルダ選択中にエラーが発生しました。',
      detail: result.message ?? '',
      failedFiles: [],
    }
    statusMessage.value = '選択失敗'
    return
  }

  await importItems(result.data?.items ?? [])
}
</script>

<template>
  <section class="file-select-area h-100">
    <div
      class="file-select-target"
      :class="{ 'is-busy': isBusy }"
    >
      <div class="file-select-main">
        <i class="bi bi-images file-select-icon" aria-hidden="true"></i>
        <p class="file-select-title mb-1">画像ファイルまたはフォルダを選択</p>
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

      <p class="file-select-status mb-0" aria-live="polite">{{ statusMessage }}</p>
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
