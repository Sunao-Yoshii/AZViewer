<script setup>
defineProps({
  show: {
    type: Boolean,
    required: true,
  },
  items: {
    type: Array,
    default: () => [],
  },
  totalCount: {
    type: Number,
    default: 0,
  },
  limit: {
    type: Number,
    default: 256,
  },
  isLoading: {
    type: Boolean,
    default: false,
  },
  message: {
    type: String,
    default: '',
  },
})

defineEmits(['close', 'select'])
</script>

<template>
  <div v-if="show" class="modal-backdrop-shell" role="presentation">
    <div
      class="modal fade show d-block"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
    >
      <div class="modal-dialog modal-xl modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">重複タグ構成の検索</h5>
            <button
              type="button"
              class="btn-close"
              aria-label="閉じる"
              @click="$emit('close')"
            ></button>
          </div>

          <div class="modal-body">
            <div class="small text-muted mb-2">
              表示件数: {{ items.length }} / {{ totalCount }}
            </div>

            <div v-if="isLoading" class="text-muted">
              読み込み中...
            </div>

            <div v-else-if="message" class="alert alert-secondary mb-0">
              {{ message }}
            </div>

            <div v-else class="list-group duplicate-tag-set-list">
              <button
                v-for="item in items"
                :key="`${item.hash}:${item.tagSet}`"
                type="button"
                class="list-group-item list-group-item-action"
                @click="$emit('select', item)"
              >
                <div class="d-flex justify-content-between gap-3">
                  <span class="duplicate-tag-set-names">
                    {{ item.tagNames }}
                  </span>
                  <span class="badge text-bg-primary flex-shrink-0">
                    {{ item.imageCount }} 件
                  </span>
                </div>
              </button>
            </div>
          </div>

          <div class="modal-footer">
            <button
              type="button"
              class="btn btn-secondary btn-sm"
              @click="$emit('close')"
            >
              閉じる
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade show"></div>
  </div>
</template>
