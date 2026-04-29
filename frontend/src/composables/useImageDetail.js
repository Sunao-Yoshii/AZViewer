import { ref } from 'vue'
import {
  fetchLocalImage,
  openContainingFolder,
} from '../services/backendApi'

export function useImageDetail({ pushToast }) {
  const selectedItem = ref(null)
  const detailImageUrl = ref('')
  const isLoadingImage = ref(false)

  async function handleOpenDetail(item) {
    selectedItem.value = item
    detailImageUrl.value = ''
    isLoadingImage.value = true

    const result = await fetchLocalImage(item.path)
    isLoadingImage.value = false
    if (!result.success) {
      pushToast({ type: 'error', message: result.message || '画像を読み込めませんでした。' })
      return
    }
    detailImageUrl.value = result.data?.dataUrl ?? ''
  }

  function handleCloseDetail() {
    selectedItem.value = null
    detailImageUrl.value = ''
    isLoadingImage.value = false
  }

  async function handleOpenContainingFolder(path) {
    const result = await openContainingFolder(path)
    if (!result.success) {
      pushToast({ type: 'error', message: result.message || 'フォルダを開けませんでした。' })
    }
  }

  return {
    selectedItem,
    detailImageUrl,
    isLoadingImage,
    handleOpenDetail,
    handleCloseDetail,
    handleOpenContainingFolder,
  }
}
