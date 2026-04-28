<script setup>
import Pagination from '../common/pagination.vue'
import Tile from '../tile/tile.vue'

defineProps({
  searchResult: {
    type: Object,
    required: true,
  },
  isSearching: {
    type: Boolean,
    default: false,
  },
})

defineEmits([
  'change-page',
  'change-page-size',
  'change-sort',
  'open-detail',
  'request-delete',
  'save-detail',
])

const sortOptions = [
  { label: '登録の新しい順', value: 'id_desc' },
  { label: '登録の古い順', value: 'id_asc' },
  { label: 'ファイル名昇順', value: 'filename_asc' },
  { label: 'ファイル名降順', value: 'filename_desc' },
  { label: 'レーティング昇順', value: 'rating_asc' },
  { label: 'レーティング降順', value: 'rating_desc' },
]
const pageSizeOptions = [25, 50, 75, 100]
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

    <div v-if="(searchResult.total_count ?? 0) === 0" class="card">
      <div class="card-body py-5 text-center text-secondary">一致するデータがありません</div>
    </div>

    <div v-else class="image-grid">
      <Tile
        v-for="item in searchResult.items"
        :key="item.id"
        :item="item"
        :is-searching="isSearching"
        @open-detail="$emit('open-detail', $event)"
        @request-delete="$emit('request-delete', $event)"
        @save-detail="$emit('save-detail', $event)"
      />
    </div>

    <div v-if="(searchResult.total_pages ?? 0) > 1" class="d-flex justify-content-between align-items-center">
      <div class="small text-secondary">
        {{ searchResult.page }} / {{ searchResult.total_pages }} ページ
      </div>
    </div>

    <Pagination
      :search-result="searchResult"
      :is-searching="isSearching"
      @change-page="$emit('change-page', $event)"
    />
  </section>
</template>
