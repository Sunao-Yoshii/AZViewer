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
})

defineEmits(['search', 'health-check', 'import-complete'])
</script>

<template>
  <div class="app-shell">
    <AppHeader :app-info="appInfo" @health-check="$emit('health-check')" />

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
