<script setup>
defineProps({
  appInfo: {
    type: Object,
    default: null,
  },
  apiResult: {
    type: Object,
    default: null,
  },
})
</script>

<template>
  <section>
    <div class="d-flex flex-column flex-lg-row justify-content-between gap-3 mb-4">
      <div>
        <h1 class="h3 mb-2">Home</h1>
        <p class="text-secondary mb-0">
          共通レイアウトと Python API 接続を確認する初期画面です。
        </p>
      </div>
      <div class="alert alert-primary mb-0 py-2 px-3" role="status">
        <i class="bi bi-window-sidebar me-1" aria-hidden="true"></i>
        Header / Sidebar / Main / Footer
      </div>
    </div>

    <div class="row g-3">
      <div class="col-12 col-xl-5">
        <div class="card h-100">
          <div class="card-header bg-white fw-semibold">Application</div>
          <div class="card-body">
            <dl class="row mb-0">
              <dt class="col-sm-4">Name</dt>
              <dd class="col-sm-8">{{ appInfo?.name ?? '-' }}</dd>
              <dt class="col-sm-4">Version</dt>
              <dd class="col-sm-8">{{ appInfo?.version ?? '-' }}</dd>
              <dt class="col-sm-4">Description</dt>
              <dd class="col-sm-8">{{ appInfo?.description ?? '-' }}</dd>
            </dl>
          </div>
        </div>
      </div>

      <div class="col-12 col-xl-7">
        <div class="card h-100">
          <div class="card-header bg-white fw-semibold">Latest API Response</div>
          <div class="card-body">
            <pre class="response-view mb-0">{{ JSON.stringify(apiResult, null, 2) }}</pre>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

