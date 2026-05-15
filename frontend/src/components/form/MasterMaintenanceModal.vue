<script setup>
defineProps({
  show: {
    type: Boolean,
    required: true,
  },
  mode: {
    type: String,
    required: true,
    validator: (value) => ['tag', 'model'].includes(value),
  },
  activeTab: {
    type: String,
    default: 'delete',
    validator: (value) => ['delete', 'replace'].includes(value),
  },
  keyword: {
    type: String,
    default: '',
  },
  items: {
    type: Array,
    default: () => [],
  },
  totalCount: {
    type: Number,
    default: 0,
  },
  selectedItem: {
    type: Object,
    default: null,
  },
  replacementName: {
    type: String,
    default: '',
  },
  isLoading: {
    type: Boolean,
    default: false,
  },
  isProcessing: {
    type: Boolean,
    default: false,
  },
})

defineEmits([
  'close',
  'change-tab',
  'update-keyword',
  'search',
  'select-item',
  'update-replacement-name',
  'delete-item',
  'replace-item',
  'delete-unused',
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
            <h5 class="modal-title">
              {{ mode === 'tag' ? 'タグメンテナンス' : 'モデルメンテナンス' }}
            </h5>
            <button
              type="button"
              class="btn-close"
              aria-label="閉じる"
              :disabled="isProcessing"
              @click="$emit('close')"
            ></button>
          </div>

          <div class="modal-body">
            <ul class="nav nav-tabs">
              <li class="nav-item">
                <button
                  type="button"
                  class="nav-link"
                  :class="{ active: activeTab === 'delete' }"
                  :disabled="isProcessing"
                  @click="$emit('change-tab', 'delete')"
                >
                  {{ mode === 'tag' ? 'タグの削除' : 'モデルの削除' }}
                </button>
              </li>
              <li class="nav-item">
                <button
                  type="button"
                  class="nav-link"
                  :class="{ active: activeTab === 'replace' }"
                  :disabled="isProcessing"
                  @click="$emit('change-tab', 'replace')"
                >
                  {{ mode === 'tag' ? 'タグの置き換え' : 'モデルの置き換え' }}
                </button>
              </li>
            </ul>

            <div class="input-group input-group-sm mt-3">
              <input
                type="text"
                class="form-control"
                :value="keyword"
                :placeholder="mode === 'tag' ? 'タグ名で検索' : 'モデル名で検索'"
                :disabled="isLoading || isProcessing"
                @input="$emit('update-keyword', $event.target.value)"
                @keydown.enter.prevent="$emit('search')"
              />
              <button
                type="button"
                class="btn btn-outline-secondary"
                :disabled="isLoading || isProcessing"
                @click="$emit('search')"
              >
                検索
              </button>
            </div>

            <div class="small text-muted mt-2">
              表示件数: {{ items.length }} / 条件一致: {{ totalCount }}
            </div>

            <div v-if="isLoading" class="text-muted mt-3">
              読み込み中...
            </div>

            <template v-else-if="activeTab === 'delete'">
              <button
                type="button"
                class="btn btn-outline-danger btn-sm mt-3"
                :disabled="isLoading || isProcessing"
                @click="$emit('delete-unused')"
              >
                {{ mode === 'tag' ? '未使用タグを一括削除' : '未使用モデルを一括削除' }}
              </button>

              <div class="master-maintenance-badge-list mt-3">
                <button
                  v-for="item in items"
                  :key="item.id"
                  type="button"
                  class="btn btn-outline-danger btn-sm master-maintenance-badge"
                  :disabled="isLoading || isProcessing"
                  :title="item.name"
                  @click="$emit('delete-item', item)"
                >
                  {{ item.name }}
                  <span class="badge text-bg-light ms-1">{{ item.imageCount }}</span>
                </button>
              </div>
            </template>

            <template v-else>
              <div class="master-maintenance-badge-list mt-3">
                <button
                  v-for="item in items"
                  :key="item.id"
                  type="button"
                  class="btn btn-outline-primary btn-sm master-maintenance-badge"
                  :class="{ active: selectedItem?.id === item.id }"
                  :disabled="isLoading || isProcessing"
                  :title="item.name"
                  @click="$emit('select-item', item)"
                >
                  {{ item.name }}
                  <span class="badge text-bg-light ms-1">{{ item.imageCount }}</span>
                </button>
              </div>

              <div v-if="selectedItem" class="card master-maintenance-edit-card">
                <div class="card-body">
                  <div class="mb-2 fw-semibold">
                    「{{ selectedItem.name }}」を編集
                  </div>
                  <div class="input-group input-group-sm">
                    <input
                      type="text"
                      class="form-control"
                      :value="replacementName"
                      :disabled="isProcessing"
                      :placeholder="mode === 'tag' ? '置き換え後のタグ名' : '置き換え後のモデル名'"
                      @input="$emit('update-replacement-name', $event.target.value)"
                      @keydown.enter.prevent="$emit('replace-item')"
                    />
                    <button
                      type="button"
                      class="btn btn-primary"
                      :disabled="isProcessing || !replacementName.trim()"
                      @click="$emit('replace-item')"
                    >
                      保存
                    </button>
                  </div>
                </div>
              </div>

              <div v-else class="text-muted small mt-3">
                置き換える対象を選択してください。
              </div>
            </template>
          </div>

          <div class="modal-footer">
            <button
              type="button"
              class="btn btn-secondary"
              :disabled="isProcessing"
              @click="$emit('close')"
            >
              閉じる
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade show"></div>
  </div>
</template>
