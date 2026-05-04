function waitForNextApiCheck() {
  return new Promise((resolve) => {
    const finish = () => {
      window.clearTimeout(timerId)
      document.removeEventListener('pywebviewready', handleReady)
      resolve()
    }

    const timerId = window.setTimeout(finish, 50)

    function handleReady() {
      finish()
    }

    document.addEventListener('pywebviewready', handleReady, { once: true })
  })
}

function getCallableBackendApi(methodName) {
  const api = window.pywebview?.api
  if (!api || typeof api[methodName] !== 'function') {
    return null
  }

  return api
}

async function waitForPywebviewApi(methodName) {
  let api = getCallableBackendApi(methodName)
  while (!api) {
    await waitForNextApiCheck()
    api = getCallableBackendApi(methodName)
  }
  return api
}

export async function callBackendApi(methodName, ...args) {
  const api = await waitForPywebviewApi(methodName)

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

export async function deleteImageFilesWithPhysicalFiles(payload) {
  return await callBackendApi('delete_image_files_with_physical_files', payload)
}

export async function moveImageFilesToFolder(payload) {
  return await callBackendApi('move_image_files_to_folder', payload)
}

export async function fetchLocalImage(path) {
  return await callBackendApi('fetchLocalImage', { path })
}

export async function fetchLocalImageThumb(id) {
  return await callBackendApi('fetchLocalImageThumb', { id })
}

export async function fetchImageMetadata(path) {
  return await callBackendApi('fetch_image_metadata', { path })
}

export async function fetchTagsForSearch(payload = {}) {
  return await callBackendApi('fetch_tags_for_search', payload)
}

export async function fetchFoldersForSearch(payload = {}) {
  return await callBackendApi('fetch_folders_for_search', payload)
}

export async function fetchDuplicateTagSets(payload = {}) {
  return await callBackendApi('fetch_duplicate_tag_sets', payload)
}

export async function importPromptTags() {
  return await callBackendApi('import_prompt_tags', {})
}

export async function openContainingFolder(path) {
  return await callBackendApi('open_containing_folder', { path })
}
