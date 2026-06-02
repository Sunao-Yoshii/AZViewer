<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { LARGE_PAGE_SIZE_THRESHOLD, PAGE_SIZE_OPTIONS } from '../../composables/useImageSearch'
import Pagination from '../common/pagination.vue'
import Tile from '../tile/tile.vue'

const props = defineProps({
  searchResult: {
    type: Object,
    required: true,
  },
  isSearching: {
    type: Boolean,
    default: false,
  },
  selectedImageIds: {
    type: Array,
    default: () => [],
  },
  editingImageId: {
    type: Number,
    default: null,
  },
})

defineEmits([
  'change-page',
  'change-page-size',
  'change-sort',
  'edit-finished',
  'open-detail',
  'save-detail',
  'selection-change',
])

const sortOptions = [
  { label: '登録の新しい順', value: 'id_desc' },
  { label: '登録の古い順', value: 'id_asc' },
  { label: 'ファイル名昇順', value: 'filename_asc' },
  { label: 'ファイル名降順', value: 'filename_desc' },
  { label: 'レーティング昇順', value: 'rating_asc' },
  { label: 'レーティング降順', value: 'rating_desc' },
]
const standardPageSizeOptions = PAGE_SIZE_OPTIONS.filter((size) => size < LARGE_PAGE_SIZE_THRESHOLD)
const largePageSizeOptions = PAGE_SIZE_OPTIONS.filter((size) => size >= LARGE_PAGE_SIZE_THRESHOLD)
const CHUNK_RENDER_THRESHOLD = 500
const CHUNK_RENDER_BATCH_SIZE = 50

const renderedItems = ref([])
const isChunkRendering = ref(false)
const renderedCount = computed(() => renderedItems.value.length)
const totalRenderCount = computed(() => props.searchResult.items?.length ?? 0)

let renderToken = 0

function shouldChunkRender(items) {
  return (items?.length ?? 0) >= CHUNK_RENDER_THRESHOLD
}

function waitForNextFrame() {
  return new Promise((resolve) => window.requestAnimationFrame(resolve))
}

async function startRenderItems(items) {
  const token = ++renderToken
  renderedItems.value = []

  if (!shouldChunkRender(items)) {
    renderedItems.value = [...items]
    isChunkRendering.value = false
    return
  }

  isChunkRendering.value = true

  for (let index = 0; index < items.length; index += CHUNK_RENDER_BATCH_SIZE) {
    if (token !== renderToken) {
      return
    }

    renderedItems.value = [
      ...renderedItems.value,
      ...items.slice(index, index + CHUNK_RENDER_BATCH_SIZE),
    ]

    await waitForNextFrame()
  }

  if (token === renderToken) {
    isChunkRendering.value = false
  }
}

watch(
  () => props.searchResult.items,
  (items) => {
    startRenderItems(items ?? [])
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  renderToken += 1
})
</script>

<template>
  <section class="vstack gap-4">
    <div class="d-flex flex-column flex-lg-row justify-content-between gap-3 align-items-lg-center">
      <div>
        <h1 class="h3 mb-2">画像一覧</h1>
        <p class="text-secondary mb-0">登録済み画像を検索条件に応じて表示します。</p>
      </div>

      <div class="d-flex flex-wrap gap-2 align-items-center">
        <label class="small text-secondary" for="sortSelect">並び順</label>
        <select
          id="sortSelect"
          class="form-select form-select-sm home-control"
          :value="searchResult.sort"
          :disabled="isSearching"
          @change="$emit('change-sort', $event.target.value)"
        >
          <option v-for="option in sortOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>

        <label class="small text-secondary" for="pageSizeSelect">件数</label>
        <select
          id="pageSizeSelect"
          class="form-select form-select-sm home-control"
          :value="searchResult.page_size"
          :disabled="isSearching"
          @change="$emit('change-page-size', Number($event.target.value))"
        >
          <optgroup label="通常表示">
            <option v-for="size in standardPageSizeOptions" :key="size" :value="size">{{ size }}</option>
          </optgroup>
          <optgroup label="大量表示">
            <option v-for="size in largePageSizeOptions" :key="size" :value="size">{{ size }}</option>
          </optgroup>
        </select>

        <span class="small text-secondary">{{ searchResult.total_count ?? 0 }} 件</span>
      </div>
    </div>

    <div
      v-if="(searchResult.page_size ?? 25) >= LARGE_PAGE_SIZE_THRESHOLD"
      class="alert alert-warning py-2 mb-0 image-page-size-warning"
    >
      大量表示では、画像数や端末性能によって表示や操作が重くなる場合があります。
    </div>

    <div v-if="isChunkRendering" class="alert alert-info py-2 mb-0 image-chunk-rendering-message">
      画像タイルを段階的に表示しています。
      {{ renderedCount }} / {{ totalRenderCount }} 件
    </div>

    <div v-if="(searchResult.total_count ?? 0) === 0" class="card">
      <div class="card-body py-5 text-center text-secondary">一致するデータがありません</div>
    </div>

    <template v-else>
      <Pagination
        :page="searchResult.page"
        :total-pages="searchResult.total_pages"
        :is-busy="isSearching"
        @change-page="$emit('change-page', $event)"
      />

      <div class="image-grid">
        <Tile
          v-for="item in renderedItems"
          :key="item.id"
          :item="item"
          :is-searching="isSearching"
          :selected="selectedImageIds.includes(item.id)"
          :editing-image-id="editingImageId"
          @edit-finished="$emit('edit-finished', $event)"
          @open-detail="$emit('open-detail', $event)"
          @save-detail="$emit('save-detail', $event)"
          @selection-change="$emit('selection-change', $event)"
        />
      </div>
    </template>

    <div v-if="(searchResult.total_pages ?? 0) > 1" class="d-flex justify-content-between align-items-center">
      <div class="small text-secondary">
        {{ searchResult.page }} / {{ searchResult.total_pages }} ページ
      </div>
    </div>

    <Pagination
      :page="searchResult.page"
      :total-pages="searchResult.total_pages"
      :is-busy="isSearching"
      @change-page="$emit('change-page', $event)"
    />
  </section>
</template>
