import { nextTick, ref } from 'vue'
import placeholderUrl from '../assets/images/placeholder.svg'
import {
  callBackendApi,
  fetchLocalImageThumb,
  searchImageFiles,
} from '../services/backendApi'

function waitForNextPaint() {
  return new Promise((resolve) => {
    window.requestAnimationFrame(() => resolve())
  })
}

export function useImageSearch({ pushToast, setStatus, loading }) {
  const appInfo = ref(null)
  const filters = ref({
    path: '',
    rating: '',
    is_checked: false,
    is_favorite: false,
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
      page: merged.page,
      page_size: merged.page_size,
      sort: merged.sort,
    }
  }

  async function addThumbnailUrl(item) {
    const result = await fetchLocalImageThumb(item.id)
    if (!result.success) {
      return { ...item, thumbnailUrl: placeholderUrl }
    }
    return { ...item, thumbnailUrl: result.data?.dataUrl || placeholderUrl }
  }

  async function addThumbnailUrls(items) {
    return await Promise.all(items.map(addThumbnailUrl))
  }

  async function applySearchResult(data, appliedPayload) {
    const items = await addThumbnailUrls(data.items ?? [])
    filters.value = {
      ...filters.value,
      path: appliedPayload.path ?? '',
      rating: appliedPayload.rating ?? '',
      is_checked: appliedPayload.is_checked === 1,
      is_favorite: appliedPayload.is_favorite === 1,
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
    await executeSearch({ page: 1 }, true)
  }

  async function handleImportComplete() {
    await executeSearch({}, true)
  }

  async function handlePageChange(page) {
    await executeSearch({ page }, true)
  }

  async function handlePageSizeChange(pageSize) {
    await executeSearch({ page: 1, page_size: pageSize }, true)
  }

  async function handleSortChange(sort) {
    await executeSearch({ page: 1, sort }, true)
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
  }
}
