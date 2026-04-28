<script setup>
/**
 * image_file_data レコードを受け取り、サムネイルと基本情報をカード形式で表示するコンポーネント
 * - サムネイルは fetchLocalImageThumb API を呼び出して取得する
 * - 確認済み・お気に入りのフラグはスイッチで切り替え可能で、切り替え時に update-flag イベントを発火する
 * - 画像のタイトルはファイル名、サブタイトルはフォルダパスとする
 * - 画像のIDとレーティングも表示する
 */

import { ref, watch } from 'vue'
import placeholderUrl from '../../assets/images/placeholder.svg'
import { fetchLocalImageThumb } from '../../services/backendApi'

const props = defineProps({
  item: {
    type: Object,
    required: true,
  },
  isSearching: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update-flag'])

const thumbnailUrl = ref(placeholderUrl)

watch(
  () => props.item.id,
  (id) => {
    thumbnailUrl.value = placeholderUrl
    loadThumbnail(id)
  },
  { immediate: true }
)

async function loadThumbnail(id) {
  const result = await fetchLocalImageThumb(id)
  if (!result.success) {
    thumbnailUrl.value = placeholderUrl
    return
  }
  thumbnailUrl.value = result.data?.dataUrl || placeholderUrl
}

function toggleFlag(field, event) {
  emit('update-flag', {
    id: props.item.id,
    field,
    value: event.target.checked ? 1 : 0,
  })
}
</script>

<template>
  <article class="card image-tile">
    <img
      class="image-tile-thumb"
      :src="thumbnailUrl"
      :alt="item.filename"
    />
    <div class="card-body image-tile-body">
      <div class="small fw-semibold text-truncate" :title="item.filename">{{ item.filename }}</div>
      <div class="image-tile-folder small text-secondary text-truncate" :title="item.folder">
        {{ item.folder }}
      </div>
      <div class="d-flex justify-content-between align-items-center gap-2 mt-2">
        <span class="badge text-bg-secondary">{{ item.rating }}</span>
        <span class="small text-secondary">#{{ item.id }}</span>
      </div>

      <div class="form-check form-switch mt-3">
        <input
          :id="`checked-${item.id}`"
          class="form-check-input"
          type="checkbox"
          :checked="item.is_checked === 1"
          :disabled="isSearching"
          @change="toggleFlag('is_checked', $event)"
        />
        <label class="form-check-label small" :for="`checked-${item.id}`">チェック</label>
      </div>

      <div class="form-check form-switch">
        <input
          :id="`favorite-${item.id}`"
          class="form-check-input"
          type="checkbox"
          :checked="item.is_favorite === 1"
          :disabled="isSearching"
          @change="toggleFlag('is_favorite', $event)"
        />
        <label class="form-check-label small" :for="`favorite-${item.id}`">お気に入り</label>
      </div>

      <div class="image-tile-comment small mt-2">{{ item.comment || '-' }}</div>
    </div>
  </article>
</template>
