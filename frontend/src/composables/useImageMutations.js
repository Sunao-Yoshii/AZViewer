import {
  deleteImageFile,
  deleteImageFilesWithPhysicalFiles,
  updateImageFileDetail,
} from '../services/backendApi'

function buildPhysicalDeleteConfirmMessage(count) {
  return [
    `選択した ${count} 件の画像を削除します。`,
    '',
    'この操作では、AZViewer 上の登録情報だけでなく、実際の画像ファイルもディスクから削除されます。',
    'この操作は元に戻せません。',
    '',
    '削除しますか？',
  ].join('\n')
}

function pushPhysicalDeleteResultToast(pushToast, result, targetCount) {
  const data = result.data ?? {}
  const failedCount = data.failedCount ?? 0

  if (failedCount > 0) {
    pushToast({
      type: 'warning',
      message: `一部画像の削除に失敗しました。対象: ${data.targetCount ?? targetCount} 件 / 削除: ${data.deletedRecordCount ?? 0} 件 / 失敗: ${failedCount} 件`,
    })
    return
  }

  pushToast({
    type: 'success',
    message: `選択画像の削除が完了しました。対象: ${data.targetCount ?? targetCount} 件 / 削除: ${data.deletedRecordCount ?? 0} 件`,
  })
}

export function useImageMutations({ pushToast, refresh, loading }) {
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

  async function deleteSelectedImages({ ids, refresh: refreshSelected, clearSelection }) {
    const targetIds = [...(ids ?? [])]
    if (targetIds.length === 0) {
      return
    }

    if (!window.confirm(buildPhysicalDeleteConfirmMessage(targetIds.length))) {
      return
    }

    loading?.showLoading(
      '選択画像を削除中',
      '実ファイル、サムネイル、登録情報を削除しています...'
    )

    try {
      const result = await deleteImageFilesWithPhysicalFiles({ ids: targetIds })
      if (!result?.success) {
        pushToast({ type: 'danger', message: result?.message || '選択画像の削除に失敗しました。' })
        return
      }

      pushPhysicalDeleteResultToast(pushToast, result, targetIds.length)
      clearSelection?.()
      await refreshSelected?.()
    } catch (error) {
      pushToast({ type: 'danger', message: '選択画像の削除に失敗しました。' })
    } finally {
      loading?.hideLoading()
    }
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
    deleteSelectedImages,
    handleDelete,
    handleSaveDetail,
  }
}
