<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import BulkAttributeEditModal from './components/form/BulkAttributeEditModal.vue'
import BulkTagAddModal from './components/form/BulkTagAddModal.vue'
import DuplicateTagSetModal from './components/form/DuplicateTagSetModal.vue'
import ImageRenameModal from './components/form/ImageRenameModal.vue'
import MasterMaintenanceModal from './components/form/MasterMaintenanceModal.vue'
import WildcardExportModal from './components/form/WildcardExportModal.vue'
import LoadingOverlay from './components/common/LoadingOverlay.vue'
import Content from './components/layout/Content.vue'
import MainLayout from './components/layout/MainLayout.vue'
import ImageDetailViewer from './components/tile/ImageDetailViewer.vue'
import { useAppStatus } from './composables/useAppStatus'
import { useDuplicateTagSetSearch } from './composables/useDuplicateTagSetSearch'
import { useImageDetail } from './composables/useImageDetail'
import { useImageMutations } from './composables/useImageMutations'
import { usePromptTagImport } from './composables/usePromptTagImport'
import { useImageSearch } from './composables/useImageSearch'
import { useLoadingOverlay } from './composables/useLoadingOverlay'
import { useMasterMaintenance } from './composables/useMasterMaintenance'
import { useToast } from './composables/useToast'
import { useWildcardExport } from './composables/useWildcardExport'

const { status, setStatus } = useAppStatus()
const { toasts, pushToast } = useToast()
const loading = useLoadingOverlay()
const selectedImageIdSet = ref(new Set())
const editingImageId = ref(null)
const isDetailActionBusy = ref(false)
const renameModal = reactive({
  show: false,
  item: null,
  filename: '',
  isSaving: false,
  errorMessage: '',
})
const selectedImageIds = computed(() => [...selectedImageIdSet.value])
const selectedCount = computed(() => selectedImageIds.value.length)
const currentPageImageIds = computed(() => (searchResult.value.items ?? []).map((item) => item.id))
const currentPageCount = computed(() => currentPageImageIds.value.length)
const isAllCurrentPageSelected = computed(() => {
  const ids = currentPageImageIds.value

  if (ids.length === 0) {
    return false
  }

  return ids.every((id) => selectedImageIdSet.value.has(id))
})

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
  detailModal,
  hasNext,
  hasPrevious,
  selectedItem,
  detailImageUrl,
  isLoadingImage,
  handleCloseDetail,
  loadDetailImage,
  moveNext,
  movePrevious,
  openDetail,
  refreshDetailItemsAfterSearch,
} = useImageDetail({
  pushToast,
  setStatus,
  loading,
})
const imageMutations = useImageMutations({
  pushToast,
  setStatus,
  refresh: executeSearch,
  loading,
})
const {
  exportSelectedTags,
  handleSaveDetail,
  moveSelectedImages,
} = imageMutations
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
const masterMaintenance = useMasterMaintenance({
  pushToast,
  loading,
  refresh: executeSearch,
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

function handleToggleCurrentPageSelection() {
  const ids = currentPageImageIds.value

  if (ids.length === 0) {
    return
  }

  const next = new Set(selectedImageIdSet.value)

  if (isAllCurrentPageSelected.value) {
    ids.forEach((id) => next.delete(id))
  } else {
    ids.forEach((id) => next.add(id))
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
  const changed = await handlePageChange(page)
  if (changed !== false) {
    clearSelection()
  }
}

async function handlePageSizeChangeWithSelectionClear(pageSize) {
  const result = await handlePageSizeChange(pageSize)
  if (result?.cancelled) {
    return
  }
  if (result?.changed !== false) {
    clearSelection()
  }
}

async function handleSortChangeWithSelectionClear(sort) {
  const changed = await handleSortChange(sort)
  if (changed !== false) {
    clearSelection()
  }
}

async function handleOpenDetail(item) {
  await openDetail({
    item,
    items: searchResult.value.items,
  })
}

async function handleRemoveSelectedImagesFromCatalog() {
  await imageMutations.removeSelectedImagesFromCatalog({
    ids: selectedImageIds.value,
    refresh: executeSearch,
    clearSelection,
  })
}

async function handleMoveSelectedImagesToTrash() {
  await imageMutations.moveSelectedImagesToTrash({
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

function handleOpenBulkAttributeEdit() {
  imageMutations.openBulkAttributeEditModal({
    ids: selectedImageIds.value,
  })
}

async function handleSaveBulkAttributeEdit() {
  await imageMutations.saveBulkAttributeEdit({
    ids: selectedImageIds.value,
    refresh: executeSearch,
    clearSelection,
  })
}

async function handleImportCaptionTags() {
  await imageMutations.importCaptionTags({
    ids: selectedImageIds.value,
    refresh: executeSearch,
    clearSelection,
  })
}

function handleOpenBulkTagAdd() {
  imageMutations.openBulkTagAddModal({
    ids: selectedImageIds.value,
  })
}

async function handleSaveBulkTagAdd() {
  await imageMutations.saveBulkTagAdd({
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

async function handleExportSelectedTags() {
  await exportSelectedTags({
    ids: selectedImageIds.value,
    clearSelection,
  })
}

function buildDetailTrashConfirmMessage() {
  return [
    'この画像を OS のごみ箱へ移動します。',
    '',
    'ごみ箱への移動に成功した場合、AZViewer の管理対象からも除外されます。',
    '環境によっては、ごみ箱から復元できない場合があります。',
    '',
    '実行しますか？',
  ].join('\n')
}

async function handleMoveDetailImageToTrash(item) {
  if (!item?.id || !window.confirm(buildDetailTrashConfirmMessage())) {
    return
  }

  const currentIndex = detailModal.currentIndex
  const nextCandidateId = detailModal.items[currentIndex + 1]?.id ?? null
  const previousCandidateId = detailModal.items[currentIndex - 1]?.id ?? null
  isDetailActionBusy.value = true

  try {
    const result = await imageMutations.moveSingleImageToTrash({ id: item.id })
    if (!result?.success || (result.data?.failedCount ?? 0) > 0) {
      pushToast({ type: 'danger', message: '画像をごみ箱へ移動できませんでした。' })
      return
    }

    pushToast({ type: 'success', message: '画像をごみ箱へ移動しました。' })
    const searched = await executeSearch()
    if (!searched) {
      return
    }

    const nextItem = refreshDetailItemsAfterSearch(
      searchResult.value.items,
      nextCandidateId,
      previousCandidateId
    )
    if (nextItem) {
      await loadDetailImage(nextItem)
    }
  } finally {
    isDetailActionBusy.value = false
  }
}

function handleOpenRenameModal(item) {
  renameModal.show = true
  renameModal.item = item
  renameModal.filename = item?.filename || ''
  renameModal.errorMessage = ''
}

function closeRenameModal() {
  if (renameModal.isSaving) {
    return
  }
  renameModal.show = false
  renameModal.item = null
  renameModal.filename = ''
  renameModal.errorMessage = ''
}

function updateRenameFilename(filename) {
  renameModal.filename = filename
  renameModal.errorMessage = ''
}

async function handleRenameImage() {
  const item = renameModal.item
  if (!item?.id) {
    return
  }

  renameModal.isSaving = true
  renameModal.errorMessage = ''

  try {
    const result = await imageMutations.renameSingleImageFile({
      id: item.id,
      filename: renameModal.filename,
    })
    if (!result?.success) {
      renameModal.errorMessage = result?.message || 'ファイル名を変更できませんでした。'
      return
    }

    closeRenameModalAfterSave()
    pushToast({ type: 'success', message: 'ファイル名を変更しました。' })
    const searched = await executeSearch()
    if (!searched) {
      return
    }

    const nextItem = refreshDetailItemsAfterSearch(searchResult.value.items, item.id, null)
    if (nextItem) {
      await loadDetailImage(nextItem)
    }
  } finally {
    renameModal.isSaving = false
  }
}

function closeRenameModalAfterSave() {
  renameModal.show = false
  renameModal.item = null
  renameModal.filename = ''
  renameModal.errorMessage = ''
}

async function handleEditCurrentFromDetail(item) {
  if (!item?.id) {
    return
  }

  handleCloseDetail()
  editingImageId.value = item.id
  await nextTick()

  document.getElementById(`image-tile-${item.id}`)?.scrollIntoView({
    behavior: 'smooth',
    block: 'center',
  })
}

async function handleOpenDetailImageContainingFolder(item) {
  await imageMutations.openContainingFolder({
    path: item?.path,
  })
}

function handleTileEditFinished(id) {
  if (editingImageId.value === id) {
    editingImageId.value = null
  }
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
    :current-page-count="currentPageCount"
    :is-all-current-page-selected="isAllCurrentPageSelected"
    @search="handleSearchWithSelectionClear"
    @import-complete="handleImportCompleteWithSelectionClear"
    @import-prompt-tags="handleImportPromptTags"
    @import-caption-tags="handleImportCaptionTags"
    @toggle-current-page-selection="handleToggleCurrentPageSelection"
    @remove-selected-images-from-catalog="handleRemoveSelectedImagesFromCatalog"
    @move-selected-images-to-trash="handleMoveSelectedImagesToTrash"
    @move-selected-images="handleMoveSelectedImages"
    @open-bulk-attribute-edit="handleOpenBulkAttributeEdit"
    @open-bulk-tag-add="handleOpenBulkTagAdd"
    @open-wildcard-export="handleOpenWildcardExport"
    @export-selected-tags="handleExportSelectedTags"
    @open-duplicate-tag-sets="duplicateTagSetSearch.openDuplicateTagSetModal"
    @open-master-maintenance="masterMaintenance.openMasterMaintenance"
  >
    <Content
      :search-result="searchResult"
      :is-searching="isSearching"
      :selected-image-ids="selectedImageIds"
      :editing-image-id="editingImageId"
      @change-page="handlePageChangeWithSelectionClear"
      @change-page-size="handlePageSizeChangeWithSelectionClear"
      @change-sort="handleSortChangeWithSelectionClear"
      @edit-finished="handleTileEditFinished"
      @open-detail="handleOpenDetail"
      @save-detail="handleSaveDetail"
      @selection-change="handleSelectionChange"
    />
  </MainLayout>
  <ImageDetailViewer
    :show="detailModal.show"
    :item="selectedItem"
    :image-src="detailImageUrl"
    :has-previous="hasPrevious"
    :has-next="hasNext"
    :current-index="detailModal.currentIndex"
    :total-count="detailModal.items.length"
    :is-busy="isSearching || isLoadingImage || isDetailActionBusy"
    :is-loading-image="isLoadingImage"
    :is-keyboard-blocked="renameModal.show"
    @close="handleCloseDetail"
    @previous="movePrevious"
    @next="moveNext"
    @move-to-trash="handleMoveDetailImageToTrash"
    @rename="handleOpenRenameModal"
    @edit-current="handleEditCurrentFromDetail"
    @open-containing-folder="handleOpenDetailImageContainingFolder"
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
  <BulkAttributeEditModal
    :show="imageMutations.bulkAttributeEditModal.show"
    :selected-count="selectedCount"
    :form="imageMutations.bulkAttributeEditModal.form"
    :is-saving="imageMutations.bulkAttributeEditModal.isSaving"
    @close="imageMutations.closeBulkAttributeEditModal"
    @update-form="imageMutations.updateBulkAttributeEditForm"
    @save="handleSaveBulkAttributeEdit"
  />
  <BulkTagAddModal
    :show="imageMutations.bulkTagAddModal.show"
    :selected-count="selectedCount"
    :tags-text="imageMutations.bulkTagAddModal.tagsText"
    :is-saving="imageMutations.bulkTagAddModal.isSaving"
    @close="imageMutations.closeBulkTagAddModal"
    @update-tags-text="imageMutations.updateBulkTagAddText"
    @save="handleSaveBulkTagAdd"
  />
  <ImageRenameModal
    :show="renameModal.show"
    :item="renameModal.item"
    :filename="renameModal.filename"
    :is-saving="renameModal.isSaving"
    :error-message="renameModal.errorMessage"
    @close="closeRenameModal"
    @save="handleRenameImage"
    @update:filename="updateRenameFilename"
  />
  <MasterMaintenanceModal
    :show="masterMaintenance.masterMaintenanceModal.show"
    :mode="masterMaintenance.masterMaintenanceModal.mode"
    :active-tab="masterMaintenance.masterMaintenanceModal.activeTab"
    :keyword="masterMaintenance.masterMaintenanceModal.keyword"
    :items="masterMaintenance.masterMaintenanceModal.items"
    :total-count="masterMaintenance.masterMaintenanceModal.totalCount"
    :selected-item="masterMaintenance.masterMaintenanceModal.selectedItem"
    :replacement-name="masterMaintenance.masterMaintenanceModal.replacementName"
    :is-loading="masterMaintenance.masterMaintenanceModal.isLoading"
    :is-processing="masterMaintenance.masterMaintenanceModal.isProcessing"
    @close="masterMaintenance.closeMasterMaintenance"
    @change-tab="masterMaintenance.changeMasterMaintenanceTab"
    @update-keyword="masterMaintenance.updateMasterMaintenanceKeyword"
    @search="masterMaintenance.searchMasterMaintenanceItems"
    @select-item="masterMaintenance.selectMasterMaintenanceItem"
    @update-replacement-name="masterMaintenance.updateReplacementName"
    @delete-item="masterMaintenance.deleteMasterMaintenanceItem"
    @replace-item="masterMaintenance.replaceMasterMaintenanceItem"
    @delete-unused="masterMaintenance.deleteUnusedMasterItems"
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
