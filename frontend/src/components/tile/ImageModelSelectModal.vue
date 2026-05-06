<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    required: true,
  },
  selectedModelName: {
    type: String,
    default: '',
  },
  models: {
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

const emit = defineEmits(['close', 'search', 'apply'])

const filterText = ref('')
const newModelName = ref('')
const workingSelectedModelName = ref('')

watch(
  () => props.show,
  (show) => {
    if (!show) {
      return
    }

    filterText.value = ''
    newModelName.value = ''
    workingSelectedModelName.value = props.selectedModelName || ''
    emit('search', { keyword: '' })
  }
)

function selectModel(modelName) {
  workingSelectedModelName.value = modelName || ''
}

function handleSearch() {
  emit('search', { keyword: filterText.value })
}

function handleApply() {
  const value = (newModelName.value || workingSelectedModelName.value || '').trim()
  emit('apply', value)
}
</script>

<template>
  <div v-if="show" class="modal-backdrop-shell" role="presentation">
    <div
      class="modal fade show d-block"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
    >
      <div class="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">モデル設定</h5>
            <button
              type="button"
              class="btn-close"
              aria-label="閉じる"
              @click="$emit('close')"
            ></button>
          </div>

          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label small fw-semibold" for="newModelName">
                新規モデル名
              </label>
              <input
                id="newModelName"
                v-model="newModelName"
                type="text"
                class="form-control form-control-sm"
                maxlength="512"
                placeholder="新規モデル名"
              />
            </div>

            <div class="input-group input-group-sm mb-2">
              <input
                v-model="filterText"
                type="text"
                class="form-control"
                placeholder="既存モデルを絞り込み"
                @keydown.enter.prevent="handleSearch"
              />
              <button type="button" class="btn btn-outline-secondary" @click="handleSearch">
                検索
              </button>
            </div>

            <div class="small text-muted mb-2">
              表示件数: {{ models.length }} / {{ totalCount }}
            </div>

            <div v-if="isLoading" class="text-muted">読み込み中...</div>
            <div v-else-if="externalMessage" class="alert alert-secondary mb-0">
              {{ externalMessage }}
            </div>
            <div v-else class="d-flex flex-wrap gap-2 model-select-badge-list">
              <button
                v-for="model in models"
                :key="model.name"
                type="button"
                class="btn btn-sm model-search-item"
                :class="workingSelectedModelName === model.name ? 'btn-info' : 'btn-outline-secondary'"
                :title="model.name"
                @click="selectModel(model.name)"
              >
                {{ model.name }}
                <span class="badge text-bg-light ms-1">{{ model.image_count }}</span>
              </button>
            </div>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn btn-secondary btn-sm" @click="$emit('close')">
              キャンセル
            </button>
            <button type="button" class="btn btn-primary btn-sm" @click="handleApply">
              選択
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade show"></div>
  </div>
</template>
