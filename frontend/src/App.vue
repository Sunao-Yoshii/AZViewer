<script setup>
import { onBeforeUnmount, onMounted } from 'vue'
import LoadingOverlay from './components/common/LoadingOverlay.vue'
import Content from './components/layout/Content.vue'
import MainLayout from './components/layout/MainLayout.vue'
import ImageDetailModal from './components/tile/ImageDetailModal.vue'
import { useAppStatus } from './composables/useAppStatus'
import { useImageDetail } from './composables/useImageDetail'
import { useImageMutations } from './composables/useImageMutations'
import { usePromptTagImport } from './composables/usePromptTagImport'
import { useImageSearch } from './composables/useImageSearch'
import { useLoadingOverlay } from './composables/useLoadingOverlay'
import { useToast } from './composables/useToast'

const { status, setStatus } = useAppStatus()
const { toasts, pushToast } = useToast()
const loading = useLoadingOverlay()

const {
  appInfo,
  filters,
  searchResult,
  isSearching,
  executeSearch,
  loadInitialData,
  handleSearch,
  handleImportComplete,
  handlePageChange,
  handlePageSizeChange,
  handleSortChange,
} = useImageSearch({
  pushToast,
  setStatus,
  loading,
})
const {
  selectedItem,
  detailImageUrl,
  isLoadingImage,
  handleOpenDetail,
  handleCloseDetail,
  handleOpenContainingFolder,
} = useImageDetail({
  pushToast,
  setStatus,
  loading,
})
const {
  handleDelete,
  handleSaveDetail,
} = useImageMutations({
  pushToast,
  setStatus,
  refresh: executeSearch,
})
const {
  isImporting: isImportingPromptTags,
  handleImportPromptTags,
} = usePromptTagImport({
  pushToast,
  loading,
  refresh: executeSearch,
})

function handleImportStartedEvent() {
  loading.showLoading('登録中', 'ドロップされた画像ファイルを登録しています。しばらくお待ちください。')
}

function handleImportedEvent(event) {
  loading.hideLoading()
  if (event.detail?.success === false) {
    pushToast({
      type: 'error',
      message: event.detail.data?.errorSummary ||
        event.detail.message ||
        'ドロップされたファイルの登録に失敗しました。',
    })
    return
  }

  handleImportComplete()
}

onMounted(() => {
  window.addEventListener('azviewer:import-start', handleImportStartedEvent)
  window.addEventListener('azviewer:import-complete', handleImportedEvent)
  loadInitialData()
})

onBeforeUnmount(() => {
  window.removeEventListener('azviewer:import-start', handleImportStartedEvent)
  window.removeEventListener('azviewer:import-complete', handleImportedEvent)
})
</script>

<template>
  <MainLayout
    :app-info="appInfo"
    :filters="filters"
    :status="status"
    :is-searching="isSearching || isImportingPromptTags"
    @search="handleSearch"
    @import-complete="handleImportComplete"
    @import-prompt-tags="handleImportPromptTags"
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
    :item="selectedItem"
    :image-url="detailImageUrl"
    :is-loading-image="isLoadingImage"
    @close="handleCloseDetail"
    @open-folder="handleOpenContainingFolder"
  />
  <LoadingOverlay
    :show="loading.loadingOverlay.show"
    :title="loading.loadingOverlay.title"
    :message="loading.loadingOverlay.message"
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
