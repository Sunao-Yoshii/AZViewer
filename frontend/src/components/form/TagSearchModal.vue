<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    required: true,
  },
  selectedTags: {
    type: Array,
    default: () => [],
  },
  tagItems: {
    type: Array,
    default: () => [],
  },
  totalCount: {
    type: Number,
    default: 0,
  },
  isLoading: {
    type: Boolean,
    default: false,
  },
  externalMessage: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['close', 'apply', 'search-tags'])

const filterText = ref('')
const workingSelectedTags = ref([])
const message = ref('')

watch(
  () => props.show,
  (show) => {
    if (!show) {
      return
    }

    filterText.value = ''
    workingSelectedTags.value = [...(props.selectedTags ?? [])].slice(0, 3)
    message.value = ''
  }
)

function handleSearch() {
  emit('search-tags', {
    keyword: filterText.value,
  })
}

function addTag(tagName) {
  if (!tagName || workingSelectedTags.value.includes(tagName)) {
    return
  }

  if (workingSelectedTags.value.length >= 3) {
    message.value = 'タグは最大3件まで指定できます。'
    return
  }

  workingSelectedTags.value = [...workingSelectedTags.value, tagName]
  message.value = ''
}

function removeTag(tagName) {
  workingSelectedTags.value = workingSelectedTags.value.filter((value) => value !== tagName)
  message.value = ''
}

function handleApply() {
  emit('apply', [...workingSelectedTags.value].slice(0, 3))
}
</script>

<template>
  <div v-if="show" class="modal-backdrop-shell" role="presentation">
    <div
      class="modal d-block"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
      aria-labelledby="tagSearchTitle"
    >
      <div class="modal-dialog modal-lg modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h1 id="tagSearchTitle" class="modal-title fs-5">タグ検索</h1>
            <button type="button" class="btn-close" aria-label="閉じる" @click="$emit('close')"></button>
          </div>

          <div class="modal-body vstack gap-3">
            <div>
              <div class="small fw-semibold mb-1">選択中</div>
              <div v-if="workingSelectedTags.length" class="d-flex flex-wrap gap-1">
                <span
                  v-for="tag in workingSelectedTags"
                  :key="tag"
                  class="badge text-bg-secondary"
                >
                  {{ tag }}
                  <button
                    type="button"
                    class="btn-close btn-close-white ms-1 tag-badge-close"
                    aria-label="タグを削除"
                    @click="removeTag(tag)"
                  ></button>
                </span>
              </div>
              <div v-else class="small text-secondary">未選択</div>
            </div>

            <div>
              <div class="input-group input-group-sm">
                <input
                  v-model="filterText"
                  type="text"
                  class="form-control"
                  placeholder="タグ名で検索"
                  :disabled="isLoading"
                  @keydown.enter.prevent="handleSearch"
                />
                <button
                  type="button"
                  class="btn btn-outline-secondary"
                  :disabled="isLoading"
                  @click="handleSearch"
                >
                  検索
                </button>
              </div>
            </div>

            <div v-if="message || externalMessage" class="small text-danger">
              {{ message || externalMessage }}
            </div>

            <div class="d-flex justify-content-between align-items-center small text-secondary">
              <span>表示件数: {{ tagItems.length }} / {{ totalCount }}</span>
              <span v-if="isLoading">読み込み中</span>
            </div>

            <div class="tag-search-list">
              <button
                v-for="tag in tagItems"
                :key="tag.id"
                type="button"
                class="badge text-bg-light border tag-search-item"
                :class="{ 'is-selected': workingSelectedTags.includes(tag.name) }"
                @click="addTag(tag.name)"
              >
                {{ tag.name }}
              </button>
              <div v-if="!isLoading && tagItems.length === 0" class="small text-secondary">
                表示できるタグがありません
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn btn-primary" @click="handleApply">
              OK
            </button>
            <button type="button" class="btn btn-secondary" @click="$emit('close')">
              キャンセル
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop show"></div>
  </div>
</template>
