import { computed, reactive } from 'vue'
import {
  fetchLocalImage,
  openContainingFolder,
} from '../services/backendApi'

export function useImageDetail({ pushToast }) {
  const detailModal = reactive({
    show: false,
    item: null,
    imageSrc: '',
    items: [],
    currentIndex: -1,
    isLoading: false,
  })

  const selectedItem = computed(() => detailModal.item)
  const detailImageUrl = computed(() => detailModal.imageSrc)
  const isLoadingImage = computed(() => detailModal.isLoading)
  const hasPrevious = computed(() => detailModal.currentIndex > 0)
  const hasNext = computed(() =>
    detailModal.currentIndex >= 0 &&
    detailModal.currentIndex < detailModal.items.length - 1
  )

  async function loadDetailImage(item) {
    if (!item) {
      detailModal.imageSrc = ''
      detailModal.isLoading = false
      return
    }

    detailModal.imageSrc = ''
    detailModal.isLoading = true
    const result = await fetchLocalImage(item.path)
    detailModal.isLoading = false
    if (!result.success) {
      pushToast({ type: 'error', message: result.message || '画像を読み込めませんでした。' })
      return
    }
    detailModal.imageSrc = result.data?.dataUrl ?? ''
  }

  async function openDetail({ item, items }) {
    detailModal.show = true
    detailModal.items = [...(items ?? [])]
    detailModal.currentIndex = detailModal.items.findIndex((entry) => entry.id === item.id)
    detailModal.item = item
    await loadDetailImage(item)
  }

  async function handleOpenDetail(item) {
    await openDetail({ item, items: [item] })
  }

  function closeDetail() {
    detailModal.show = false
    detailModal.item = null
    detailModal.imageSrc = ''
    detailModal.items = []
    detailModal.currentIndex = -1
    detailModal.isLoading = false
  }

  function handleCloseDetail() {
    closeDetail()
  }

  async function movePrevious() {
    if (!hasPrevious.value) {
      return
    }

    await showDetailItemAtIndex(detailModal.currentIndex - 1)
  }

  async function moveNext() {
    if (!hasNext.value) {
      return
    }

    await showDetailItemAtIndex(detailModal.currentIndex + 1)
  }

  async function showDetailItemAtIndex(index) {
    const nextItem = detailModal.items[index]
    if (!nextItem) {
      return
    }

    detailModal.currentIndex = index
    detailModal.item = nextItem
    await loadDetailImage(nextItem)
  }

  function refreshDetailItemsAfterSearch(items, preferredId = null, fallbackId = null) {
    const nextItems = [...(items ?? [])]
    detailModal.items = nextItems

    let nextIndex = -1
    if (preferredId != null) {
      nextIndex = nextItems.findIndex((item) => item.id === preferredId)
    }
    if (nextIndex < 0 && fallbackId != null) {
      nextIndex = nextItems.findIndex((item) => item.id === fallbackId)
    }
    if (nextIndex < 0) {
      closeDetail()
      return null
    }

    detailModal.currentIndex = nextIndex
    detailModal.item = nextItems[nextIndex]
    return nextItems[nextIndex]
  }

  async function handleOpenContainingFolder(path) {
    const result = await openContainingFolder(path)
    if (!result.success) {
      pushToast({ type: 'error', message: result.message || 'フォルダを開けませんでした。' })
    }
  }

  return {
    detailModal,
    selectedItem,
    detailImageUrl,
    hasNext,
    hasPrevious,
    isLoadingImage,
    closeDetail,
    handleOpenDetail,
    handleCloseDetail,
    handleOpenContainingFolder,
    loadDetailImage,
    moveNext,
    movePrevious,
    openDetail,
    refreshDetailItemsAfterSearch,
  }
}
