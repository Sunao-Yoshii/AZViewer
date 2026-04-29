import { ref } from 'vue'
import {
  importSelectedItems,
  selectFilesDialog,
  selectFolderDialog,
} from '../services/backendApi'

function createClosedErrorModal() {
  return {
    show: false,
    summary: '',
    detail: '',
    failedFiles: [],
  }
}

export function useImageImport({ emit }) {
  const isBusy = ref(false)
  const statusMessage = ref('')
  const errorModal = ref(createClosedErrorModal())

  function closeErrorModal() {
    errorModal.value = createClosedErrorModal()
  }

  function showSelectionError(summary, result) {
    errorModal.value = {
      show: true,
      summary,
      detail: result.message ?? '',
      failedFiles: [],
    }
    statusMessage.value = '選択失敗'
  }

  function applyImportSuccess(result) {
    const importedCount = result.data?.importedCount ?? 0
    const skippedCount = result.data?.skippedCount ?? 0
    statusMessage.value = `登録 ${importedCount} 件 / 除外 ${skippedCount} 件`
    emit('import-complete', { importedCount, skippedCount })
  }

  function applyImportFailure(result, items) {
    errorModal.value = {
      show: true,
      summary: result.data?.errorSummary ?? 'データ登録中にエラーが発生しました。',
      detail: result.message ?? '',
      failedFiles: result.data?.failedFiles ?? items.map((item) => item.path),
    }
    statusMessage.value = '登録失敗'
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
      applyImportSuccess(result)
    } else {
      applyImportFailure(result, items)
    }

    isBusy.value = false
  }

  async function handleSelectFiles() {
    isBusy.value = true
    statusMessage.value = 'ファイル選択中'
    const result = await selectFilesDialog()
    isBusy.value = false

    if (!result.success) {
      showSelectionError('ファイル選択中にエラーが発生しました。', result)
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
      showSelectionError('フォルダ選択中にエラーが発生しました。', result)
      return
    }

    await importItems(result.data?.items ?? [])
  }

  return {
    isBusy,
    statusMessage,
    errorModal,
    closeErrorModal,
    importItems,
    handleSelectFiles,
    handleSelectFolder,
  }
}
