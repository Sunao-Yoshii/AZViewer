import { reactive } from 'vue'
import { fetchDuplicateTagSets } from '../services/backendApi'

function createDuplicateTagSetModal() {
  return {
    show: false,
    items: [],
    totalCount: 0,
    limit: 256,
    isLoading: false,
    message: '',
  }
}

export function useDuplicateTagSetSearch({ pushToast, applyDuplicateTagSetCondition }) {
  const duplicateTagSetModal = reactive(createDuplicateTagSetModal())

  async function openDuplicateTagSetModal() {
    duplicateTagSetModal.show = true
    duplicateTagSetModal.items = []
    duplicateTagSetModal.totalCount = 0
    duplicateTagSetModal.message = ''
    duplicateTagSetModal.isLoading = true

    try {
      const result = await fetchDuplicateTagSets({ limit: 256 })
      if (!result?.success) {
        applyDuplicateTagSetLoadFailure(result?.message)
        return
      }

      duplicateTagSetModal.items = result.data?.items ?? []
      duplicateTagSetModal.totalCount = result.data?.totalCount ?? 0
      duplicateTagSetModal.limit = result.data?.limit ?? 256
      if (duplicateTagSetModal.items.length === 0) {
        duplicateTagSetModal.message = '重複しているタグ構成はありません。'
      }
    } catch {
      applyDuplicateTagSetLoadFailure()
    } finally {
      duplicateTagSetModal.isLoading = false
    }
  }

  function closeDuplicateTagSetModal() {
    Object.assign(duplicateTagSetModal, createDuplicateTagSetModal())
  }

  async function handleSelectDuplicateTagSet(item) {
    if (!item?.hash || !item?.tagSet) {
      pushToast({
        type: 'warning',
        message: '検索対象のタグ構成が不正です。',
      })
      return
    }

    closeDuplicateTagSetModal()
    await applyDuplicateTagSetCondition(item)
  }

  function applyDuplicateTagSetLoadFailure(message = '重複タグ構成一覧を取得できませんでした。') {
    duplicateTagSetModal.items = []
    duplicateTagSetModal.totalCount = 0
    duplicateTagSetModal.message = message || '重複タグ構成一覧を取得できませんでした。'
  }

  return {
    duplicateTagSetModal,
    openDuplicateTagSetModal,
    closeDuplicateTagSetModal,
    handleSelectDuplicateTagSet,
  }
}
