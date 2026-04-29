<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  item: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['cancel', 'save'])

const ratingOptions = ['General', 'R-15', 'R-18', 'R-18G']
const form = ref(createFormState(props.item))

const isDirty = computed(() => {
  return (
    form.value.rating !== props.item.rating ||
    Number(form.value.is_checked) !== props.item.is_checked ||
    Number(form.value.is_favorite) !== props.item.is_favorite ||
    form.value.comment !== (props.item.comment ?? '')
  )
})

watch(
  () => props.item,
  (item) => {
    form.value = createFormState(item)
  }
)

function createFormState(item) {
  return {
    rating: item.rating ?? 'General',
    is_checked: item.is_checked === 1,
    is_favorite: item.is_favorite === 1,
    comment: item.comment ?? '',
  }
}

function createSavePayload() {
  return {
    id: props.item.id,
    rating: form.value.rating,
    is_checked: form.value.is_checked ? 1 : 0,
    is_favorite: form.value.is_favorite ? 1 : 0,
    comment: form.value.comment,
  }
}

function handleReturn() {
  if (!isDirty.value) {
    emit('cancel')
    return
  }

  emit('save', createSavePayload())
}
</script>

<template>
  <form class="image-tile-edit mt-2" @submit.prevent="handleReturn">
    <fieldset class="mb-2">
      <legend class="form-label small fw-semibold mb-1">Rating</legend>
      <div class="btn-group btn-group-sm image-tile-rating-group" role="group" aria-label="Rating">
        <template v-for="rating in ratingOptions" :key="rating">
          <input
            :id="`tileRating-${item.id}-${rating}`"
            v-model="form.rating"
            class="btn-check"
            type="radio"
            :name="`tileRating-${item.id}`"
            :value="rating"
            autocomplete="off"
          />
          <label class="btn btn-outline-secondary" :for="`tileRating-${item.id}-${rating}`">
            {{ rating }}
          </label>
        </template>
      </div>
    </fieldset>

    <div class="form-check form-switch image-tile-switch">
      <input
        :id="`tileChecked-${item.id}`"
        v-model="form.is_checked"
        class="form-check-input"
        type="checkbox"
      />
      <label class="form-check-label" :for="`tileChecked-${item.id}`">チェック</label>
    </div>

    <div class="form-check form-switch image-tile-switch">
      <input
        :id="`tileFavorite-${item.id}`"
        v-model="form.is_favorite"
        class="form-check-input"
        type="checkbox"
      />
      <label class="form-check-label" :for="`tileFavorite-${item.id}`">お気に入り</label>
    </div>

    <div class="mt-2">
      <label class="form-label small fw-semibold mb-1" :for="`tileComment-${item.id}`">
        Comment
      </label>
      <textarea
        :id="`tileComment-${item.id}`"
        v-model="form.comment"
        class="form-control form-control-sm"
        maxlength="255"
        rows="3"
      ></textarea>
    </div>

    <button type="submit" class="btn btn-primary btn-sm w-100 mt-2">
      {{ isDirty ? '保存して戻る' : '表示に戻る' }}
    </button>
  </form>
</template>
