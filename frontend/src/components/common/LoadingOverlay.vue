<script setup>
defineProps({
  show: {
    type: Boolean,
    required: true,
  },
  title: {
    type: String,
    default: '',
  },
  message: {
    type: String,
    default: '',
  },
})
</script>

<template>
  <div v-if="show" class="startup-overlay" role="alert" aria-live="assertive" aria-busy="true">
    <div class="startup-overlay-card shadow">
      <div class="startup-overlay-spinner" aria-hidden="true"></div>
      <p v-if="title" class="startup-overlay-title mb-2">{{ title }}</p>
      <p class="startup-overlay-message mb-0">{{ message }}</p>
    </div>
  </div>
</template>
