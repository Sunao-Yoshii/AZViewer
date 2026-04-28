<script setup>
import placeholderUrl from '../../assets/images/placeholder.svg'

defineProps({
  item: {
    type: Object,
    required: true,
  },
  isSearching: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['open-detail', 'request-delete'])
</script>

<template>
  <article class="card image-tile">
    <button
      type="button"
      class="btn-close image-tile-delete"
      aria-label="削除"
      :disabled="isSearching"
      @click.stop="$emit('request-delete', item.id)"
    ></button>
    <img
      class="image-tile-thumb"
      :src="item.thumbnailUrl || placeholderUrl"
      :alt="item.filename"
      role="button"
      @click="$emit('open-detail', item)"
    />
    <div class="card-body image-tile-body">
      <div class="small fw-semibold text-truncate" :title="item.filename">{{ item.filename }}</div>
      <div class="image-tile-folder small text-secondary text-truncate" :title="item.folder">
        {{ item.folder }}
      </div>
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
    </div>
  </article>
</template>
