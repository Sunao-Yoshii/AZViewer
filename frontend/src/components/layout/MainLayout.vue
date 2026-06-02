<script setup>
import AppFooter from './AppFooter.vue'
import AppHeader from './AppHeader.vue'
import AppSidebar from './AppSidebar.vue'

defineProps({
  appInfo: {
    type: Object,
    default: null,
  },
  filters: {
    type: Object,
    required: true,
  },
  status: {
    type: Object,
    required: true,
  },
  isSearching: {
    type: Boolean,
    default: false,
  },
  selectedCount: {
    type: Number,
    default: 0,
  },
  selectedImageIds: {
    type: Array,
    default: () => [],
  },
  currentPageCount: {
    type: Number,
    default: 0,
  },
  isAllCurrentPageSelected: {
    type: Boolean,
    default: false,
  },
})

defineEmits([
  'search',
  'import-complete',
  'import-prompt-tags',
  'import-caption-tags',
  'toggle-current-page-selection',
  'export-selected-tags',
  'move-selected-images',
  'move-selected-images-to-trash',
  'remove-selected-images-from-catalog',
  'open-bulk-attribute-edit',
  'open-bulk-tag-add',
  'open-wildcard-export',
  'open-duplicate-tag-sets',
  'open-master-maintenance',
  'selection-change',
  'change-page',
  'change-page-size',
  'change-sort',
  'open-detail',
  'save-detail',
])
</script>

<template>
  <div class="app-shell">
    <AppHeader
      :app-info="appInfo"
      :is-busy="isSearching"
      :selected-count="selectedCount"
      :current-page-count="currentPageCount"
      :is-all-current-page-selected="isAllCurrentPageSelected"
      @import-prompt-tags="$emit('import-prompt-tags')"
      @import-caption-tags="$emit('import-caption-tags')"
      @toggle-current-page-selection="$emit('toggle-current-page-selection')"
      @export-selected-tags="$emit('export-selected-tags')"
      @move-selected-images="$emit('move-selected-images')"
      @move-selected-images-to-trash="$emit('move-selected-images-to-trash')"
      @remove-selected-images-from-catalog="$emit('remove-selected-images-from-catalog')"
      @open-bulk-attribute-edit="$emit('open-bulk-attribute-edit')"
      @open-bulk-tag-add="$emit('open-bulk-tag-add')"
      @open-wildcard-export="$emit('open-wildcard-export')"
      @open-duplicate-tag-sets="$emit('open-duplicate-tag-sets')"
      @open-master-maintenance="$emit('open-master-maintenance', $event)"
    />

    <div class="app-body d-flex">
      <AppSidebar
        :filters="filters"
        :is-busy="isSearching"
        @search="$emit('search')"
        @import-complete="$emit('import-complete', $event)"
      />

      <main class="app-main flex-grow-1 overflow-auto">
        <div class="container-fluid py-4">
          <slot />
        </div>
      </main>
    </div>

    <AppFooter :status="status" />
  </div>
</template>
