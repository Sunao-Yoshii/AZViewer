<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import DuplicateTagSetModal from './components/form/DuplicateTagSetModal.vue'
import WildcardExportModal from './components/form/WildcardExportModal.vue'
import LoadingOverlay from './components/common/LoadingOverlay.vue'
import Content from './components/layout/Content.vue'
import MainLayout from './components/layout/MainLayout.vue'
import ImageDetailModal from './components/tile/ImageDetailModal.vue'
import { useAppStatus } from './composables/useAppStatus'
import { useDuplicateTagSetSearch } from './composables/useDuplicateTagSetSearch'
import { useImageDetail } from './composables/useImageDetail'
import { useImageMutations } from './composables/useImageMutations'
import { usePromptTagImport } from './composables/usePromptTagImport'
import { useImageSearch } from './composables/useImageSearch'
import { useLoadingOverlay } from './composables/useLoadingOverlay'
import { useToast } from './composables/useToast'
import { useWildcardExport } from './composables/useWildcardExport'

const { status, setStatus } = useAppStatus()
const { toasts, pushToast } = useToast()
const loading = useLoadingOverlay()
const selectedImageIdSet = ref(new Set())
const selectedImageIds = computed(() => [...selectedImageIdSet.value])
const selectedCount = computed(() => selectedImageIds.value.length)

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
  applyDuplicateTagSetCondition,
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
  deleteSelectedImages,
  handleDelete,
  handleSaveDetail,
  moveSelectedImages,
} = useImageMutations({
  pushToast,
  setStatus,
  refresh: executeSearch,
  loading,
})
const {
  isImporting: isImportingPromptTags,
  handleImportPromptTags,
} = usePromptTagImport({
  pushToast,
  loading,
  refresh: executeSearch,
})
const duplicateTagSetSearch = useDuplicateTagSetSearch({
  pushToast,
  applyDuplicateTagSetCondition,
})
const wildcardExport = useWildcardExport({
  pushToast,
  clearSelection,
})

function clearSelection() {
  selectedImageIdSet.value = new Set()
}

function handleSelectionChange({ id, selected }) {
  const next = new Set(selectedImageIdSet.value)
  if (selected) {
    next.add(id)
  } else {
    next.delete(id)
  }
  selectedImageIdSet.value = next
}

async function handleSearchWithSelectionClear() {
  clearSelection()
  await handleSearch()
}

async function handleImportCompleteWithSelectionClear() {
  clearSelection()
  await handleImportComplete()
}

async function handlePageChangeWithSelectionClear(page) {
  clearSelection()
  await handlePageChange(page)
}

async function handlePageSizeChangeWithSelectionClear(pageSize) {
  clearSelection()
  await handlePageSizeChange(pageSize)
}

async function handleSortChangeWithSelectionClear(sort) {
  clearSelection()
  await handleSortChange(sort)
}

async function handleDeleteSelectedImages() {
  await deleteSelectedImages({
    ids: selectedImageIds.value,
    refresh: executeSearch,
    clearSelection,
  })
}

async function handleMoveSelectedImages() {
  await moveSelectedImages({
    ids: selectedImageIds.value,
    refresh: executeSearch,
    clearSelection,
  })
}

function handleOpenWildcardExport() {
  wildcardExport.openWildcardExportModal({
    ids: selectedImageIds.value,
    currentItems: searchResult.value.items,
  })
}

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

  handleImportCompleteWithSelectionClear()
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
    :selected-count="selectedCount"
    :selected-image-ids="selectedImageIds"
    @search="handleSearchWithSelectionClear"
    @import-complete="handleImportCompleteWithSelectionClear"
    @import-prompt-tags="handleImportPromptTags"
    @delete-selected-images="handleDeleteSelectedImages"
    @move-selected-images="handleMoveSelectedImages"
    @open-wildcard-export="handleOpenWildcardExport"
    @open-duplicate-tag-sets="duplicateTagSetSearch.openDuplicateTagSetModal"
  >
    <Content
      :search-result="searchResult"
      :is-searching="isSearching"
      :selected-image-ids="selectedImageIds"
      @change-page="handlePageChangeWithSelectionClear"
      @change-page-size="handlePageSizeChangeWithSelectionClear"
      @change-sort="handleSortChangeWithSelectionClear"
      @open-detail="handleOpenDetail"
      @request-delete="handleDelete"
      @save-detail="handleSaveDetail"
      @selection-change="handleSelectionChange"
    />
  </MainLayout>
  <ImageDetailModal
    :item="selectedItem"
    :image-url="detailImageUrl"
    :is-loading-image="isLoadingImage"
    @close="handleCloseDetail"
    @open-folder="handleOpenContainingFolder"
  />
  <DuplicateTagSetModal
    :show="duplicateTagSetSearch.duplicateTagSetModal.show"
    :items="duplicateTagSetSearch.duplicateTagSetModal.items"
    :total-count="duplicateTagSetSearch.duplicateTagSetModal.totalCount"
    :limit="duplicateTagSetSearch.duplicateTagSetModal.limit"
    :is-loading="duplicateTagSetSearch.duplicateTagSetModal.isLoading"
    :message="duplicateTagSetSearch.duplicateTagSetModal.message"
    @close="duplicateTagSetSearch.closeDuplicateTagSetModal"
    @select="duplicateTagSetSearch.handleSelectDuplicateTagSet"
  />
  <WildcardExportModal
    :show="wildcardExport.wildcardExportModal.show"
    :export-mode="wildcardExport.wildcardExportModal.exportMode"
    :tag-items="wildcardExport.wildcardExportModal.tagItems"
    :preview-text="wildcardExport.wildcardExportModal.previewText"
    :selected-count="wildcardExport.wildcardExportModal.selectedIds.length"
    :output-line-count="wildcardExport.wildcardExportModal.outputLineCount"
    :is-saving="wildcardExport.wildcardExportModal.isSaving"
    @close="wildcardExport.closeWildcardExportModal"
    @change-mode="wildcardExport.changeWildcardExportMode"
    @toggle-tag="wildcardExport.toggleWildcardExportTag"
    @save="wildcardExport.saveWildcardExport"
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
