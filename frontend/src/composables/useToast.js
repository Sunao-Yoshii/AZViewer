import { ref } from 'vue'

export function useToast() {
  const toasts = ref([])

  function removeToast(id) {
    toasts.value = toasts.value.filter((toast) => toast.id !== id)
  }

  function pushToast(notification) {
    if (!notification?.message) {
      return
    }

    const id = `${Date.now()}-${Math.random().toString(16).slice(2)}`
    toasts.value = [
      ...toasts.value,
      {
        id,
        type: notification.type === 'error' ? 'danger' : 'info',
        title: notification.title ?? '',
        message: notification.message,
      },
    ]
    window.setTimeout(() => removeToast(id), 6000)
  }

  return {
    toasts,
    pushToast,
    removeToast,
  }
}
