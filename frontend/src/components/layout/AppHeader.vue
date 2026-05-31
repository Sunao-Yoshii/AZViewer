<script setup>
defineProps({
  appInfo: {
    type: Object,
    required: true,
  },
  isBusy: {
    type: Boolean,
    default: false,
  },
  selectedCount: {
    type: Number,
    default: 0,
  },
  visibleCount: {
    type: Number,
    default: 0,
  },
  isAllVisibleSelected: {
    type: Boolean,
    default: false,
  },
})

defineEmits([
  'open-bulk-attribute-edit',
  'open-wildcard-export',
  'export-selected-tags',
  'move-selected-images',
  'move-selected-images-to-trash',
  'remove-selected-images-from-catalog',
  'import-prompt-tags',
  'import-caption-tags',
  'open-bulk-tag-add',
  'open-duplicate-tag-sets',
  'toggle-visible-selection',
  'open-master-maintenance',
])
</script>

<template>
  <header class="navbar navbar-expand border-bottom bg-white app-header">
    <div class="container-fluid">
      <span class="navbar-brand mb-0 h1">{{ appInfo?.name ?? 'AZViewer' }}</span>
      <div class="app-header-actions">
        <button
          type="button"
          class="btn btn-outline-secondary btn-sm"
          :disabled="isBusy || visibleCount === 0"
          @click="$emit('toggle-visible-selection')"
        >
          {{ isAllVisibleSelected ? '表示中の選択を解除' : `表示中をすべて選択 (${visibleCount})` }}
        </button>
        <button
          type="button"
          class="btn btn-outline-primary btn-sm"
          :disabled="isBusy || selectedCount === 0"
          @click="$emit('open-bulk-attribute-edit')"
        >
          選択画像を一括編集 ({{ selectedCount }})
        </button>
        <div class="dropdown">
          <button
            class="btn btn-outline-success btn-sm dropdown-toggle"
            type="button"
            data-bs-toggle="dropdown"
            :disabled="isBusy || selectedCount === 0"
          >
            アウトプット ({{ selectedCount }})
          </button>
          <ul class="dropdown-menu">
            <li>
              <button
                type="button"
                class="dropdown-item"
                :disabled="isBusy || selectedCount === 0"
                @click="$emit('open-wildcard-export')"
              >
                ワイルドカード出力
              </button>
            </li>
            <li>
              <button
                type="button"
                class="dropdown-item"
                :disabled="isBusy || selectedCount === 0"
                @click="$emit('export-selected-tags')"
              >
                タグ出力
              </button>
            </li>
          </ul>
        </div>
        <div class="dropdown">
          <button
            class="btn btn-outline-success btn-sm dropdown-toggle"
            type="button"
            data-bs-toggle="dropdown"
            :disabled="isBusy || selectedCount === 0"
          >
            ファイル操作 ({{ selectedCount }})
          </button>
          <ul class="dropdown-menu">
            <li>
              <button
                type="button"
                class="dropdown-item"
                :disabled="isBusy || selectedCount === 0"
                @click="$emit('move-selected-images')"
              >
                ファイルを移動
              </button>
            </li>
            <li>
              <button
                type="button"
                class="dropdown-item text-warning"
                :disabled="isBusy || selectedCount === 0"
                @click="$emit('move-selected-images-to-trash')"
              >
                ごみ箱へ移動
              </button>
            </li>
            <li><hr class="dropdown-divider" /></li>
            <li>
              <button
                type="button"
                class="dropdown-item"
                :disabled="isBusy || selectedCount === 0"
                @click="$emit('remove-selected-images-from-catalog')"
              >
                選択画像を管理対象から除外
              </button>
            </li>
          </ul>
        </div>
        <div class="dropdown">
          <button
            class="btn btn-outline-primary btn-sm dropdown-toggle"
            type="button"
            data-bs-toggle="dropdown"
            :disabled="isBusy"
          >
            タグ操作
          </button>
          <ul class="dropdown-menu">
            <li>
              <button
                type="button"
                class="dropdown-item"
                :disabled="isBusy"
                @click="$emit('import-prompt-tags')"
              >
                プロンプトの読み取り
              </button>
            </li>
            <li>
              <button
                type="button"
                class="dropdown-item"
                :disabled="isBusy || selectedCount === 0"
                @click="$emit('import-caption-tags')"
              >
                キャプションタグ読み込み
              </button>
            </li>
            <li>
              <button
                type="button"
                class="dropdown-item"
                :disabled="isBusy || selectedCount === 0"
                @click="$emit('open-bulk-tag-add')"
              >
                一括タグ追加
              </button>
            </li>
            <li>
              <button
                type="button"
                class="dropdown-item"
                :disabled="isBusy"
                @click="$emit('open-duplicate-tag-sets')"
              >
                重複タグ構成の検索
              </button>
            </li>
          </ul>
        </div>
        <div class="dropdown">
          <button
            class="btn btn-outline-secondary btn-sm dropdown-toggle"
            type="button"
            data-bs-toggle="dropdown"
            :disabled="isBusy"
          >
            マスタメンテナンス
          </button>
          <ul class="dropdown-menu">
            <li>
              <button
                type="button"
                class="dropdown-item"
                @click="$emit('open-master-maintenance', 'tag')"
              >
                タグメンテナンス
              </button>
            </li>
            <li>
              <button
                type="button"
                class="dropdown-item"
                @click="$emit('open-master-maintenance', 'model')"
              >
                モデルメンテナンス
              </button>
            </li>
          </ul>
        </div>
        <span class="text-secondary small d-none d-sm-inline">
          {{ appInfo?.version ? `v${appInfo.version}` : 'Vue + pywebview' }}
        </span>
      </div>
    </div>
  </header>
</template>
