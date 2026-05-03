import { reactive } from 'vue'
import { fetchImageMetadata } from '../services/backendApi'
import { useToast } from './useToast'

export function useImageMetadata() {
  const { pushToast } = useToast()
  const metadataModal = reactive({
    show: false,
    mode: 'display',
    item: null,
    metadataText: '',
    isLoading: false,
  })

  async function openMetadataModal(item, mode = 'display') {
    metadataModal.show = true
    metadataModal.mode = mode
    metadataModal.item = item
    metadataModal.metadataText = ''
    metadataModal.isLoading = true

    try {
      const result = await fetchImageMetadata(item?.path)
      if (!result?.success) {
        metadataModal.metadataText = ''
        pushToast({
          type: 'danger',
          message: result?.message || 'メタ情報を取得できませんでした',
        })
        return
      }

      metadataModal.metadataText = result.data?.metadata ?? ''
    } catch {
      metadataModal.metadataText = ''
      pushToast({
        type: 'danger',
        message: 'メタ情報を取得できませんでした',
      })
    } finally {
      metadataModal.isLoading = false
    }
  }

  function closeMetadataModal() {
    metadataModal.show = false
    metadataModal.mode = 'display'
    metadataModal.item = null
    metadataModal.metadataText = ''
    metadataModal.isLoading = false
  }

  async function handleCopyMetadataText({ text }) {
    const value = text ?? ''
    if (!value) {
      pushToast({
        type: 'warning',
        message: 'テキストが選択されていません',
      })
      return false
    }

    try {
      await writeClipboardText(value)
      pushToast({
        type: 'success',
        message: '選択テキストをコピーしました',
      })
      return true
    } catch {
      pushToast({
        type: 'danger',
        message: 'クリップボードへのコピーに失敗しました',
      })
      return false
    }
  }

  async function handleApplyMetadataTags({ text }, applyToTagInput) {
    const value = sanitizeMetadataSelection(text)
    if (!value) {
      pushToast({
        type: 'warning',
        message: 'テキストが選択されていません',
      })
      return
    }

    try {
      await writeClipboardText(value)
    } catch {
      pushToast({
        type: 'warning',
        message: 'コピーには失敗しましたが、タグ入力欄へ反映します',
      })
    }

    applyToTagInput(value)
    closeMetadataModal()
    pushToast({
      type: 'success',
      message: '選択テキストをタグ入力欄へ反映しました',
    })
  }

  return {
    metadataModal,
    openMetadataModal,
    closeMetadataModal,
    handleCopyMetadataText,
    handleApplyMetadataTags,
  }
}

export function sanitizeMetadataSelection(value) {
  return String(value ?? '')
    .replace(/[\r\n\t]/g, ' ')
    .replace(/[\x00-\x1F\x7F]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
}

async function writeClipboardText(value) {
  if (!navigator.clipboard?.writeText) {
    throw new Error('Clipboard API is unavailable.')
  }

  await navigator.clipboard.writeText(value)
}
