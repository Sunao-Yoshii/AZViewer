<script setup>
import SearchForm from '../form/search_form.vue'
import FileSelectArea from '../upload/FileSelectArea.vue'

defineProps({
  filters: {
    type: Object,
    required: true,
  },
  isBusy: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['search', 'import-complete'])
</script>

<template>
  <aside class="app-sidebar border-end bg-light">
    <div class="app-sidebar-upload p-3 border-bottom">
      <FileSelectArea @import-complete="$emit('import-complete', $event)" />
    </div>

    <section class="app-sidebar-menu p-3">
      <div class="d-flex align-items-center justify-content-between mb-3">
        <h2 class="h6 mb-0">検索条件</h2>
        <span class="badge text-bg-light border">image_file_data</span>
      </div>

      <SearchForm :filters="filters" :is-busy="isBusy" @search="emit('search')" />
    </section>
  </aside>
</template>
