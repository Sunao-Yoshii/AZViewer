<script setup>
import { computed, ref, watch } from 'vue'
import { fetchModelsForSearch } from '../../services/backendApi'
import ImageModelSelectModal from './ImageModelSelectModal.vue'

const props = defineProps({
  item: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['cancel', 'save', 'open-metadata'])

const ratingOptions = ['General', 'R-15', 'R-18', 'R-18G']
const BRACKET_CHARS = new Set(['(', ')', '[', ']', '{', '}'])
const MAX_TAG_NAME_LENGTH = 512
const form = ref(createFormState(props.item))
const tagError = ref('')
const showModelSelectModal = ref(false)
const modelSearchState = ref({
  items: [],
  totalCount: 0,
  isLoading: false,
  message: '',
})

const isDirty = computed(() => {
  return (
    form.value.rating !== props.item.rating ||
    Number(form.value.is_checked) !== props.item.is_checked ||
    Number(form.value.is_favorite) !== props.item.is_favorite ||
    form.value.comment !== (props.item.comment ?? '') ||
    JSON.stringify(normalizeTagsForCompare(form.value.tags)) !==
      JSON.stringify(normalizeTagsForCompare(props.item.tags)) ||
    form.value.modelName !== (props.item.modelName ?? '')
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
    tags: [...(item.tags ?? [])],
    tagInput: '',
    modelName: item.modelName ?? '',
  }
}

function createSavePayload() {
  return {
    id: props.item.id,
    rating: form.value.rating,
    is_checked: form.value.is_checked ? 1 : 0,
    is_favorite: form.value.is_favorite ? 1 : 0,
    comment: form.value.comment,
    tags: form.value.tags,
    modelName: form.value.modelName || null,
  }
}

function normalizeTagText(value) {
  return value
    .trim()
    .split('')
    .filter((char, index, chars) => !isUnescapedBracket(char, chars[index - 1]))
    .join('')
    .replace(/:\d+(?:\.\d+)?$/, '')
    .trim()
    .toLowerCase()
}

function isUnescapedBracket(char, previousChar) {
  return BRACKET_CHARS.has(char) && previousChar !== '\\'
}

function normalizeTagsForCompare(tags) {
  return [...(tags ?? [])].sort()
}

function addTagsFromInput() {
  tagError.value = ''
  const normalizedTags = form.value.tagInput
    .split(',')
    .map(normalizeTagText)
    .filter(Boolean)

  const tooLong = normalizedTags.find((tag) => tag.length > MAX_TAG_NAME_LENGTH)
  if (tooLong) {
    tagError.value = `タグは${MAX_TAG_NAME_LENGTH}文字以内で入力してください。`
    return
  }

  form.value.tags = [...new Set([...form.value.tags, ...normalizedTags])]
  form.value.tagInput = ''
}

function removeTag(tag) {
  form.value.tags = form.value.tags.filter((value) => value !== tag)
}

function clearModelName() {
  form.value.modelName = ''
}

function applyModelName(modelName) {
  form.value.modelName = (modelName || '').trim()
  showModelSelectModal.value = false
}

function closeModelSelectModal() {
  showModelSelectModal.value = false
}

async function handleSearchModels({ keyword }) {
  modelSearchState.value = {
    ...modelSearchState.value,
    isLoading: true,
    message: '',
  }

  try {
    const result = await fetchModelsForSearch({
      keyword: keyword ?? '',
      limit: 256,
    })
    if (!result.success) {
      applyModelSearchFailure(result.message)
      return
    }

    modelSearchState.value = {
      items: result.data?.models ?? [],
      totalCount: result.data?.total_count ?? 0,
      isLoading: false,
      message: '',
    }
  } catch {
    applyModelSearchFailure()
  }
}

function applyModelSearchFailure(message = 'モデル一覧を取得できませんでした。') {
  modelSearchState.value = {
    items: [],
    totalCount: 0,
    isLoading: false,
    message: message || 'モデル一覧を取得できませんでした。',
  }
}

function applyTextToTagInput(value) {
  form.value.tagInput = value
}

function handleReturn() {
  if (!isDirty.value) {
    emit('cancel')
    return
  }

  emit('save', createSavePayload())
}

defineExpose({
  applyTextToTagInput,
})
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

    <div class="mt-2">
      <div class="d-flex justify-content-between align-items-center gap-2 mb-1">
        <label class="form-label small fw-semibold mb-0" :for="`tileTags-${item.id}`">
          Tags
        </label>
        <button
          type="button"
          class="btn btn-outline-secondary btn-sm"
          @click="$emit('open-metadata')"
        >
          メタ情報からタグ
        </button>
      </div>
      <input
        :id="`tileTags-${item.id}`"
        v-model="form.tagInput"
        class="form-control form-control-sm"
        type="text"
        placeholder="タグを入力。カンマ区切り可"
        @keydown.enter.prevent="addTagsFromInput"
      />
      <div v-if="tagError" class="form-text text-danger">{{ tagError }}</div>
      <div v-if="form.tags.length" class="mt-2 d-flex flex-wrap gap-1">
        <span
          v-for="tag in form.tags"
          :key="tag"
          class="badge text-bg-secondary tag-badge tag-badge--editable"
          :title="tag"
        >
          {{ tag }}
          <button
            type="button"
            class="btn-close btn-close-white ms-1"
            style="font-size: 0.55rem;"
            aria-label="タグを削除"
            @click="removeTag(tag)"
          ></button>
        </span>
      </div>
    </div>

    <div class="mt-2">
      <div class="small text-muted mb-1">Model</div>
      <div class="d-flex align-items-center gap-2 flex-wrap">
        <span
          v-if="form.modelName"
          class="badge text-bg-info image-model-badge"
          :title="form.modelName"
        >
          {{ form.modelName }}
        </span>
        <span v-else class="small text-muted">未設定</span>
        <button
          type="button"
          class="btn btn-outline-secondary btn-sm"
          @click="showModelSelectModal = true"
        >
          モデル設定
        </button>
        <button
          v-if="form.modelName"
          type="button"
          class="btn btn-outline-danger btn-sm"
          @click="clearModelName"
        >
          解除
        </button>
      </div>
    </div>

    <button type="submit" class="btn btn-primary btn-sm w-100 mt-2">
      {{ isDirty ? '保存して戻る' : '表示に戻る' }}
    </button>
    <ImageModelSelectModal
      :show="showModelSelectModal"
      :selected-model-name="form.modelName"
      :models="modelSearchState.items"
      :total-count="modelSearchState.totalCount"
      :is-loading="modelSearchState.isLoading"
      :external-message="modelSearchState.message"
      @close="closeModelSelectModal"
      @search="handleSearchModels"
      @apply="applyModelName"
    />
  </form>
</template>
