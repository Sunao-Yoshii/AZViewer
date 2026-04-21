<script setup>
import { computed, onMounted, ref } from 'vue'
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
const status = ref({
  type: 'secondary',
  message: '起動準備中',
})

const activeComponent = computed(() => pages[activePageKey.value] ?? Home)

function setStatus(type, message) {
  status.value = { type, message }
}

async function loadInitialData() {
  setStatus('info', 'Python API に接続中')

  const initResult = await callBackendApi('initialize')
  apiResult.value = initResult

  if (!initResult.success) {
    setStatus('warning', initResult.message)
    return
  }

  const [appInfoResult, menuResult] = await Promise.all([
    callBackendApi('get_app_info'),
    callBackendApi('get_menu_definitions'),
  ])

  apiResult.value = appInfoResult

  if (appInfoResult.success) {
    appInfo.value = appInfoResult.data
  }

  if (menuResult.success && Array.isArray(menuResult.data)) {
    menus.value = menuResult.data
  }

  setStatus('success', 'Python API 接続済み')
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
</template>

