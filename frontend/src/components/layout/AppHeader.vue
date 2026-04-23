<script setup>
defineProps({
  appInfo: {
    type: Object,
    default: null,
  },
})
</script>

<template>
  <header class="navbar navbar-expand border-bottom bg-white app-header">
    <div class="container-fluid">
      <span class="navbar-brand mb-0 h1">{{ appInfo?.name ?? 'AZViewer' }}</span>
      <div class="d-flex align-items-center">
        <span class="text-secondary small d-none d-sm-inline">
          {{ appInfo?.version ? `v${appInfo.version}` : 'Vue + pywebview' }}
        </span>
      </div>
    </div>
  </header>
</template>
