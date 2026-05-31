import { reactive } from 'vue'
import {
  bulkAddTags,
  bulkUpdateImageFileAttributes,
  exportSelectedImageTags,
  importCaptionTags as importCaptionTagsApi,
  moveImageFilesToTrash,
  moveImageFilesToFolder,
  removeImageFilesFromCatalog,
  selectFolderDialog,
  updateImageFileDetail,
} from '../services/backendApi'

function buildCatalogRemovalConfirmMessage(count) {
  return [
    `選択した ${count} 件の画像を AZViewer の管理対象から除外します。`,
    '',
    'この操作では、AZViewer 上の登録情報、タグ関連情報、モデル関連情報、サムネイルキャッシュを削除します。',
    '実際の画像ファイルは削除されません。',
    '',
    '実行しますか？',
  ].join('\n')
}

function buildTrashMoveConfirmMessage(count) {
  return [
    `選択した ${count} 件の画像を OS のごみ箱へ移動します。`,
    '',
    'ごみ箱への移動に成功した画像は、AZViewer の管理対象からも除外されます。',
    '環境によっては、ごみ箱から復元できない場合があります。',
    '',
    '実行しますか？',
  ].join('\n')
}

function pushCatalogRemovalResultToast(pushToast, result, targetCount) {
  const data = result?.data ?? {}
  pushToast({
    type: 'success',
    message: `選択画像を管理対象から除外しました。対象: ${data.targetCount ?? targetCount} 件 / 除外: ${data.removedCount ?? 0} 件 / 失敗: ${data.failedCount ?? 0} 件`,
  })
}

function pushTrashMoveResultToast(pushToast, result, targetCount) {
  const data = result?.data ?? {}
  const failedCount = data.failedCount ?? 0

  pushToast({
    type: failedCount > 0 ? 'warning' : 'success',
    message: failedCount > 0
      ? `一部画像をごみ箱へ移動できませんでした。対象: ${data.targetCount ?? targetCount} 件 / 移動: ${data.trashedCount ?? 0} 件 / 失敗: ${failedCount} 件`
      : `選択画像をごみ箱へ移動しました。対象: ${data.targetCount ?? targetCount} 件 / 移動: ${data.trashedCount ?? 0} 件`,
  })
}

function buildMoveConfirmMessage(count, destinationFolder) {
  return [
    `選択した ${count} 件の画像ファイルを移動します。`,
    '',
    '移動先:',
    destinationFolder,
    '',
    '移動後は AZViewer 上の登録パスも更新されます。',
    '実行しますか？',
  ].join('\n')
}

function extractSelectedFolderPath(result) {
  const items = result?.data?.items ?? []
  const folderItem = items.find((item) => item?.type === 'directory')
  return folderItem?.path || ''
}

function pushMoveResultToast(pushToast, result, targetCount) {
  const data = result?.data ?? {}
  const failedCount = data.failedCount ?? 0
  const movedCount = data.movedCount ?? 0
  const skippedCount = data.skippedCount ?? 0

  if (failedCount > 0 && movedCount === 0 && skippedCount === 0) {
    pushToast({
      type: 'warning',
      message: `画像ファイルを移動できませんでした。対象: ${data.targetCount ?? targetCount} 件 / 失敗: ${failedCount} 件`,
    })
    return
  }

  if (failedCount > 0) {
    pushToast({
      type: 'warning',
      message: `一部画像ファイルの移動に失敗しました。対象: ${data.targetCount ?? targetCount} 件 / 移動: ${movedCount} 件 / スキップ: ${skippedCount} 件 / 失敗: ${failedCount} 件`,
    })
    return
  }

  pushToast({
    type: 'success',
    message: `画像ファイルの移動が完了しました。対象: ${data.targetCount ?? targetCount} 件 / 移動: ${movedCount} 件 / スキップ: ${skippedCount} 件`,
  })
}

function buildTagCaptionExportConfirmMessage(count) {
  return [
    `選択した ${count} 件の画像について、画像に設定されているタグを同名の .txt ファイルとして出力します。`,
    '',
    '出力先は各画像ファイルと同じフォルダです。',
    '既に .txt ファイルが存在する場合は上書きされます。',
    'タグが設定されていない画像はスキップされます。',
    '',
    '実行しますか？',
  ].join('\n')
}

function pushTagCaptionExportResultToast(pushToast, result, targetCount) {
  const data = result?.data ?? {}
  const failedCount = data.failedCount ?? 0
  const prefix = failedCount > 0
    ? 'タグ出力が完了しましたが、一部失敗しました。'
    : 'タグ出力が完了しました。'

  pushToast({
    type: failedCount > 0 ? 'warning' : 'success',
    message: `${prefix}対象: ${data.targetCount ?? targetCount} 件 / 出力: ${data.exportedCount ?? 0} 件 / スキップ: ${data.skippedCount ?? 0} 件 / 失敗: ${failedCount} 件`,
  })
}

function buildCaptionTagImportConfirmMessage(count) {
  return [
    `選択した ${count} 件の画像について、画像と同名の caption .txt を読み込み、タグとして追加登録します。`,
    '',
    '既存タグは保持されます。',
    '同名 .txt が存在しない画像、タグが取得できない画像はスキップされます。',
    '',
    '実行しますか？',
  ].join('\n')
}

function pushCaptionTagImportResultToast(pushToast, result, targetCount) {
  const data = result?.data ?? {}
  const failedCount = data.failedCount ?? 0
  const prefix = failedCount > 0
    ? 'キャプションタグ読み込みが完了しましたが、一部失敗しました。'
    : 'キャプションタグ読み込みが完了しました。'

  pushToast({
    type: failedCount > 0 ? 'warning' : 'success',
    message: `${prefix}対象: ${data.targetCount ?? targetCount} 件 / 更新: ${data.updatedCount ?? 0} 件 / スキップ: ${data.skippedCount ?? 0} 件 / 失敗: ${failedCount} 件`,
  })
}

function pushBulkTagAddResultToast(pushToast, result, targetCount) {
  const data = result?.data ?? {}
  pushToast({
    type: (data.failedCount ?? 0) > 0 ? 'warning' : 'success',
    message: `一括タグ追加が完了しました。対象: ${data.targetCount ?? targetCount} 件 / 更新: ${data.updatedCount ?? 0} 件 / スキップ: ${data.skippedCount ?? 0} 件 / 失敗: ${data.failedCount ?? 0} 件`,
  })
}

function createBulkAttributeEditForm() {
  return {
    ratingEnabled: false,
    rating: 'General',
    checkedEnabled: false,
    isChecked: false,
    favoriteEnabled: false,
    isFavorite: false,
  }
}

function buildBulkAttributeUpdates(form) {
  const updates = {}

  if (form.ratingEnabled) {
    updates.rating = form.rating
  }

  if (form.checkedEnabled) {
    updates.isChecked = form.isChecked ? 1 : 0
  }

  if (form.favoriteEnabled) {
    updates.isFavorite = form.isFavorite ? 1 : 0
  }

  return updates
}

function pushBulkAttributeUpdateSuccessToast(pushToast, result, targetCount) {
  const data = result?.data ?? {}
  pushToast({
    type: 'success',
    message: `選択画像の属性を更新しました。対象: ${data.targetCount ?? targetCount} 件 / 更新: ${data.updatedCount ?? 0} 件`,
  })
}

function validateBulkAttributeEditRequest(pushToast, targetIds, updates) {
  if (targetIds.length === 0) {
    pushToast({
      type: 'warning',
      message: '一括編集する画像を選択してください。',
    })
    return false
  }

  if (Object.keys(updates).length === 0) {
    pushToast({
      type: 'warning',
      message: '変更する項目を選択してください。',
    })
    return false
  }

  return true
}

export function useImageMutations({ pushToast, refresh, loading }) {
  const bulkAttributeEditModal = reactive({
    show: false,
    isSaving: false,
    form: createBulkAttributeEditForm(),
  })
  const bulkTagAddModal = reactive({
    show: false,
    tagsText: '',
    isSaving: false,
  })

  function resetBulkAttributeEditForm() {
    bulkAttributeEditModal.form = createBulkAttributeEditForm()
  }

  function openBulkAttributeEditModal({ ids }) {
    const targetIds = [...(ids ?? [])]

    if (targetIds.length === 0) {
      pushToast({
        type: 'warning',
        message: '一括編集する画像を選択してください。',
      })
      return
    }

    resetBulkAttributeEditForm()
    bulkAttributeEditModal.show = true
  }

  function closeBulkAttributeEditModal() {
    bulkAttributeEditModal.show = false
    bulkAttributeEditModal.isSaving = false
    resetBulkAttributeEditForm()
  }

  function openBulkTagAddModal({ ids }) {
    const targetIds = [...(ids ?? [])]

    if (targetIds.length === 0) {
      pushToast({
        type: 'warning',
        message: 'タグを追加する画像を選択してください。',
      })
      return
    }

    bulkTagAddModal.tagsText = ''
    bulkTagAddModal.show = true
  }

  function closeBulkTagAddModal() {
    bulkTagAddModal.show = false
    bulkTagAddModal.tagsText = ''
    bulkTagAddModal.isSaving = false
  }

  function updateBulkTagAddText(value) {
    bulkTagAddModal.tagsText = value
  }

  function updateBulkAttributeEditForm({ key, value }) {
    if (!(key in bulkAttributeEditModal.form)) {
      return
    }

    bulkAttributeEditModal.form[key] = value
  }

  async function saveBulkAttributeEdit({ ids, refresh: refreshSelected, clearSelection }) {
    const targetIds = [...(ids ?? [])]
    const updates = buildBulkAttributeUpdates(bulkAttributeEditModal.form)

    if (!validateBulkAttributeEditRequest(pushToast, targetIds, updates)) {
      return
    }

    bulkAttributeEditModal.isSaving = true

    try {
      const result = await bulkUpdateImageFileAttributes({
        ids: targetIds,
        updates,
      })

      if (!result?.success) {
        pushToast({
          type: 'danger',
          message: result?.message || '選択画像の属性更新に失敗しました。',
        })
        return
      }

      pushBulkAttributeUpdateSuccessToast(pushToast, result, targetIds.length)
      clearSelection?.()
      await refreshSelected?.()
      closeBulkAttributeEditModal()
    } catch (error) {
      pushToast({
        type: 'danger',
        message: '選択画像の属性更新に失敗しました。',
      })
    } finally {
      bulkAttributeEditModal.isSaving = false
    }
  }

  async function removeSelectedImagesFromCatalog({ ids, refresh: refreshSelected, clearSelection }) {
    const targetIds = [...(ids ?? [])]
    if (targetIds.length === 0) {
      return
    }

    if (!window.confirm(buildCatalogRemovalConfirmMessage(targetIds.length))) {
      return
    }

    loading?.showLoading(
      '管理対象から除外中',
      '選択画像の登録情報を AZViewer から除外しています...'
    )

    try {
      const result = await removeImageFilesFromCatalog({ ids: targetIds })
      if (!result?.success) {
        pushToast({ type: 'danger', message: result?.message || '管理対象からの除外に失敗しました。' })
        return
      }

      pushCatalogRemovalResultToast(pushToast, result, targetIds.length)
      clearSelection?.()
      await refreshSelected?.()
    } catch (error) {
      pushToast({ type: 'danger', message: '管理対象からの除外に失敗しました。' })
    } finally {
      loading?.hideLoading()
    }
  }

  async function moveSelectedImagesToTrash({ ids, refresh: refreshSelected, clearSelection }) {
    const targetIds = [...(ids ?? [])]
    if (targetIds.length === 0) {
      return
    }

    if (!window.confirm(buildTrashMoveConfirmMessage(targetIds.length))) {
      return
    }

    loading?.showLoading(
      'ごみ箱へ移動中',
      '選択画像をごみ箱へ移動し、登録情報を整理しています...'
    )

    try {
      const result = await moveImageFilesToTrash({ ids: targetIds })
      if (!result?.success) {
        pushToast({ type: 'danger', message: result?.message || 'ごみ箱への移動に失敗しました。' })
        return
      }

      pushTrashMoveResultToast(pushToast, result, targetIds.length)
      clearSelection?.()
      await refreshSelected?.()
    } catch (error) {
      pushToast({ type: 'danger', message: 'ごみ箱への移動に失敗しました。' })
    } finally {
      loading?.hideLoading()
    }
  }

  async function moveSelectedImages({ ids, refresh: refreshSelected, clearSelection }) {
    const targetIds = [...(ids ?? [])]
    if (targetIds.length === 0) {
      return
    }

    const folderResult = await selectFolderDialog()
    if (!folderResult?.success) {
      return
    }

    const destinationFolder = extractSelectedFolderPath(folderResult)
    if (!destinationFolder || !window.confirm(buildMoveConfirmMessage(targetIds.length, destinationFolder))) {
      return
    }

    loading?.showLoading(
      '画像ファイルを移動中',
      '実ファイルの移動と登録情報の更新を行っています...'
    )

    try {
      const result = await moveImageFilesToFolder({
        ids: targetIds,
        destinationFolder,
      })
      if (!result?.success) {
        pushToast({ type: 'danger', message: result?.message || '画像ファイルの移動に失敗しました。' })
        return
      }

      pushMoveResultToast(pushToast, result, targetIds.length)
      clearSelection?.()
      await refreshSelected?.()
    } catch (error) {
      pushToast({ type: 'danger', message: '画像ファイルの移動に失敗しました。' })
    } finally {
      loading?.hideLoading()
    }
  }

  async function exportSelectedTags({ ids, clearSelection }) {
    const targetIds = [...(ids ?? [])]
    if (targetIds.length === 0) {
      return
    }

    if (!window.confirm(buildTagCaptionExportConfirmMessage(targetIds.length))) {
      return
    }

    loading?.showLoading(
      'タグを出力中',
      'タグ出現頻度を集計し、caption ファイルを出力しています...'
    )

    try {
      const result = await exportSelectedImageTags({ ids: targetIds })
      if (!result?.success) {
        pushToast({ type: 'danger', message: result?.message || 'タグ出力に失敗しました。' })
        return
      }

      pushTagCaptionExportResultToast(pushToast, result, targetIds.length)
      clearSelection?.()
    } catch (error) {
      pushToast({ type: 'danger', message: 'タグ出力に失敗しました。' })
    } finally {
      loading?.hideLoading()
    }
  }

  async function importCaptionTags({ ids, refresh: refreshSelected, clearSelection }) {
    const targetIds = [...(ids ?? [])]
    if (targetIds.length === 0) {
      return
    }

    if (!window.confirm(buildCaptionTagImportConfirmMessage(targetIds.length))) {
      return
    }

    loading?.showLoading(
      'キャプションタグを読み込み中',
      '選択画像と同名の caption ファイルからタグを追加しています...'
    )

    try {
      const result = await importCaptionTagsApi({ ids: targetIds })
      if (!result?.success) {
        pushToast({ type: 'danger', message: result?.message || 'キャプションタグ読み込みに失敗しました。' })
        return
      }

      pushCaptionTagImportResultToast(pushToast, result, targetIds.length)
      clearSelection?.()
      await refreshSelected?.()
    } catch (error) {
      pushToast({ type: 'danger', message: 'キャプションタグ読み込みに失敗しました。' })
    } finally {
      loading?.hideLoading()
    }
  }

  async function saveBulkTagAdd({ ids, refresh: refreshSelected, clearSelection }) {
    const targetIds = [...(ids ?? [])]
    if (targetIds.length === 0 || !bulkTagAddModal.tagsText.trim()) {
      pushToast({ type: 'warning', message: '追加するタグを入力してください。' })
      return
    }

    bulkTagAddModal.isSaving = true
    loading?.showLoading('タグを一括追加中', '選択画像へ指定タグを追加しています...')

    try {
      const result = await bulkAddTags({ ids: targetIds, tagsText: bulkTagAddModal.tagsText })
      if (!result?.success) {
        pushToast({ type: 'warning', message: result?.message || '一括タグ追加に失敗しました。' })
        return
      }

      pushBulkTagAddResultToast(pushToast, result, targetIds.length)
      closeBulkTagAddModal()
      clearSelection?.()
      await refreshSelected?.()
    } catch (error) {
      pushToast({ type: 'danger', message: '一括タグ追加に失敗しました。' })
    } finally {
      bulkTagAddModal.isSaving = false
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
    bulkAttributeEditModal,
    bulkTagAddModal,
    closeBulkAttributeEditModal,
    closeBulkTagAddModal,
    exportSelectedTags,
    handleSaveDetail,
    importCaptionTags,
    moveSelectedImages,
    moveSelectedImagesToTrash,
    openBulkAttributeEditModal,
    openBulkTagAddModal,
    removeSelectedImagesFromCatalog,
    saveBulkAttributeEdit,
    saveBulkTagAdd,
    updateBulkAttributeEditForm,
    updateBulkTagAddText,
  }
}
