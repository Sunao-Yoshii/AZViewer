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

export async function bulkUpdateImageFileAttributes(payload) {
  return await callBackendApi('bulk_update_image_file_attributes', payload)
}

export async function moveImageFilesToFolder(payload) {
  return await callBackendApi('move_image_files_to_folder', payload)
}

export async function removeImageFilesFromCatalog(payload) {
  return await callBackendApi('remove_image_files_from_catalog', payload)
}

export async function moveImageFilesToTrash(payload) {
  return await callBackendApi('move_image_files_to_trash', payload)
}

export async function exportSelectedImageTags(payload) {
  return await callBackendApi('export_selected_image_tags', payload)
}

export async function importCaptionTags(payload) {
  return await callBackendApi('import_caption_tags', payload)
}

export async function bulkAddTags(payload) {
  return await callBackendApi('bulk_add_tags', payload)
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

export async function fetchModelsForSearch(payload = {}) {
  return await callBackendApi('fetch_models_for_search', payload)
}

export async function fetchTagsForMaintenance(payload = {}) {
  return await callBackendApi('fetch_tags_for_maintenance', payload)
}

export async function deleteTagMaster(id) {
  return await callBackendApi('delete_tag_master', { id })
}

export async function replaceTagMaster(payload) {
  return await callBackendApi('replace_tag_master', payload)
}

export async function deleteUnusedTags() {
  return await callBackendApi('delete_unused_tags', {})
}

export async function fetchModelsForMaintenance(payload = {}) {
  return await callBackendApi('fetch_models_for_maintenance', payload)
}

export async function deleteModelMaster(id) {
  return await callBackendApi('delete_model_master', { id })
}

export async function replaceModelMaster(payload) {
  return await callBackendApi('replace_model_master', payload)
}

export async function deleteUnusedModels() {
  return await callBackendApi('delete_unused_models', {})
}

export async function fetchDuplicateTagSets(payload = {}) {
  return await callBackendApi('fetch_duplicate_tag_sets', payload)
}

export async function importPromptTags() {
  return await callBackendApi('import_prompt_tags', {})
}

export async function exportWildcardText(payload) {
  return await callBackendApi('export_wildcard_text', payload)
}

export async function openContainingFolder(path) {
  return await callBackendApi('open_containing_folder', { path })
}
