<script setup>
import { computed, ref, watch } from 'vue'
import placeholderUrl from '../assets/images/placeholder.svg'
import { fetchLocalImageThumb } from '../services/backendApi'

const props = defineProps({
  searchResult: {
    type: Object,
    required: true,
  },
  isSearching: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['change-page', 'change-page-size', 'change-sort', 'update-flag'])

const thumbnailMap = ref({})
const sortOptions = [
  { label: '登録の新しい順', value: 'id_desc' },
  { label: '登録の古い順', value: 'id_asc' },
  { label: 'ファイル名昇順', value: 'filename_asc' },
  { label: 'ファイル名降順', value: 'filename_desc' },
  { label: 'レーティング昇順', value: 'rating_asc' },
  { label: 'レーティング降順', value: 'rating_desc' },
]
const pageSizeOptions = [25, 50, 75, 100]

const visiblePages = computed(() => {
  const totalPages = props.searchResult.total_pages ?? 0
  const currentPage = props.searchResult.page ?? 1
  if (totalPages < 2) {
    return []
  }
  if (totalPages < 5) {
    return Array.from({ length: totalPages }, (_, index) => index + 1)
  }
  const start = Math.max(1, currentPage - 2)
  const end = Math.min(totalPages, currentPage + 2)
  return Array.from({ length: end - start + 1 }, (_, index) => start + index)
})

watch(
  () => props.searchResult.items,
  (items) => {
    if (!Array.isArray(items)) {
      return
    }
    for (const item of items) {
      if (thumbnailMap.value[item.id]) {
        continue
      }
      thumbnailMap.value[item.id] = placeholderUrl
      loadThumbnail(item.id)
    }
  },
  { immediate: true }
)

async function loadThumbnail(id) {
  const result = await fetchLocalImageThumb(id)
  if (!result.success) {
    thumbnailMap.value = { ...thumbnailMap.value, [id]: placeholderUrl }
    return
  }
  thumbnailMap.value = {
    ...thumbnailMap.value,
    [id]: result.data?.dataUrl || placeholderUrl,
  }
}

function toggleFlag(item, field, event) {
  emit('update-flag', {
    id: item.id,
    field,
    value: event.target.checked ? 1 : 0,
  })
}
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
          <option v-for="size in pageSizeOptions" :key="size" :value="size">{{ size }}</option>
        </select>

        <span class="small text-secondary">{{ searchResult.total_count ?? 0 }} 件</span>
      </div>
    </div>

    <div v-if="(searchResult.total_pages ?? 0) > 1" class="d-flex justify-content-between align-items-center">
      <div class="small text-secondary">
        {{ searchResult.page }} / {{ searchResult.total_pages }} ページ
      </div>
      <div class="btn-group btn-group-sm">
        <button
          v-for="page in visiblePages"
          :key="`top-${page}`"
          type="button"
          class="btn"
          :class="page === searchResult.page ? 'btn-primary' : 'btn-outline-primary'"
          :disabled="isSearching"
          @click="$emit('change-page', page)"
        >
          {{ page }}
        </button>
      </div>
    </div>

    <div v-if="(searchResult.total_count ?? 0) === 0" class="card">
      <div class="card-body py-5 text-center text-secondary">一致するデータがありません</div>
    </div>

    <div v-else class="image-grid">
      <article
        v-for="item in searchResult.items"
        :key="item.id"
        class="card image-tile"
      >
        <img
          class="image-tile-thumb"
          :src="thumbnailMap[item.id] || placeholderUrl"
          :alt="item.filename"
        />
        <div class="card-body image-tile-body">
          <div class="small fw-semibold text-truncate" :title="item.filename">{{ item.filename }}</div>
          <div class="image-tile-folder small text-secondary text-truncate" :title="item.folder">
            {{ item.folder }}
          </div>
          <div class="d-flex justify-content-between align-items-center gap-2 mt-2">
            <span class="badge text-bg-secondary">{{ item.rating }}</span>
            <span class="small text-secondary">#{{ item.id }}</span>
          </div>

          <div class="form-check form-switch mt-3">
            <input
              :id="`checked-${item.id}`"
              class="form-check-input"
              type="checkbox"
              :checked="item.is_checked === 1"
              :disabled="isSearching"
              @change="toggleFlag(item, 'is_checked', $event)"
            />
            <label class="form-check-label small" :for="`checked-${item.id}`">確認済み</label>
          </div>

          <div class="form-check form-switch">
            <input
              :id="`favorite-${item.id}`"
              class="form-check-input"
              type="checkbox"
              :checked="item.is_favorite === 1"
              :disabled="isSearching"
              @change="toggleFlag(item, 'is_favorite', $event)"
            />
            <label class="form-check-label small" :for="`favorite-${item.id}`">お気に入り</label>
          </div>

          <div class="image-tile-comment small mt-2">{{ item.comment || '-' }}</div>
        </div>
      </article>
    </div>

    <div v-if="(searchResult.total_pages ?? 0) > 1" class="d-flex justify-content-center">
      <div class="btn-group btn-group-sm">
        <button
          v-for="page in visiblePages"
          :key="`bottom-${page}`"
          type="button"
          class="btn"
          :class="page === searchResult.page ? 'btn-primary' : 'btn-outline-primary'"
          :disabled="isSearching"
          @click="$emit('change-page', page)"
        >
          {{ page }}
        </button>
      </div>
    </div>
  </section>
</template>
