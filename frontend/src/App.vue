<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import LoadingOverlay from './components/common/LoadingOverlay.vue'
import Content from './components/layout/Content.vue'
import MainLayout from './components/layout/MainLayout.vue'
import ImageDetailModal from './components/tile/ImageDetailModal.vue'
import placeholderUrl from './assets/images/placeholder.svg'
import {
  callBackendApi,
  deleteImageFile,
  fetchLocalImage,
  fetchLocalImageThumb,
  searchImageFiles,
  updateImageFileDetail,
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
const selectedDetailItem = ref(null)
const detailImageUrl = ref('')
const isDetailImageLoading = ref(false)
const isSavingDetail = ref(false)
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

async function applySearchResult(data, appliedPayload) {
  const items = await addThumbnailUrls(data.items ?? [])
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
    items,
    sort: appliedPayload.sort ?? 'id_desc',
  }
}

async function addThumbnailUrls(items) {
  return await Promise.all(items.map(addThumbnailUrl))
}

async function addThumbnailUrl(item) {
  const result = await fetchLocalImageThumb(item.id)
  if (!result.success) {
    return { ...item, thumbnailUrl: placeholderUrl }
  }
  return { ...item, thumbnailUrl: result.data?.dataUrl || placeholderUrl }
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
    await applySearchResult(result.data ?? {}, payload)
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
    await applySearchResult(data.initialSearchResult, normalizeSearchPayload())
  }
  setStatus('success', '起動処理が完了しました')
  isOverlayVisible.value = false
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

async function handleOpenDetail(item) {
  selectedDetailItem.value = item
  detailImageUrl.value = ''
  isDetailImageLoading.value = true

  const result = await fetchLocalImage(item.path)
  isDetailImageLoading.value = false
  if (!result.success) {
    pushToast({ type: 'error', message: result.message || '画像を読み込めませんでした。' })
    return
  }
  detailImageUrl.value = result.data?.dataUrl ?? ''
}

function handleCloseDetail() {
  selectedDetailItem.value = null
  detailImageUrl.value = ''
  isDetailImageLoading.value = false
}

async function handleDelete(id) {
  if (!window.confirm('このアプリケーション上から削除します。よろしいですか？')) {
    return
  }

  const result = await deleteImageFile(id)
  if (!result.success) {
    pushToast({ type: 'error', message: result.message || '削除に失敗しました。' })
    return
  }
  await executeSearch({}, true)
}

async function handleSaveDetail(payload) {
  isSavingDetail.value = true
  try {
    const result = await updateImageFileDetail(payload)
    if (!result.success) {
      pushToast({ type: 'error', message: result.message || '詳細の保存に失敗しました。' })
      return
    }
    handleCloseDetail()
    await executeSearch({}, true)
  } finally {
    isSavingDetail.value = false
  }
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
  >
    <Content
      :search-result="searchResult"
      :is-searching="isSearching"
      @change-page="handlePageChange"
      @change-page-size="handlePageSizeChange"
      @change-sort="handleSortChange"
      @open-detail="handleOpenDetail"
      @request-delete="handleDelete"
      @save-detail="handleSaveDetail"
    />
  </MainLayout>
  <ImageDetailModal
    :item="selectedDetailItem"
    :image-url="detailImageUrl"
    :is-loading-image="isDetailImageLoading"
    :is-saving="isSavingDetail"
    @close="handleCloseDetail"
    @save="handleSaveDetail"
  />
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
