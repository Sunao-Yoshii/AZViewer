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
})

defineEmits([
  'search',
  'import-complete',
  'import-prompt-tags',
  'delete-selected-images',
  'move-selected-images',
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
      @import-prompt-tags="$emit('import-prompt-tags')"
      @delete-selected-images="$emit('delete-selected-images')"
      @move-selected-images="$emit('move-selected-images')"
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
