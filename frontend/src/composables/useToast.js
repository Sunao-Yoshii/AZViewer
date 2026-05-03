import { ref } from 'vue'

const toasts = ref([])

export function useToast() {
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
        type: normalizeToastType(notification.type),
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

function normalizeToastType(type) {
  if (type === 'error') {
    return 'danger'
  }
  if (['danger', 'warning', 'success', 'info'].includes(type)) {
    return type
  }
  return 'info'
}
