import { ref } from 'vue'

export function useAppStatus() {
  const status = ref({
    type: 'secondary',
    message: '起動準備中',
  })

  function setStatus(type, message) {
    status.value = { type, message }
  }

  return {
    status,
    setStatus,
  }
}
