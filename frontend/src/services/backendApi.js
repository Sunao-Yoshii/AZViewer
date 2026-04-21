function createUnavailableResponse(methodName) {
  return {
    success: false,
    message: `Python API is not available: ${methodName}`,
    data: null,
  }
}

function waitForPywebviewApi(timeoutMs = 1500) {
  if (window.pywebview?.api) {
    return Promise.resolve(window.pywebview.api)
  }

  return new Promise((resolve) => {
    const timerId = window.setTimeout(() => {
      document.removeEventListener('pywebviewready', handleReady)
      resolve(null)
    }, timeoutMs)

    function handleReady() {
      window.clearTimeout(timerId)
      resolve(window.pywebview?.api ?? null)
    }

    document.addEventListener('pywebviewready', handleReady, { once: true })
  })
}

export async function callBackendApi(methodName, ...args) {
  const api = await waitForPywebviewApi()

  if (!api || typeof api[methodName] !== 'function') {
    return createUnavailableResponse(methodName)
  }

  try {
    return await api[methodName](...args)
  } catch (error) {
    return {
      success: false,
      message: error instanceof Error ? error.message : String(error),
      data: null,
    }
  }
}
