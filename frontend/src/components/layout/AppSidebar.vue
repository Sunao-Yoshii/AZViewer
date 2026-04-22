<script setup>
import FileSelectArea from '../upload/FileSelectArea.vue'

defineProps({
  menus: {
    type: Array,
    required: true,
  },
  activePageKey: {
    type: String,
    required: true,
  },
})

defineEmits(['change-page'])
</script>

<template>
  <aside class="app-sidebar border-end bg-light">
    <div class="app-sidebar-upload p-3 border-bottom">
      <FileSelectArea />
    </div>

    <nav class="app-sidebar-menu nav nav-pills flex-column gap-1 p-3">
      <button
        v-for="menu in menus"
        :key="menu.key"
        type="button"
        class="nav-link text-start"
        :class="{ active: activePageKey === menu.key }"
        @click="$emit('change-page', menu.key)"
      >
        <span class="d-block fw-semibold">{{ menu.label }}</span>
        <span class="d-block small opacity-75">{{ menu.description }}</span>
      </button>
    </nav>
  </aside>
</template>
