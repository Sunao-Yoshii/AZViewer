<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import LoadingOverlay from './components/common/LoadingOverlay.vue'
import MainLayout from './components/layout/MainLayout.vue'
import Home from './pages/Home.vue'
import SamplePage from './pages/SamplePage.vue'
import { callBackendApi } from './services/backendApi'

const pages = {
  home: Home,
  sample: SamplePage,
}

const fallbackMenus = [
  { key: 'home', label: 'Home', description: '基盤の概要とアプリ情報を表示します。' },
  { key: 'sample', label: 'Sample', description: '今後の機能追加用プレースホルダです。' },
]

const activePageKey = ref('home')
const menus = ref(fallbackMenus)
const appInfo = ref(null)
const apiResult = ref(null)
const startupNotification = ref(null)
const toasts = ref([])
const isStartupLocked = ref(false)
const startupOverlayMessage = ref('起動処理を完了しています。しばらくお待ちください。')
const status = ref({
  type: 'secondary',
  message: '起動準備中',
})

const activeComponent = computed(() => pages[activePageKey.value] ?? Home)

function setStatus(type, message) {
  status.value = { type, message }
}

function showToast(notification) {
  if (!notification?.message) {
    return
  }

  const id = `${Date.now()}-${Math.random().toString(16).slice(2)}`
  const item = {
    id,
    type: notification.type === 'error' ? 'danger' : 'info',
    title: notification.title ?? '',
    message: notification.message,
  }

  toasts.value = [...toasts.value, item]
  window.setTimeout(() => {
    toasts.value = toasts.value.filter((toast) => toast.id !== id)
  }, 6000)
}

function waitForNextPaint() {
  return new Promise((resolve) => {
    window.requestAnimationFrame(() => resolve())
  })
}

async function loadInitialData() {
  setStatus('info', 'Python API に接続中')
  isStartupLocked.value = true
  startupOverlayMessage.value = 'ファイル状態確認中です...'
  await nextTick()
  await waitForNextPaint()

  try {
    const initResult = await callBackendApi('initialize')
    apiResult.value = initResult

    if (!initResult.success) {
      setStatus('warning', initResult.message)
      startupNotification.value = {
        type: 'error',
        message: 'ファイル状態確認の実行中にエラーが発生しました',
      }
      return
    }

    const appData = initResult.data ?? {}
    appInfo.value = appData.appInfo ?? null
    if (Array.isArray(appData.menus)) {
      menus.value = appData.menus
    }
    startupNotification.value = appData.startupNotification ?? null

    setStatus('success', '起動処理が完了しました')
  } finally {
    isStartupLocked.value = false
  }

  if (startupNotification.value) {
    showToast(startupNotification.value)
  }
}

async function runHealthCheck() {
  setStatus('info', 'ヘルスチェック実行中')
  const result = await callBackendApi('health_check')
  apiResult.value = result
  setStatus(result.success ? 'success' : 'danger', result.message)
}

function changePage(pageKey) {
  activePageKey.value = pageKey
}

onMounted(loadInitialData)
</script>

<template>
  <MainLayout
    :app-info="appInfo"
    :menus="menus"
    :active-page-key="activePageKey"
    :status="status"
    @change-page="changePage"
    @health-check="runHealthCheck"
  >
    <component
      :is="activeComponent"
      :app-info="appInfo"
      :api-result="apiResult"
      :status="status"
      @health-check="runHealthCheck"
    />
  </MainLayout>
  <LoadingOverlay
    :show="isStartupLocked"
    title="ファイル状態確認中です..."
    :message="startupOverlayMessage"
  />
  <div class="toast-stack" aria-live="polite" aria-atomic="true">
    <div
      v-for="toast in toasts"
      :key="toast.id"
      class="toast-card shadow-sm"
      :class="`toast-card-${toast.type}`"
      role="status"
    >
      <p v-if="toast.title" class="toast-card-title mb-1">{{ toast.title }}</p>
      <p class="mb-0">{{ toast.message }}</p>
    </div>
  </div>
</template>
