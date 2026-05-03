<script setup>
defineProps({
  appInfo: {
    type: Object,
    required: true,
  },
  isBusy: {
    type: Boolean,
    default: false,
  },
})

defineEmits([
  'import-prompt-tags',
])
</script>

<template>
  <header class="navbar navbar-expand border-bottom bg-white app-header">
    <div class="container-fluid">
      <span class="navbar-brand mb-0 h1">{{ appInfo?.name ?? 'AZViewer' }}</span>
      <div class="d-flex align-items-center gap-3">
        <button
          type="button"
          class="btn btn-outline-primary btn-sm"
          :disabled="isBusy"
          @click="$emit('import-prompt-tags')"
        >
          プロンプトの読み取り
        </button>
        <span class="text-secondary small d-none d-sm-inline">
          {{ appInfo?.version ? `v${appInfo.version}` : 'Vue + pywebview' }}
        </span>
      </div>
    </div>
  </header>
</template>
