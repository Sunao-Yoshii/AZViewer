<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  item: {
    type: Object,
    default: null,
  },
  imageUrl: {
    type: String,
    default: '',
  },
  isLoadingImage: {
    type: Boolean,
    default: false,
  },
  isSaving: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close', 'save'])

const isActualSize = ref(false)
const form = ref(createFormState(props.item))

const ratingOptions = ['General', 'R-15', 'R-18', 'R-18G']

watch(
  () => props.item,
  (item) => {
    isActualSize.value = false
    form.value = createFormState(item)
  }
)

function createFormState(item) {
  return {
    rating: item?.rating ?? 'General',
    is_checked: item?.is_checked === 1,
    is_favorite: item?.is_favorite === 1,
    comment: item?.comment ?? '',
  }
}

function handleSave() {
  if (!props.item || !window.confirm('入力内容を保存しますか？')) {
    return
  }

  emit('save', {
    id: props.item.id,
    rating: form.value.rating,
    is_checked: form.value.is_checked ? 1 : 0,
    is_favorite: form.value.is_favorite ? 1 : 0,
    comment: form.value.comment,
  })
}
</script>

<template>
  <div v-if="item" class="modal-backdrop-shell" role="presentation">
    <div
      class="modal d-block"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
      aria-labelledby="imageDetailTitle"
    >
      <div class="modal-dialog modal-xl modal-dialog-centered image-detail-dialog">
        <div class="modal-content image-detail-content">
          <div class="modal-header">
            <h1 id="imageDetailTitle" class="modal-title fs-5 text-truncate">
              {{ item.filename }}
            </h1>
            <button type="button" class="btn-close" aria-label="閉じる" @click="$emit('close')"></button>
          </div>

          <div class="modal-body image-detail-body">
            <div class="image-detail-preview">
              <div v-if="isLoadingImage" class="text-secondary">読み込み中</div>
              <img
                v-else-if="imageUrl"
                class="image-detail-image"
                :class="{ 'is-actual-size': isActualSize }"
                :src="imageUrl"
                :alt="item.filename"
                @click="isActualSize = !isActualSize"
              />
              <div v-else class="text-secondary">画像を表示できません</div>
            </div>

            <form class="image-detail-form" @submit.prevent="handleSave">
              <div class="small text-muted detail-path">{{ item.path }}</div>

              <div class="form-check form-switch">
                <input
                  id="detailChecked"
                  v-model="form.is_checked"
                  class="form-check-input"
                  type="checkbox"
                />
                <label class="form-check-label" for="detailChecked">チェック</label>
              </div>

              <div class="form-check form-switch">
                <input
                  id="detailFavorite"
                  v-model="form.is_favorite"
                  class="form-check-input"
                  type="checkbox"
                />
                <label class="form-check-label" for="detailFavorite">お気に入り</label>
              </div>

              <fieldset>
                <legend class="form-label small fw-semibold mb-2">Rating</legend>
                <div
                  v-for="rating in ratingOptions"
                  :key="rating"
                  class="form-check"
                >
                  <input
                    :id="`detailRating-${rating}`"
                    v-model="form.rating"
                    class="form-check-input"
                    type="radio"
                    name="detailRating"
                    :value="rating"
                  />
                  <label class="form-check-label" :for="`detailRating-${rating}`">
                    {{ rating }}
                  </label>
                </div>
              </fieldset>

              <div>
                <label class="form-label small fw-semibold" for="detailComment">Comment</label>
                <textarea
                  id="detailComment"
                  v-model="form.comment"
                  class="form-control"
                  rows="5"
                ></textarea>
              </div>
            </form>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn btn-primary" :disabled="isSaving" @click="handleSave">
              Save
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop show"></div>
  </div>
</template>
