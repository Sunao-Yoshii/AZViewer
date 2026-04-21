<script setup>
defineProps({
  status: {
    type: Object,
    required: true,
  },
})
</script>

<template>
  <footer class="border-top bg-white app-footer">
    <div class="container-fluid d-flex align-items-center justify-content-between gap-3">
      <span class="small text-secondary">AZViewer Foundation</span>
      <span class="badge text-bg-light border">
        <span :class="`status-dot bg-${status.type}`" aria-hidden="true"></span>
        {{ status.message }}
      </span>
    </div>
  </footer>
</template>

