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
  form: {
    type: Object,
    required: true,
  },
  isSaving: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits([
  'close',
  'update-form',
  'save',
])

const ratingOptions = ['General', 'R-15', 'R-18', 'R-18G']

const hasAnyUpdate = computed(() => (
  props.form.ratingEnabled ||
  props.form.checkedEnabled ||
  props.form.favoriteEnabled
))

function getRatingInputId(rating) {
  return `bulk-rating-${rating.toLowerCase().replace(/[^a-z0-9]/g, '')}`
}

function updateField(key, value) {
  emit('update-form', { key, value })
}
</script>

<template>
  <div v-if="show" class="modal-backdrop-shell" role="presentation">
    <div
      class="modal fade show d-block"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
    >
      <div class="modal-dialog modal-lg modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <div>
              <h5 class="modal-title">選択画像を一括編集</h5>
              <div class="small text-muted">対象: {{ selectedCount }} 件</div>
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
            <section class="bulk-attribute-edit-section">
              <div class="bulk-attribute-edit-title">レーティング</div>
              <div class="form-check mb-2">
                <input
                  id="bulk-rating-enabled"
                  class="form-check-input"
                  type="checkbox"
                  :checked="form.ratingEnabled"
                  :disabled="isSaving"
                  @change="updateField('ratingEnabled', $event.target.checked)"
                />
                <label class="form-check-label" for="bulk-rating-enabled">
                  レーティングを変更する
                </label>
              </div>

              <div class="btn-group" role="group" aria-label="レーティング選択">
                <template
                  v-for="rating in ratingOptions"
                  :key="rating"
                >
                  <input
                    :id="getRatingInputId(rating)"
                    type="radio"
                    class="btn-check"
                    name="bulkRating"
                    :value="rating"
                    :checked="form.rating === rating"
                    :disabled="!form.ratingEnabled || isSaving"
                    @change="updateField('rating', rating)"
                  />
                  <label
                    class="btn btn-outline-secondary"
                    :for="getRatingInputId(rating)"
                  >
                    {{ rating }}
                  </label>
                </template>
              </div>
            </section>

            <section class="bulk-attribute-edit-section">
              <div class="bulk-attribute-edit-title">チェック状態</div>
              <div class="form-check mb-2">
                <input
                  id="bulk-checked-enabled"
                  class="form-check-input"
                  type="checkbox"
                  :checked="form.checkedEnabled"
                  :disabled="isSaving"
                  @change="updateField('checkedEnabled', $event.target.checked)"
                />
                <label class="form-check-label" for="bulk-checked-enabled">
                  チェック状態を変更する
                </label>
              </div>

              <div class="form-check form-switch">
                <input
                  id="bulk-is-checked"
                  class="form-check-input"
                  type="checkbox"
                  :checked="form.isChecked"
                  :disabled="!form.checkedEnabled || isSaving"
                  @change="updateField('isChecked', $event.target.checked)"
                />
                <label class="form-check-label" for="bulk-is-checked">
                  チェック
                </label>
              </div>
            </section>

            <section class="bulk-attribute-edit-section">
              <div class="bulk-attribute-edit-title">お気に入り状態</div>
              <div class="form-check mb-2">
                <input
                  id="bulk-favorite-enabled"
                  class="form-check-input"
                  type="checkbox"
                  :checked="form.favoriteEnabled"
                  :disabled="isSaving"
                  @change="updateField('favoriteEnabled', $event.target.checked)"
                />
                <label class="form-check-label" for="bulk-favorite-enabled">
                  お気に入り状態を変更する
                </label>
              </div>

              <div class="form-check form-switch">
                <input
                  id="bulk-is-favorite"
                  class="form-check-input"
                  type="checkbox"
                  :checked="form.isFavorite"
                  :disabled="!form.favoriteEnabled || isSaving"
                  @change="updateField('isFavorite', $event.target.checked)"
                />
                <label class="form-check-label" for="bulk-is-favorite">
                  お気に入り
                </label>
              </div>
            </section>
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
              :disabled="isSaving || selectedCount === 0 || !hasAnyUpdate"
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
