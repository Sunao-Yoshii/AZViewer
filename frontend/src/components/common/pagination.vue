<script setup>
import { computed } from 'vue'

const props = defineProps({
  searchResult: {
    type: Object,
    required: true,
  },
  isSearching: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['change-page'])

const visiblePages = computed(() => {
  const totalPages = props.searchResult.total_pages ?? 0
  const currentPage = props.searchResult.page ?? 1
  if (totalPages < 2) {
    return []
  }
  if (totalPages < 5) {
    return Array.from({ length: totalPages }, (_, index) => index + 1)
  }
  const start = Math.max(1, currentPage - 2)
  const end = Math.min(totalPages, currentPage + 2)
  return Array.from({ length: end - start + 1 }, (_, index) => start + index)
})
</script>

<template>
  <div v-if="(searchResult.total_pages ?? 0) > 1" class="d-flex justify-content-center">
    <div class="btn-group btn-group-sm">
      <button
        v-for="page in visiblePages"
        :key="`bottom-${page}`"
        type="button"
        class="btn"
        :class="page === searchResult.page ? 'btn-primary' : 'btn-outline-primary'"
        :disabled="isSearching"
        @click="$emit('change-page', page)"
      >
        {{ page }}
      </button>
    </div>
  </div>
</template>
