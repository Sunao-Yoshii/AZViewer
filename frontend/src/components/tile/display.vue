<script setup>
defineProps({
  item: {
    type: Object,
    required: true,
  },
})

defineEmits(['edit', 'open-metadata'])

const ratingBadgeClass = (rating) => {
  switch (rating) {
    case 'General':
      return 'text-bg-success'
    case 'R-15':
      return 'text-bg-warning'
    case 'R-18':
    case 'R-18G':
      return 'text-bg-danger'
    default:
      return 'text-bg-secondary'
  }
}
</script>

<template>
  <div class="d-flex flex-wrap gap-1 mt-2">
    <span :class="['badge', ratingBadgeClass(item.rating)]">{{ item.rating }}</span>
    <span :class="item.is_checked === 1 ? 'badge bg-primary' : 'badge bg-secondary'">
      チェック
    </span>
    <span :class="item.is_favorite === 1 ? 'badge bg-warning text-dark' : 'badge bg-secondary'">
      お気に入り
    </span>
  </div>

  <div class="image-tile-comment small mt-2">{{ item.comment || '-' }}</div>

  <div
    v-if="item.tags?.length"
    class="mt-2 d-flex flex-wrap gap-1 tag_area"
    id="tag_area"
  >
    <span
      v-for="tag in item.tags"
      :key="tag"
      class="badge text-bg-secondary tag-badge tag-badge--tile"
      :title="tag"
    >
      {{ tag }}
    </span>
  </div>

  <div class="d-flex flex-wrap gap-2 mt-2">
    <button
      type="button"
      class="btn btn-outline-secondary btn-sm"
      @click="$emit('open-metadata')"
    >
      メタ情報
    </button>
    <button
      type="button"
      class="btn btn-outline-secondary btn-sm"
      @click="$emit('edit')"
    >
      Edit
    </button>
  </div>
</template>
