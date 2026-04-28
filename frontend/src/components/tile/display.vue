<script setup>
defineProps({
  item: {
    type: Object,
    required: true,
  },
})

defineEmits(['edit'])
</script>

<template>
  <div class="d-flex flex-wrap gap-1 mt-2">
    <span class="badge text-bg-secondary">{{ item.rating }}</span>
    <span :class="item.is_checked === 1 ? 'badge bg-primary' : 'badge bg-secondary'">
      チェック
    </span>
    <span :class="item.is_favorite === 1 ? 'badge bg-warning text-dark' : 'badge bg-secondary'">
      お気に入り
    </span>
  </div>

  <div class="image-tile-comment small mt-2">{{ item.comment || '-' }}</div>

  <button
    type="button"
    class="btn btn-outline-secondary btn-sm mt-2"
    @click="$emit('edit')"
  >
    Edit
  </button>
</template>
