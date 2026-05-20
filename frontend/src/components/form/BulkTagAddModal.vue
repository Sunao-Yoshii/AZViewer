<script setup>
import { computed } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    required: true,
  },
  selectedCount: {
    type: Number,
    default: 0,
  },
  tagsText: {
    type: String,
    default: '',
  },
  isSaving: {
    type: Boolean,
    default: false,
  },
})

defineEmits([
  'close',
  'update-tags-text',
  'save',
])

const canSave = computed(() => props.selectedCount > 0 && props.tagsText.trim().length > 0)
</script>

<template>
  <div v-if="show" class="modal-backdrop-shell" role="presentation">
    <div
      class="modal fade show d-block"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
    >
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <div>
              <h5 class="modal-title">一括タグ追加</h5>
              <div class="small text-muted">選択画像: {{ selectedCount }} 件</div>
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
            <label class="form-label" for="bulk-tag-add-text">
              カンマ区切りで複数タグを追加できます。
            </label>
            <textarea
              id="bulk-tag-add-text"
              class="form-control bulk-tag-add-textarea"
              rows="5"
              placeholder="例: my_lora_trigger, character_name, outfit_a"
              :value="tagsText"
              :disabled="isSaving"
              @input="$emit('update-tags-text', $event.target.value)"
            ></textarea>
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
              :disabled="isSaving || !canSave"
              @click="$emit('save')"
            >
              追加
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade show"></div>
  </div>
</template>
