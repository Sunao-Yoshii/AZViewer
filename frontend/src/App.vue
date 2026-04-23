<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import LoadingOverlay from './components/common/LoadingOverlay.vue'
import MainLayout from './components/layout/MainLayout.vue'
import Home from './pages/Home.vue'
import {
  callBackendApi,
  searchImageFiles,
  updateImageFileFlags,
} from './services/backendApi'

const appInfo = ref(null)
const searchFilters = ref({
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
const toasts = ref([])
const isOverlayVisible = ref(false)
const overlayTitle = ref('ファイル状態確認中です...')
const overlayMessage = ref('起動処理を完了しています。しばらくお待ちください。')
const isSearching = ref(false)
const status = ref({
  type: 'secondary',
  message: '起動準備中',
})

function setStatus(type, message) {
  status.value = { type, message }
}

function pushToast(notification) {
  if (!notification?.message) {
    return
  }

  const id = `${Date.now()}-${Math.random().toString(16).slice(2)}`
  toasts.value = [
    ...toasts.value,
    {
      id,
      type: notification.type === 'error' ? 'danger' : 'info',
      title: notification.title ?? '',
      message: notification.message,
    },
  ]
  window.setTimeout(() => {
    toasts.value = toasts.value.filter((toast) => toast.id !== id)
  }, 6000)
}

function normalizeSearchPayload(overrides = {}) {
  const merged = { ...searchFilters.value, ...overrides }
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

function applySearchResult(data, appliedPayload) {
  searchFilters.value = {
    ...searchFilters.value,
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
    sort: appliedPayload.sort ?? 'id_desc',
  }
}

async function executeSearch(overrides = {}, overlay = false) {
  const payload = normalizeSearchPayload(overrides)
  isSearching.value = true
  if (overlay) {
    overlayTitle.value = '検索中'
    overlayMessage.value = '画像一覧を取得しています。しばらくお待ちください。'
    isOverlayVisible.value = true
  }

  try {
    const result = await searchImageFiles(payload)
    if (!result.success) {
      pushToast({ type: 'error', message: result.message || '検索に失敗しました。' })
      return false
    }
    applySearchResult(result.data ?? {}, payload)
    return true
  } finally {
    isSearching.value = false
    if (overlay) {
      isOverlayVisible.value = false
    }
  }
}

function waitForNextPaint() {
  return new Promise((resolve) => {
    window.requestAnimationFrame(() => resolve())
  })
}

async function loadInitialData() {
  setStatus('info', 'Python API に接続中')
  overlayTitle.value = 'ファイル状態確認中です...'
  overlayMessage.value = '起動処理を完了しています。しばらくお待ちください。'
  isOverlayVisible.value = true
  await nextTick()
  await waitForNextPaint()

  const initResult = await callBackendApi('initialize')

  if (!initResult.success) {
    setStatus('warning', initResult.message)
    isOverlayVisible.value = false
    return
  }

  const data = initResult.data ?? {}
  appInfo.value = data.appInfo ?? null
  if (data.startupNotification) {
    pushToast(data.startupNotification)
  }
  if (data.initialSearchResult) {
    applySearchResult(data.initialSearchResult, normalizeSearchPayload())
  }
  setStatus('success', '起動処理が完了しました')
  isOverlayVisible.value = false
}

async function runHealthCheck() {
  setStatus('info', 'ヘルスチェック実行中')
  const result = await callBackendApi('health_check')
  setStatus(result.success ? 'success' : 'danger', result.message)
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

function matchesCurrentFilters(item) {
  if (searchFilters.value.is_checked && item.is_checked !== 1) {
    return false
  }
  if (searchFilters.value.is_favorite && item.is_favorite !== 1) {
    return false
  }
  if (searchFilters.value.rating && item.rating !== searchFilters.value.rating) {
    return false
  }
  if (
    searchFilters.value.path &&
    !String(item.path).toLowerCase().includes(searchFilters.value.path.toLowerCase())
  ) {
    return false
  }
  return true
}

async function handleFlagUpdate(payload) {
  const originalItems = searchResult.value.items.map((item) => ({ ...item }))
  const nextItems = searchResult.value.items
    .map((item) => {
      if (item.id !== payload.id) {
        return item
      }
      return { ...item, [payload.field]: payload.value }
    })
    .filter(matchesCurrentFilters)

  const removedCount = searchResult.value.items.length - nextItems.length
  const nextTotalCount = Math.max(0, searchResult.value.total_count - removedCount)
  searchResult.value = {
    ...searchResult.value,
    items: nextItems,
    total_count: nextTotalCount,
    total_pages:
      nextTotalCount > 0
        ? Math.ceil(nextTotalCount / searchResult.value.page_size)
        : 0,
  }

  const result = await updateImageFileFlags(payload)
  if (result.success) {
    return
  }

  searchResult.value = {
    ...searchResult.value,
    items: originalItems,
  }
  pushToast({ type: 'error', message: 'フラグ更新に失敗しました。一覧を再取得します。' })
  await executeSearch({}, true)
}

function handleImportedEvent() {
  handleImportComplete()
}

onMounted(() => {
  window.addEventListener('azviewer:import-complete', handleImportedEvent)
  loadInitialData()
})

onBeforeUnmount(() => {
  window.removeEventListener('azviewer:import-complete', handleImportedEvent)
})
</script>

<template>
  <MainLayout
    :app-info="appInfo"
    :filters="searchFilters"
    :status="status"
    :is-searching="isSearching"
    @search="handleSearch"
    @import-complete="handleImportComplete"
    @health-check="runHealthCheck"
  >
    <Home
      :search-result="searchResult"
      :is-searching="isSearching"
      @change-page="handlePageChange"
      @change-page-size="handlePageSizeChange"
      @change-sort="handleSortChange"
      @update-flag="handleFlagUpdate"
    />
  </MainLayout>
  <LoadingOverlay
    :show="isOverlayVisible"
    :title="overlayTitle"
    :message="overlayMessage"
  />
  <div class="toast-stack" aria-live="polite" aria-atomic="true">
    <div
      v-for="toast in toasts"
      :key="toast.id"
      class="toast-card shadow-sm"
      :class="`toast-card-${toast.type}`"
      role="status"
    >
      <p v-if="toast.title" class="toast-card-title mb-1">{{ toast.title }}</p>
      <p class="mb-0">{{ toast.message }}</p>
    </div>
  </div>
</template>
