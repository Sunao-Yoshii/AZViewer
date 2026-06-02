<script setup>
import { computed } from 'vue'

const props = defineProps({
  page: {
    type: Number,
    default: 1,
  },
  totalPages: {
    type: Number,
    default: 1,
  },
  isBusy: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['change-page'])

const currentPage = computed(() => Math.max(1, Number(props.page || 1)))
const normalizedTotalPages = computed(() => Math.max(0, Number(props.totalPages || 0)))

const displayedPages = computed(() => {
  const total = normalizedTotalPages.value
  const current = Math.min(currentPage.value, total)

  if (total <= 1) {
    return []
  }

  if (total <= 7) {
    return Array.from({ length: total }, (_, index) => index + 1)
  }

  const pages = new Set([1, total])
  for (let page = current - 2; page <= current + 2; page += 1) {
    if (page >= 1 && page <= total) {
      pages.add(page)
    }
  }

  const sortedPages = [...pages].sort((a, b) => a - b)
  const result = []

  for (let index = 0; index < sortedPages.length; index += 1) {
    const page = sortedPages[index]
    const previous = sortedPages[index - 1]
    if (previous && page - previous > 1) {
      result.push(`ellipsis-${previous}-${page}`)
    }
    result.push(page)
  }

  return result
})
</script>

<template>
  <nav
    v-if="normalizedTotalPages > 1"
    class="pagination-nav"
    aria-label="画像一覧ページング"
  >
    <div class="btn-group btn-group-sm">
      <button
        type="button"
        class="btn btn-outline-secondary"
        :disabled="isBusy || currentPage <= 1"
        @click="$emit('change-page', 1)"
      >
        最初
      </button>

      <button
        type="button"
        class="btn btn-outline-secondary"
        :disabled="isBusy || currentPage <= 1"
        @click="$emit('change-page', currentPage - 1)"
      >
        前へ
      </button>

      <template v-for="item in displayedPages" :key="item">
        <button
          v-if="typeof item === 'number'"
          type="button"
          class="btn"
          :class="item === currentPage ? 'btn-primary' : 'btn-outline-secondary'"
          :disabled="isBusy || item === currentPage"
          @click="$emit('change-page', item)"
        >
          {{ item }}
        </button>

        <button
          v-else
          type="button"
          class="btn btn-outline-secondary"
          disabled
        >
          ...
        </button>
      </template>

      <button
        type="button"
        class="btn btn-outline-secondary"
        :disabled="isBusy || currentPage >= normalizedTotalPages"
        @click="$emit('change-page', currentPage + 1)"
      >
        次へ
      </button>

      <button
        type="button"
        class="btn btn-outline-secondary"
        :disabled="isBusy || currentPage >= normalizedTotalPages"
        @click="$emit('change-page', normalizedTotalPages)"
      >
        最後
      </button>
    </div>
  </nav>
</template>
