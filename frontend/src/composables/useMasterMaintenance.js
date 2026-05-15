import { reactive } from 'vue'
import {
  deleteModelMaster,
  deleteTagMaster,
  deleteUnusedModels,
  deleteUnusedTags,
  fetchModelsForMaintenance,
  fetchTagsForMaintenance,
  replaceModelMaster,
  replaceTagMaster,
} from '../services/backendApi'

function createMasterMaintenanceModal() {
  return {
    show: false,
    mode: 'tag',
    activeTab: 'delete',
    keyword: '',
    items: [],
    totalCount: 0,
    selectedItem: null,
    replacementName: '',
    isLoading: false,
    isProcessing: false,
  }
}

function modeLabel(mode) {
  return mode === 'tag' ? 'タグ' : 'モデル'
}

function buildDeleteConfirmMessage(mode, item) {
  const label = modeLabel(mode)
  const action = mode === 'tag' ? '外されます' : '解除されます'
  return [
    `${label}「${item.name}」を削除します。`,
    `この${label}は ${item.imageCount ?? 0} 件の画像から${action}。`,
    '',
    '削除しますか？',
  ].join('\n')
}

function buildReplaceConfirmMessage(mode, item, replacementName) {
  const label = modeLabel(mode)
  return [
    `${label}「${item.name}」を「${replacementName}」へ置き換えます。`,
    `この${label}は ${item.imageCount ?? 0} 件の画像に影響します。`,
    '',
    '実行しますか？',
  ].join('\n')
}

function buildDeleteUnusedConfirmMessage(mode) {
  const label = mode === 'tag' ? '未使用タグ' : '未使用モデル'
  return `${label}を一括削除します。\n\n使用件数 0 件のマスタのみ削除します。\n実行しますか？`
}

function toActionSet(mode) {
  if (mode === 'tag') {
    return {
      fetchItems: fetchTagsForMaintenance,
      deleteItem: deleteTagMaster,
      replaceItem: replaceTagMaster,
      deleteUnused: deleteUnusedTags,
    }
  }
  return {
    fetchItems: fetchModelsForMaintenance,
    deleteItem: deleteModelMaster,
    replaceItem: replaceModelMaster,
    deleteUnused: deleteUnusedModels,
  }
}

export function useMasterMaintenance({ pushToast, loading, refresh }) {
  const masterMaintenanceModal = reactive(createMasterMaintenanceModal())

  async function openMasterMaintenance(mode) {
    if (!['tag', 'model'].includes(mode)) {
      return
    }

    Object.assign(masterMaintenanceModal, createMasterMaintenanceModal(), {
      show: true,
      mode,
    })
    await searchMasterMaintenanceItems()
  }

  function closeMasterMaintenance() {
    if (masterMaintenanceModal.isProcessing) {
      return
    }

    Object.assign(masterMaintenanceModal, createMasterMaintenanceModal())
  }

  function changeMasterMaintenanceTab(tab) {
    if (!['delete', 'replace'].includes(tab) || masterMaintenanceModal.isProcessing) {
      return
    }

    masterMaintenanceModal.activeTab = tab
    masterMaintenanceModal.selectedItem = null
    masterMaintenanceModal.replacementName = ''
  }

  function updateMasterMaintenanceKeyword(keyword) {
    masterMaintenanceModal.keyword = keyword
  }

  async function searchMasterMaintenanceItems() {
    masterMaintenanceModal.isLoading = true
    try {
      const result = await toActionSet(masterMaintenanceModal.mode).fetchItems({
        keyword: masterMaintenanceModal.keyword,
        limit: 50,
      })
      applyMasterMaintenanceSearchResult(result)
    } catch {
      applyMasterMaintenanceLoadFailure()
    } finally {
      masterMaintenanceModal.isLoading = false
    }
  }

  function applyMasterMaintenanceSearchResult(result) {
    if (!result?.success) {
      applyMasterMaintenanceLoadFailure(result?.message)
      return
    }

    masterMaintenanceModal.items = result.data?.items ?? []
    masterMaintenanceModal.totalCount = result.data?.totalCount ?? 0
  }

  function applyMasterMaintenanceLoadFailure(message = 'マスタ一覧の取得に失敗しました。') {
    masterMaintenanceModal.items = []
    masterMaintenanceModal.totalCount = 0
    pushToast({ type: 'danger', message })
  }

  function selectMasterMaintenanceItem(item) {
    masterMaintenanceModal.selectedItem = item
    masterMaintenanceModal.replacementName = item?.name ?? ''
  }

  function updateReplacementName(name) {
    masterMaintenanceModal.replacementName = name
  }

  async function deleteMasterMaintenanceItem(item) {
    if (!item?.id || !window.confirm(buildDeleteConfirmMessage(masterMaintenanceModal.mode, item))) {
      return
    }

    await processMasterMutation({
      title: `${modeLabel(masterMaintenanceModal.mode)}を削除中`,
      message: 'マスタ情報を更新しています...',
      run: () => toActionSet(masterMaintenanceModal.mode).deleteItem(item.id),
      failureMessage: `${modeLabel(masterMaintenanceModal.mode)}の削除に失敗しました。`,
      success: (result) => `${modeLabel(masterMaintenanceModal.mode)}を削除しました。影響画像: ${result.data?.affectedImageCount ?? 0} 件`,
    })
  }

  async function replaceMasterMaintenanceItem() {
    const item = masterMaintenanceModal.selectedItem
    const newName = masterMaintenanceModal.replacementName.trim()
    if (!item?.id || !newName || !window.confirm(buildReplaceConfirmMessage(masterMaintenanceModal.mode, item, newName))) {
      return
    }

    await processMasterMutation({
      title: `${modeLabel(masterMaintenanceModal.mode)}を置き換え中`,
      message: 'マスタ情報を更新しています...',
      run: () => toActionSet(masterMaintenanceModal.mode).replaceItem({ id: item.id, newName }),
      failureMessage: `${modeLabel(masterMaintenanceModal.mode)}の置き換えに失敗しました。`,
      success: (result) => `${modeLabel(masterMaintenanceModal.mode)}を置き換えました。影響画像: ${result.data?.affectedImageCount ?? 0} 件`,
    })
  }

  async function deleteUnusedMasterItems() {
    if (!window.confirm(buildDeleteUnusedConfirmMessage(masterMaintenanceModal.mode))) {
      return
    }

    await processMasterMutation({
      title: `${modeLabel(masterMaintenanceModal.mode)}を整理中`,
      message: '未使用マスタを削除しています...',
      run: () => toActionSet(masterMaintenanceModal.mode).deleteUnused(),
      failureMessage: `未使用${modeLabel(masterMaintenanceModal.mode)}の削除に失敗しました。`,
      success: (result) => `未使用${modeLabel(masterMaintenanceModal.mode)}を削除しました。削除: ${result.data?.deletedCount ?? 0} 件`,
    })
  }

  async function processMasterMutation({ title, message, run, failureMessage, success }) {
    masterMaintenanceModal.isProcessing = true
    loading?.showLoading(title, message)

    try {
      const result = await run()
      if (!result?.success) {
        pushToast({ type: 'danger', message: result?.message || failureMessage })
        return
      }

      await refreshAfterMasterMutation()
      pushToast({ type: 'success', message: success(result) })
    } catch {
      pushToast({ type: 'danger', message: failureMessage })
    } finally {
      masterMaintenanceModal.isProcessing = false
      loading?.hideLoading()
    }
  }

  async function refreshAfterMasterMutation() {
    masterMaintenanceModal.selectedItem = null
    masterMaintenanceModal.replacementName = ''
    await searchMasterMaintenanceItems()
    await refresh?.()
  }

  return {
    masterMaintenanceModal,
    openMasterMaintenance,
    closeMasterMaintenance,
    changeMasterMaintenanceTab,
    updateMasterMaintenanceKeyword,
    searchMasterMaintenanceItems,
    selectMasterMaintenanceItem,
    updateReplacementName,
    deleteMasterMaintenanceItem,
    replaceMasterMaintenanceItem,
    deleteUnusedMasterItems,
  }
}
