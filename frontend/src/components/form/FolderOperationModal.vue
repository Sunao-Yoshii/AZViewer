<script setup>
import { computed } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    required: true,
  },
  mode: {
    type: String,
    required: true,
    validator: (value) => ['remove', 'trash'].includes(value),
  },
  folders: {
    type: Array,
    default: () => [],
  },
  keyword: {
    type: String,
    default: '',
  },
  selectedFolder: {
    type: Object,
    default: null,
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
  isExecuting: {
    type: Boolean,
    default: false,
  },
})

defineEmits([
  'close',
  'update-keyword',
  'search',
  'select-folder',
  'execute',
])

const title = computed(() => (
  props.mode === 'trash'
    ? 'フォルダごとごみ箱へ移動'
    : 'フォルダを管理対象から除外'
))
const description = computed(() => (
  props.mode === 'trash'
    ? '選択したフォルダに属する AZViewer 登録済み画像を、OS のごみ箱へ移動します。AZViewer に登録されていないファイルは対象にしません。'
    : '選択したフォルダに属する AZViewer 登録済み画像を、管理対象から除外します。実際の画像ファイルは削除されません。'
))
const executeLabel = computed(() => (props.mode === 'trash' ? 'ごみ箱へ移動' : '管理対象から除外'))
const executeButtonClass = computed(() => (props.mode === 'trash' ? 'btn-danger' : 'btn-warning'))
const canExecute = computed(() => (
  !props.isLoading &&
  !props.isExecuting &&
  props.selectedFolder?.id &&
  (props.selectedFolder?.imageCount ?? 0) > 0
))
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
            <h5 class="modal-title">{{ title }}</h5>
            <button
              type="button"
              class="btn-close"
              aria-label="閉じる"
              :disabled="isExecuting"
              @click="$emit('close')"
            ></button>
          </div>

          <div class="modal-body vstack gap-3">
            <div class="alert py-2 mb-0" :class="mode === 'trash' ? 'alert-danger' : 'alert-warning'">
              {{ description }}
            </div>

            <div class="input-group input-group-sm">
              <input
                type="text"
                class="form-control"
                :value="keyword"
                placeholder="フォルダ名またはパスで検索"
                :disabled="isLoading || isExecuting"
                @input="$emit('update-keyword', $event.target.value)"
                @keydown.enter.prevent="$emit('search')"
              />
              <button
                type="button"
                class="btn btn-outline-primary"
                :disabled="isLoading || isExecuting"
                @click="$emit('search')"
              >
                検索
              </button>
            </div>

            <div class="d-flex flex-wrap justify-content-between gap-2 small text-secondary">
              <span>表示件数: {{ folders.length }} / 条件一致: {{ totalCount }}</span>
              <span v-if="isLoading">読み込み中</span>
              <span v-if="totalCount > limit">候補が多いため、先頭 {{ limit }} 件のみ表示しています。</span>
            </div>

            <div class="list-group folder-operation-list">
              <button
                v-for="folder in folders"
                :key="folder.id"
                type="button"
                class="list-group-item list-group-item-action"
                :class="{ active: selectedFolder?.id === folder.id }"
                :disabled="isExecuting"
                @click="$emit('select-folder', folder)"
              >
                <div class="d-flex justify-content-between gap-2">
                  <div class="folder-operation-main">
                    <div class="fw-semibold">{{ folder.name }}</div>
                    <div class="small folder-operation-path">{{ folder.path }}</div>
                  </div>
                  <span class="badge text-bg-secondary align-self-start">
                    {{ folder.imageCount }} 件
                  </span>
                </div>
              </button>

              <div v-if="!isLoading && folders.length === 0" class="list-group-item small text-secondary">
                表示できるフォルダがありません
              </div>
            </div>

            <div v-if="selectedFolder" class="border rounded p-3 folder-operation-selected">
              <div class="small text-secondary mb-1">対象フォルダ</div>
              <div class="fw-semibold folder-operation-path">{{ selectedFolder.path }}</div>
              <div class="small text-secondary mt-2">
                対象画像: {{ selectedFolder.imageCount ?? 0 }} 件
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button
              type="button"
              class="btn"
              :class="executeButtonClass"
              :disabled="!canExecute"
              @click="$emit('execute')"
            >
              {{ executeLabel }}
            </button>
            <button
              type="button"
              class="btn btn-secondary"
              :disabled="isExecuting"
              @click="$emit('close')"
            >
              キャンセル
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade show"></div>
  </div>
</template>
