import { nextTick, ref } from 'vue'
import {
  callBackendApi,
  searchImageFiles,
} from '../services/backendApi'

export const PAGE_SIZE_OPTIONS = [25, 50, 75, 100, 200, 500, 1000, 2500]
export const LARGE_PAGE_SIZE_THRESHOLD = 500
export const CONFIRM_PAGE_SIZE_THRESHOLD = 1000

function waitForNextPaint() {
  return new Promise((resolve) => {
    window.requestAnimationFrame(() => resolve())
  })
}

function normalizePageSize(value) {
  const pageSize = Number(value)
  return PAGE_SIZE_OPTIONS.includes(pageSize) ? pageSize : 25
}

function normalizePage(value) {
  const page = Number(value)
  return Number.isFinite(page) ? Math.max(1, Math.trunc(page)) : 1
}

export function useImageSearch({ pushToast, setStatus, loading }) {
  const appInfo = ref(null)
  const filters = ref({
    path: '',
    rating: '',
    is_checked: false,
    is_favorite: false,
    tags: [],
    folder: null,
    model: null,
    tagHash: null,
    tagSet: null,
    duplicateTagNames: null,
    tag_keyword: '',
    page: 1,
    page_size: 25,
    sort: 'id_desc',
  })
  const searchResult = ref({
    items: [],
    total_count: 0,
    total_pages: 0,
    page: 1,
    page_size: 25,
    sort: 'id_desc',
  })
  const isSearching = ref(false)
  const currentSearchPayload = ref(normalizeSearchPayload())

  function normalizeSearchPayload(overrides = {}) {
    const merged = { ...filters.value, ...overrides }
    return {
      path: merged.path,
      rating: merged.rating || null,
      is_checked: merged.is_checked ? 1 : null,
      is_favorite: merged.is_favorite ? 1 : null,
      tags: [...(merged.tags ?? [])].slice(0, 3),
      folder: merged.folder || null,
      model: merged.model || null,
      tag_hash: merged.tagHash || null,
      tag_set: merged.tagSet || null,
      tag_keyword: String(merged.tag_keyword ?? '').trim() || null,
      page: normalizePage(merged.page),
      page_size: normalizePageSize(merged.page_size),
      sort: merged.sort,
    }
  }

  async function applySearchResult(data, appliedPayload) {
    const items = [...(data.items ?? [])]
    filters.value = {
      ...filters.value,
      path: appliedPayload.path ?? '',
      rating: appliedPayload.rating ?? '',
      is_checked: appliedPayload.is_checked === 1,
      is_favorite: appliedPayload.is_favorite === 1,
      tags: [...(appliedPayload.tags ?? [])].slice(0, 3),
      folder: appliedPayload.folder ?? null,
      model: appliedPayload.model ?? null,
      tagHash: appliedPayload.tag_hash ?? null,
      tagSet: appliedPayload.tag_set ?? null,
      duplicateTagNames: filters.value.duplicateTagNames ?? null,
      tag_keyword: appliedPayload.tag_keyword ?? '',
      page: data.page ?? appliedPayload.page ?? 1,
      page_size: data.page_size ?? appliedPayload.page_size ?? 25,
      sort: appliedPayload.sort ?? 'id_desc',
    }
    searchResult.value = {
      ...data,
      items,
      sort: appliedPayload.sort ?? 'id_desc',
    }
    currentSearchPayload.value = appliedPayload
  }

  function clearDuplicateTagSetCondition() {
    filters.value = {
      ...filters.value,
      tagHash: null,
      tagSet: null,
      duplicateTagNames: null,
    }
  }

  async function applyDuplicateTagSetCondition(item) {
    filters.value = {
      ...filters.value,
      path: '',
      rating: '',
      is_checked: false,
      is_favorite: false,
      tags: [],
      folder: null,
      model: null,
      tagHash: item.hash,
      tagSet: item.tagSet,
      duplicateTagNames: item.tagNames,
      tag_keyword: '',
    }
    return await executeSearch({ page: 1 }, true)
  }

  async function executeSearch(overrides = {}, overlay = false) {
    const payload = normalizeSearchPayload(overrides)
    isSearching.value = true
    if (overlay) {
      loading.showLoading('検索中', '画像一覧を取得しています。しばらくお待ちください。')
    }

    try {
      const result = await searchImageFiles(payload)
      if (!result.success) {
        pushToast({ type: 'error', message: result.message || '検索に失敗しました。' })
        return false
      }
      await applySearchResult(result.data ?? {}, payload)
      return true
    } finally {
      isSearching.value = false
      if (overlay) {
        loading.hideLoading()
      }
    }
  }

  async function loadInitialData() {
    setStatus('info', 'Python API に接続中')
    loading.showLoading('ファイル状態確認中です...', '起動処理を完了しています。しばらくお待ちください。')
    await nextTick()
    await waitForNextPaint()

    const initResult = await callBackendApi('initialize')
    if (!initResult.success) {
      setStatus('warning', initResult.message)
      loading.hideLoading()
      return
    }

    const data = initResult.data ?? {}
    appInfo.value = data.appInfo ?? null
    if (data.startupNotification) {
      pushToast(data.startupNotification)
    }
    if (data.initialSearchResult) {
      await applySearchResult(data.initialSearchResult, normalizeSearchPayload())
    }
    setStatus('success', '起動処理が完了しました')
    loading.hideLoading()
  }

  async function handleSearch() {
    clearDuplicateTagSetCondition()
    return await executeSearch({ page: 1 }, true)
  }

  async function handleImportComplete() {
    return await executeSearch({}, true)
  }

  async function handlePageChange(page) {
    return await executeSearch({ page }, true)
  }

  async function handlePageSizeChange(pageSize) {
    const nextPageSize = normalizePageSize(pageSize)
    if (nextPageSize >= CONFIRM_PAGE_SIZE_THRESHOLD) {
      const confirmed = window.confirm(
        '1000件以上を表示すると、画像数や端末性能によって動作が重くなる場合があります。\nページサイズを変更しますか？'
      )

      if (!confirmed) {
        return { cancelled: true }
      }
    }

    const changed = await executeSearch({ page: 1, page_size: nextPageSize }, true)
    return { changed }
  }

  async function handleSortChange(sort) {
    return await executeSearch({ page: 1, sort }, true)
  }

  return {
    appInfo,
    filters,
    searchResult,
    isSearching,
    currentSearchPayload,
    executeSearch,
    loadInitialData,
    handleSearch,
    handleImportComplete,
    handlePageChange,
    handlePageSizeChange,
    handleSortChange,
    applyDuplicateTagSetCondition,
    clearDuplicateTagSetCondition,
  }
}
