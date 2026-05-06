<script setup>
defineProps({
  show: {
    type: Boolean,
    required: true,
  },
  exportMode: {
    type: String,
    default: 'create',
    validator: (value) => ['create', 'append'].includes(value),
  },
  tagItems: {
    type: Array,
    default: () => [],
  },
  previewText: {
    type: String,
    default: '',
  },
  selectedCount: {
    type: Number,
    default: 0,
  },
  outputLineCount: {
    type: Number,
    default: 0,
  },
  isSaving: {
    type: Boolean,
    default: false,
  },
})

defineEmits([
  'close',
  'change-mode',
  'toggle-tag',
  'save',
])
</script>

<template>
  <div v-if="show" class="modal-backdrop-shell" role="presentation">
    <div
      class="modal fade show d-block"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
    >
      <div class="modal-dialog modal-xl modal-dialog-centered modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <div>
              <h5 class="modal-title">ワイルドカード出力</h5>
              <div class="small text-muted">
                選択画像: {{ selectedCount }} 件 / 出力行: {{ outputLineCount }} 行
              </div>
            </div>
            <button
              type="button"
              class="btn-close"
              aria-label="閉じる"
              :disabled="isSaving"
              @click="$emit('close')"
            ></button>
          </div>

          <div class="modal-body">
            <div class="mb-3">
              <div class="form-check form-check-inline">
                <input
                  id="wildcard-export-create"
                  class="form-check-input"
                  type="radio"
                  name="wildcardExportMode"
                  value="create"
                  :checked="exportMode === 'create'"
                  :disabled="isSaving"
                  @change="$emit('change-mode', 'create')"
                />
                <label class="form-check-label" for="wildcard-export-create">
                  新規作成
                </label>
              </div>
              <div class="form-check form-check-inline">
                <input
                  id="wildcard-export-append"
                  class="form-check-input"
                  type="radio"
                  name="wildcardExportMode"
                  value="append"
                  :checked="exportMode === 'append'"
                  :disabled="isSaving"
                  @change="$emit('change-mode', 'append')"
                />
                <label class="form-check-label" for="wildcard-export-append">
                  既存ファイルへ追記
                </label>
              </div>
            </div>

            <div class="mb-3">
              <div class="small fw-semibold mb-2">出力対象タグ</div>
              <div v-if="tagItems.length > 0" class="wildcard-export-tags">
                <button
                  v-for="tag in tagItems"
                  :key="tag.name"
                  type="button"
                  class="btn btn-sm wildcard-tag-toggle"
                  :class="tag.enabled ? 'btn-success' : 'btn-secondary'"
                  :title="tag.name"
                  :disabled="isSaving"
                  @click="$emit('toggle-tag', tag.name)"
                >
                  {{ tag.enabled ? '〇' : '×' }}
                  {{ tag.name }}
                  <span class="badge text-bg-light ms-1">{{ tag.count }}</span>
                </button>
              </div>
              <div v-else class="alert alert-secondary mb-0">
                選択画像に出力可能なタグがありません。
              </div>
            </div>

            <div>
              <div class="small fw-semibold mb-2">出力プレビュー</div>
              <textarea
                v-if="previewText"
                class="form-control wildcard-export-preview"
                :value="previewText"
                readonly
              ></textarea>
              <div v-else class="form-control wildcard-export-preview text-muted">
                出力対象のタグがありません。
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button
              type="button"
              class="btn btn-secondary"
              :disabled="isSaving"
              @click="$emit('close')"
            >
              キャンセル
            </button>
            <button
              type="button"
              class="btn btn-primary"
              :disabled="isSaving || outputLineCount === 0"
              @click="$emit('save')"
            >
              保存
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade show"></div>
  </div>
</template>
