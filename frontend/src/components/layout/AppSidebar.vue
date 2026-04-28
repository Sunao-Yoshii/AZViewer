<script setup>
import FileSelectArea from '../upload/FileSelectArea.vue'

defineProps({
  filters: {
    type: Object,
    required: true,
  },
  isBusy: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['search', 'import-complete'])

const ratingOptions = [
  { label: 'すべて', value: '' },
  { label: 'General', value: 'General' },
  { label: 'R-15', value: 'R-15' },
  { label: 'R-18', value: 'R-18' },
  { label: 'R-18G', value: 'R-18G' },
]
</script>

<template>
  <aside class="app-sidebar border-end bg-light">
    <div class="app-sidebar-upload p-3 border-bottom">
      <FileSelectArea @import-complete="$emit('import-complete', $event)" />
    </div>

    <section class="app-sidebar-menu p-3">
      <div class="d-flex align-items-center justify-content-between mb-3">
        <h2 class="h6 mb-0">検索条件</h2>
        <span class="badge text-bg-light border">image_file_data</span>
      </div>

      <div class="vstack gap-3">
        <div>
          <label class="form-label small fw-semibold" for="searchPath">Path</label>
          <input
            id="searchPath"
            v-model="filters.path"
            class="form-control form-control-sm"
            type="text"
            placeholder="部分一致"
            :disabled="isBusy"
          />
        </div>

        <div>
          <label class="form-label small fw-semibold" for="searchRating">Rating</label>
          <select
            id="searchRating"
            v-model="filters.rating"
            class="form-select form-select-sm"
            :disabled="isBusy"
          >
            <option v-for="option in ratingOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </div>

        <div class="form-check">
          <input
            id="searchChecked"
            v-model="filters.is_checked"
            class="form-check-input"
            type="checkbox"
            :disabled="isBusy"
          />
          <label class="form-check-label small" for="searchChecked">チェック済みのみ</label>
        </div>

        <div class="form-check">
          <input
            id="searchFavorite"
            v-model="filters.is_favorite"
            class="form-check-input"
            type="checkbox"
            :disabled="isBusy"
          />
          <label class="form-check-label small" for="searchFavorite">お気に入りのみ</label>
        </div>

        <button
          type="button"
          class="btn btn-primary btn-sm w-100"
          :disabled="isBusy"
          @click="emit('search')"
        >
          <i class="bi bi-search me-1" aria-hidden="true"></i>
          検索
        </button>
      </div>
    </section>
  </aside>
</template>
