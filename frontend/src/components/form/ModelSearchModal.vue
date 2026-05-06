<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    required: true,
  },
  selectedModel: {
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

const emit = defineEmits(['close', 'search-models', 'apply'])

const filterText = ref('')
const workingSelectedModel = ref(null)

watch(
  () => props.show,
  (show) => {
    if (!show) {
      return
    }

    filterText.value = ''
    workingSelectedModel.value = props.selectedModel || null
    emit('search-models', { keyword: '' })
  }
)

function selectModel(modelName) {
  workingSelectedModel.value = modelName || null
}

function clearModel() {
  workingSelectedModel.value = null
}

function handleSearch() {
  emit('search-models', { keyword: filterText.value })
}

function handleApply() {
  emit('apply', workingSelectedModel.value)
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
            <h5 class="modal-title">モデル検索</h5>
            <button
              type="button"
              class="btn-close"
              aria-label="閉じる"
              @click="$emit('close')"
            ></button>
          </div>

          <div class="modal-body">
            <div class="mb-3">
              <div class="small text-muted mb-1">選択中モデル</div>
              <span v-if="workingSelectedModel" class="badge text-bg-info image-model-badge">
                {{ workingSelectedModel }}
              </span>
              <span v-else class="small text-muted">未指定</span>
            </div>

            <div class="input-group input-group-sm mb-2">
              <input
                v-model="filterText"
                type="text"
                class="form-control"
                placeholder="モデル名で絞り込み"
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
            <div v-else class="d-flex flex-wrap gap-2 model-search-badge-list">
              <button
                v-for="model in models"
                :key="model.name"
                type="button"
                class="btn btn-sm model-search-item"
                :class="workingSelectedModel === model.name ? 'btn-info' : 'btn-outline-secondary'"
                :title="model.name"
                @click="selectModel(model.name)"
              >
                {{ model.name }}
                <span class="badge text-bg-light ms-1">{{ model.image_count }}</span>
              </button>
            </div>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn btn-outline-danger btn-sm" @click="clearModel">
              解除
            </button>
            <button type="button" class="btn btn-secondary btn-sm" @click="$emit('close')">
              キャンセル
            </button>
            <button type="button" class="btn btn-primary btn-sm" @click="handleApply">
              OK
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade show"></div>
  </div>
</template>
