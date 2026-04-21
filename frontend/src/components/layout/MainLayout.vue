<script setup>
import AppFooter from './AppFooter.vue'
import AppHeader from './AppHeader.vue'
import AppSidebar from './AppSidebar.vue'

defineProps({
  appInfo: {
    type: Object,
    default: null,
  },
  menus: {
    type: Array,
    required: true,
  },
  activePageKey: {
    type: String,
    required: true,
  },
  status: {
    type: Object,
    required: true,
  },
})

defineEmits(['change-page', 'health-check'])
</script>

<template>
  <div class="app-shell">
    <AppHeader :app-info="appInfo" @health-check="$emit('health-check')" />

    <div class="app-body d-flex">
      <AppSidebar
        :menus="menus"
        :active-page-key="activePageKey"
        @change-page="$emit('change-page', $event)"
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

