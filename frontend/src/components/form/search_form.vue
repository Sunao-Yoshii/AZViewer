<script setup>
import { reactive, ref } from 'vue'
import {
  fetchFoldersForSearch,
  fetchTagsForSearch,
} from '../../services/backendApi'
import FolderSearchModal from './FolderSearchModal.vue'
import TagSearchModal from './TagSearchModal.vue'

const props = defineProps({
  filters: {
    type: Object,
    required: true,
  },
  isBusy: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['search'])
const showTagSearchModal = ref(false)
const showFolderSearchModal = ref(false)
const tagSearchState = reactive({
  items: [],
  totalCount: 0,
  isLoading: false,
  message: '',
})
const folderSearchState = reactive({
  items: [],
  totalCount: 0,
  isLoading: false,
  message: '',
})

const ratingOptions = [
  { label: 'すべて', value: '' },
  { label: 'General', value: 'General' },
  { label: 'R-15', value: 'R-15' },
  { label: 'R-18', value: 'R-18' },
  { label: 'R-18G', value: 'R-18G' },
]

function removeSearchTag(tag) {
  props.filters.tags = (props.filters.tags ?? []).filter((value) => value !== tag)
}

function clearSearchFolder() {
  props.filters.folder = null
}

function clearDuplicateCondition() {
  props.filters.tagHash = null
  props.filters.tagSet = null
  props.filters.duplicateTagNames = null
}

async function openTagSearchModal() {
  showTagSearchModal.value = true
  await handleSearchTags({ keyword: '' })
}

function closeTagSearchModal() {
  showTagSearchModal.value = false
}

function applyTags(tags) {
  props.filters.tags = [...tags].slice(0, 3)
  showTagSearchModal.value = false
}

async function openFolderSearchModal() {
  showFolderSearchModal.value = true
  await handleSearchFolders({ keyword: '' })
}

function closeFolderSearchModal() {
  showFolderSearchModal.value = false
}

function applyFolder(folder) {
  props.filters.folder = folder || null
  showFolderSearchModal.value = false
}

async function handleSearchTags({ keyword }) {
  tagSearchState.isLoading = true
  tagSearchState.message = ''

  try {
    const result = await fetchTagsForSearch({
      keyword: keyword ?? '',
      limit: 256,
    })
    if (!result.success) {
      applyTagSearchFailure(result.message)
      return
    }

    tagSearchState.items = result.data?.tags ?? []
    tagSearchState.totalCount = result.data?.total_count ?? 0
  } catch {
    applyTagSearchFailure()
  } finally {
    tagSearchState.isLoading = false
  }
}

function applyTagSearchFailure(message = 'タグ一覧を取得できませんでした。') {
  tagSearchState.items = []
  tagSearchState.totalCount = 0
  tagSearchState.message = message || 'タグ一覧を取得できませんでした。'
}

async function handleSearchFolders({ keyword }) {
  folderSearchState.isLoading = true
  folderSearchState.message = ''

  try {
    const result = await fetchFoldersForSearch({
      keyword: keyword ?? '',
      limit: 256,
    })
    if (!result.success) {
      applyFolderSearchFailure(result.message)
      return
    }

    folderSearchState.items = result.data?.folders ?? []
    folderSearchState.totalCount = result.data?.total_count ?? 0
  } catch {
    applyFolderSearchFailure()
  } finally {
    folderSearchState.isLoading = false
  }
}

function applyFolderSearchFailure(message = 'フォルダ一覧を取得できませんでした。') {
  folderSearchState.items = []
  folderSearchState.totalCount = 0
  folderSearchState.message = message || 'フォルダ一覧を取得できませんでした。'
}
</script>

<template>
  <div class="vstack gap-3">
    <div v-if="filters.duplicateTagNames" class="alert alert-info py-2 px-2 small mb-0">
      <div class="search-special-condition">
        <span class="search-special-condition-text">
          特殊条件: 重複タグ構成「{{ filters.duplicateTagNames }}」
        </span>
        <button
          type="button"
          class="btn btn-link btn-sm p-0"
          :disabled="isBusy"
          @click="clearDuplicateCondition"
        >
          解除
        </button>
      </div>
    </div>

    <div>
      <label class="form-label small fw-semibold" for="searchPath">Path</label>
      <input
        id="searchPath"
        v-model="filters.path"
        class="form-control form-control-sm"
        type="text"
        placeholder="部分一致"
        :disabled="isBusy"
      />
    </div>

    <div>
      <label class="form-label small fw-semibold" for="searchRating">Rating</label>
      <select
        id="searchRating"
        v-model="filters.rating"
        class="form-select form-select-sm"
        :disabled="isBusy"
      >
        <option v-for="option in ratingOptions" :key="option.value" :value="option.value">
          {{ option.label }}
        </option>
      </select>
    </div>

    <div class="form-check">
      <input
        id="searchChecked"
        v-model="filters.is_checked"
        class="form-check-input"
        type="checkbox"
        :disabled="isBusy"
      />
      <label class="form-check-label small" for="searchChecked">チェック済みのみ</label>
    </div>

    <div class="form-check">
      <input
        id="searchFavorite"
        v-model="filters.is_favorite"
        class="form-check-input"
        type="checkbox"
        :disabled="isBusy"
      />
      <label class="form-check-label small" for="searchFavorite">お気に入りのみ</label>
    </div>

    <div>
      <div class="d-flex justify-content-between align-items-center mb-1">
        <span class="form-label small fw-semibold mb-0">フォルダ</span>
        <button
          type="button"
          class="btn btn-outline-secondary btn-sm"
          :disabled="isBusy"
          @click="openFolderSearchModal"
        >
          フォルダ選択
        </button>
      </div>

      <div v-if="filters.folder" class="d-flex flex-wrap gap-1">
        <span class="badge text-bg-secondary search-folder-badge">
          {{ filters.folder }}
          <button
            type="button"
            class="btn-close btn-close-white ms-1 search-badge-close"
            aria-label="フォルダ検索条件を解除"
            :disabled="isBusy"
            @click="clearSearchFolder"
          ></button>
        </span>
      </div>
      <div v-else class="small text-secondary">未指定</div>
    </div>

    <div>
      <div class="d-flex justify-content-between align-items-center mb-1">
        <span class="form-label small fw-semibold mb-0">タグ</span>
        <button
          type="button"
          class="btn btn-outline-secondary btn-sm"
          :disabled="isBusy"
          @click="openTagSearchModal"
        >
          タグ選択
        </button>
      </div>

      <div v-if="filters.tags?.length" class="d-flex flex-wrap gap-1">
        <span
          v-for="tag in filters.tags"
          :key="tag"
          class="badge text-bg-secondary"
        >
          {{ tag }}
          <button
            type="button"
            class="btn-close btn-close-white ms-1 search-badge-close"
            aria-label="タグを検索条件から削除"
            :disabled="isBusy"
            @click="removeSearchTag(tag)"
          ></button>
        </span>
      </div>
      <div v-else class="small text-secondary">未指定</div>
    </div>

    <button
      type="button"
      class="btn btn-primary btn-sm w-100"
      :disabled="isBusy"
      @click="emit('search')"
    >
      <i class="bi bi-search me-1" aria-hidden="true"></i>
      検索
    </button>

    <TagSearchModal
      :show="showTagSearchModal"
      :selected-tags="filters.tags ?? []"
      :tag-items="tagSearchState.items"
      :total-count="tagSearchState.totalCount"
      :is-loading="tagSearchState.isLoading"
      :external-message="tagSearchState.message"
      @close="closeTagSearchModal"
      @apply="applyTags"
      @search-tags="handleSearchTags"
    />
    <FolderSearchModal
      :show="showFolderSearchModal"
      :selected-folder="filters.folder"
      :folder-items="folderSearchState.items"
      :total-count="folderSearchState.totalCount"
      :is-loading="folderSearchState.isLoading"
      :external-message="folderSearchState.message"
      @close="closeFolderSearchModal"
      @apply="applyFolder"
      @search-folders="handleSearchFolders"
    />
  </div>
</template>
