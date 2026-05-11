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
  'import-prompt-tags',
  'toggle-visible-selection',
  'delete-selected-images',
  'move-selected-images',
  'open-bulk-attribute-edit',
  'open-wildcard-export',
  'open-duplicate-tag-sets',
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
        <button
          type="button"
          class="btn btn-outline-success btn-sm"
          :disabled="isBusy || selectedCount === 0"
          @click="$emit('open-wildcard-export')"
        >
          ワイルドカード出力 ({{ selectedCount }})
        </button>
        <button
          type="button"
          class="btn btn-success btn-sm"
          :disabled="isBusy || selectedCount === 0"
          @click="$emit('move-selected-images')"
        >
          ファイルを移動 ({{ selectedCount }})
        </button>
        <button
          type="button"
          class="btn btn-danger btn-sm"
          :disabled="isBusy || selectedCount === 0"
          @click="$emit('delete-selected-images')"
        >
          選択画像を削除 ({{ selectedCount }})
        </button>
        <button
          type="button"
          class="btn btn-outline-primary btn-sm"
          :disabled="isBusy"
          @click="$emit('import-prompt-tags')"
        >
          プロンプトの読み取り
        </button>
        <button
          type="button"
          class="btn btn-outline-secondary btn-sm"
          :disabled="isBusy"
          @click="$emit('open-duplicate-tag-sets')"
        >
          重複タグ構成の検索
        </button>
        <span class="text-secondary small d-none d-sm-inline">
          {{ appInfo?.version ? `v${appInfo.version}` : 'Vue + pywebview' }}
        </span>
      </div>
    </div>
  </header>
</template>
