<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    required: true,
  },
  selectedFolder: {
    type: String,
    default: null,
  },
  folderItems: {
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

const emit = defineEmits(['close', 'apply', 'search-folders'])

const filterText = ref('')
const workingSelectedFolder = ref(null)

watch(
  () => props.show,
  (show) => {
    if (!show) {
      return
    }

    filterText.value = ''
    workingSelectedFolder.value = props.selectedFolder || null
  }
)

function handleSearch() {
  emit('search-folders', {
    keyword: filterText.value,
  })
}

function selectFolder(folderName) {
  workingSelectedFolder.value = folderName || null
}

function clearFolder() {
  workingSelectedFolder.value = null
}

function handleApply() {
  emit('apply', workingSelectedFolder.value)
}
</script>

<template>
  <div v-if="show" class="modal-backdrop-shell" role="presentation">
    <div
      class="modal d-block"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
      aria-labelledby="folderSearchTitle"
    >
      <div class="modal-dialog modal-lg modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h1 id="folderSearchTitle" class="modal-title fs-5">フォルダ検索</h1>
            <button type="button" class="btn-close" aria-label="閉じる" @click="$emit('close')"></button>
          </div>

          <div class="modal-body vstack gap-3">
            <div>
              <div class="small fw-semibold mb-1">選択中</div>
              <div v-if="workingSelectedFolder" class="d-flex flex-wrap gap-1">
                <span class="badge text-bg-secondary search-folder-badge">
                  {{ workingSelectedFolder }}
                  <button
                    type="button"
                    class="btn-close btn-close-white ms-1 search-badge-close"
                    aria-label="フォルダ選択を解除"
                    @click="clearFolder"
                  ></button>
                </span>
              </div>
              <div v-else class="small text-secondary">未選択</div>
            </div>

            <div class="input-group input-group-sm">
              <input
                v-model="filterText"
                type="text"
                class="form-control"
                placeholder="フォルダ名で検索"
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

            <div v-if="externalMessage" class="small text-danger">
              {{ externalMessage }}
            </div>

            <div class="d-flex justify-content-between align-items-center small text-secondary">
              <span>表示件数: {{ folderItems.length }} / {{ totalCount }}</span>
              <span v-if="isLoading">読み込み中</span>
            </div>

            <div class="search-candidate-list">
              <button
                v-for="folder in folderItems"
                :key="folder.name"
                type="button"
                class="badge text-bg-light border search-candidate-item folder-search-item"
                :class="{ 'is-selected': workingSelectedFolder === folder.name }"
                @click="selectFolder(folder.name)"
              >
                <span class="folder-search-name">{{ folder.name }}</span>
                <span class="folder-search-count">{{ folder.image_count }}</span>
              </button>
              <div v-if="!isLoading && folderItems.length === 0" class="small text-secondary">
                表示できるフォルダがありません
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
