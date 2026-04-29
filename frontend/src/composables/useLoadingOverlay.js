import { reactive } from 'vue'

export function useLoadingOverlay() {
  const loadingOverlay = reactive({
    show: false,
    title: '',
    message: '',
  })

  function showLoading(title, message) {
    loadingOverlay.show = true
    loadingOverlay.title = title
    loadingOverlay.message = message
  }

  function hideLoading() {
    loadingOverlay.show = false
  }

  async function withLoading(title, message, task) {
    showLoading(title, message)
    try {
      return await task()
    } finally {
      hideLoading()
    }
  }

  return {
    loadingOverlay,
    showLoading,
    hideLoading,
    withLoading,
  }
}
