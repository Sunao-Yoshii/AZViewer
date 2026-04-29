import {
  deleteImageFile,
  updateImageFileDetail,
} from '../services/backendApi'

export function useImageMutations({ pushToast, refresh }) {
  async function handleDelete(id) {
    if (!window.confirm('このアプリケーション上から削除します。よろしいですか？')) {
      return
    }

    const result = await deleteImageFile(id)
    if (!result.success) {
      pushToast({ type: 'error', message: result.message || '削除に失敗しました。' })
      return
    }
    await refresh({}, true)
  }

  async function handleSaveDetail(payload) {
    const result = await updateImageFileDetail(payload)
    if (!result.success) {
      pushToast({ type: 'error', message: result.message || '詳細の保存に失敗しました。' })
      return
    }
    await refresh({}, true)
  }

  return {
    handleDelete,
    handleSaveDetail,
  }
}
