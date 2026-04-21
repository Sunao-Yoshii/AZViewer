<script setup>
defineProps({
  appInfo: {
    type: Object,
    default: null,
  },
})

defineEmits(['health-check'])
</script>

<template>
  <header class="navbar navbar-expand border-bottom bg-white app-header">
    <div class="container-fluid">
      <span class="navbar-brand mb-0 h1">{{ appInfo?.name ?? 'AZViewer' }}</span>
      <div class="d-flex align-items-center gap-3">
        <span class="text-secondary small d-none d-sm-inline">
          {{ appInfo?.version ? `v${appInfo.version}` : 'Vue + pywebview' }}
        </span>
        <button class="btn btn-outline-primary btn-sm" type="button" @click="$emit('health-check')">
          <i class="bi bi-activity me-1" aria-hidden="true"></i>
          Check
        </button>
      </div>
    </div>
  </header>
</template>

