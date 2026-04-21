<script setup>
defineProps({
  status: {
    type: Object,
    required: true,
  },
})

defineEmits(['health-check'])
</script>

<template>
  <section>
    <div class="d-flex flex-column flex-lg-row justify-content-between gap-3 mb-4">
      <div>
        <h1 class="h3 mb-2">Sample</h1>
        <p class="text-secondary mb-0">
          追加画面を差し込むためのプレースホルダです。
        </p>
      </div>
      <button class="btn btn-primary align-self-start" type="button" @click="$emit('health-check')">
        <i class="bi bi-arrow-repeat me-1" aria-hidden="true"></i>
        API Call
      </button>
    </div>

    <div class="card">
      <div class="card-header bg-white fw-semibold">Status</div>
      <div class="card-body">
        <p class="mb-3">
          現在の状態は
          <span :class="`badge text-bg-${status.type}`">{{ status.message }}</span>
          です。
        </p>
        <div class="table-responsive">
          <table class="table table-sm align-middle mb-0">
            <thead>
              <tr>
                <th scope="col">Area</th>
                <th scope="col">Responsibility</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Vue</td>
                <td>画面表示、選択状態、API 呼び出し結果の描画</td>
              </tr>
              <tr>
                <td>Python</td>
                <td>ローカル処理、公開 API、業務ロジックの受け口</td>
              </tr>
              <tr>
                <td>pywebview</td>
                <td>デスクトップウィンドウと JavaScript API ブリッジ</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </section>
</template>

