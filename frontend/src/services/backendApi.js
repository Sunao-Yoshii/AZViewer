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

export async function importSelectedItems(items) {
  return await callBackendApi('import_selected_items', { items })
}

export async function selectFilesDialog() {
  return await callBackendApi('select_files_dialog')
}

export async function selectFolderDialog() {
  return await callBackendApi('select_folder_dialog')
}

export async function searchImageFiles(payload) {
  return await callBackendApi('search_image_files', payload)
}

export async function updateImageFileDetail(payload) {
  return await callBackendApi('update_image_file_detail', payload)
}

export async function deleteImageFile(id) {
  return await callBackendApi('delete_image_file', { id })
}

export async function fetchLocalImage(path) {
  return await callBackendApi('fetchLocalImage', { path })
}

export async function fetchLocalImageThumb(id) {
  return await callBackendApi('fetchLocalImageThumb', { id })
}
