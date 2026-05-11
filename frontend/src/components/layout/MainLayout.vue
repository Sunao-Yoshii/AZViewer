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
  visibleCount: {
    type: Number,
    default: 0,
  },
  isAllVisibleSelected: {
    type: Boolean,
    default: false,
  },
})

defineEmits([
  'search',
  'import-complete',
  'import-prompt-tags',
  'toggle-visible-selection',
  'delete-selected-images',
  'move-selected-images',
  'open-bulk-attribute-edit',
  'open-wildcard-export',
  'open-duplicate-tag-sets',
  'selection-change',
  'change-page',
  'change-page-size',
  'change-sort',
  'open-detail',
  'request-delete',
  'save-detail',
])
</script>

<template>
  <div class="app-shell">
    <AppHeader
      :app-info="appInfo"
      :is-busy="isSearching"
      :selected-count="selectedCount"
      :visible-count="visibleCount"
      :is-all-visible-selected="isAllVisibleSelected"
      @import-prompt-tags="$emit('import-prompt-tags')"
      @toggle-visible-selection="$emit('toggle-visible-selection')"
      @delete-selected-images="$emit('delete-selected-images')"
      @move-selected-images="$emit('move-selected-images')"
      @open-bulk-attribute-edit="$emit('open-bulk-attribute-edit')"
      @open-wildcard-export="$emit('open-wildcard-export')"
      @open-duplicate-tag-sets="$emit('open-duplicate-tag-sets')"
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
