import { reactive, unref } from 'vue'
import { exportWildcardText } from '../services/backendApi'

function createWildcardExportModal() {
  return {
    show: false,
    exportMode: 'create',
    selectedIds: [],
    sourceItems: [],
    tagItems: [],
    previewText: '',
    outputLineCount: 0,
    isSaving: false,
  }
}

function buildTagItems(sourceItems) {
  const countMap = new Map()

  for (const item of sourceItems) {
    const uniqueTags = [...new Set(item.tags ?? [])]
    for (const tag of uniqueTags) {
      countMap.set(tag, (countMap.get(tag) ?? 0) + 1)
    }
  }

  return [...countMap.entries()]
    .map(([name, count]) => ({
      name,
      count,
      enabled: true,
    }))
    .sort((a, b) => {
      if (b.count !== a.count) {
        return b.count - a.count
      }
      return a.name.localeCompare(b.name)
    })
}

function buildWildcardPreview(sourceItems, tagItems) {
  const enabledTagSet = new Set(
    tagItems
      .filter((tag) => tag.enabled)
      .map((tag) => tag.name)
  )
  const lines = []

  for (const item of sourceItems) {
    const tags = (item.tags ?? []).filter((tag) => enabledTagSet.has(tag))
    if (tags.length > 0) {
      lines.push(tags.join(', '))
    }
  }

  return {
    text: lines.join('\r\n'),
    lineCount: lines.length,
  }
}

export function useWildcardExport({ pushToast, clearSelection }) {
  const wildcardExportModal = reactive(createWildcardExportModal())

  function openWildcardExportModal({ ids, currentItems }) {
    const targetIds = [...(ids ?? [])]
    if (targetIds.length === 0) {
      pushToast({
        type: 'warning',
        message: 'ワイルドカード出力する画像を選択してください。',
      })
      return
    }

    const sourceItems = collectSourceItems(targetIds, currentItems)
    if (sourceItems.length === 0) {
      pushToast({
        type: 'warning',
        message: 'ワイルドカード出力する画像を確認できませんでした。',
      })
      return
    }

    Object.assign(wildcardExportModal, createWildcardExportModal(), {
      selectedIds: targetIds,
      sourceItems,
      tagItems: buildTagItems(sourceItems),
    })
    refreshWildcardPreview()
    if (wildcardExportModal.tagItems.length === 0) {
      pushToast({
        type: 'warning',
        message: '選択画像に出力可能なタグがありません。',
      })
    }
    wildcardExportModal.show = true
  }

  function closeWildcardExportModal() {
    Object.assign(wildcardExportModal, createWildcardExportModal())
  }

  function changeWildcardExportMode(mode) {
    if (!['create', 'append'].includes(mode)) {
      return
    }
    wildcardExportModal.exportMode = mode
  }

  function toggleWildcardExportTag(tagName) {
    const tag = wildcardExportModal.tagItems.find((item) => item.name === tagName)
    if (!tag) {
      return
    }

    tag.enabled = !tag.enabled
    refreshWildcardPreview()
  }

  async function saveWildcardExport() {
    const text = wildcardExportModal.previewText
    if (!text) {
      pushToast({
        type: 'warning',
        message: '出力対象のタグがありません。',
      })
      return
    }

    wildcardExportModal.isSaving = true
    try {
      const result = await exportWildcardText({
        mode: wildcardExportModal.exportMode,
        text,
      })
      if (!result?.success) {
        handleWildcardExportFailure(result)
        return
      }

      pushWildcardExportSuccess(result)
      clearSelection?.()
      closeWildcardExportModal()
    } catch {
      pushToast({
        type: 'danger',
        message: 'ワイルドカード出力に失敗しました。',
      })
    } finally {
      wildcardExportModal.isSaving = false
    }
  }

  function refreshWildcardPreview() {
    const result = buildWildcardPreview(
      wildcardExportModal.sourceItems,
      wildcardExportModal.tagItems
    )
    wildcardExportModal.previewText = result.text
    wildcardExportModal.outputLineCount = result.lineCount
  }

  function collectSourceItems(targetIds, currentItems) {
    const selectedIdSet = new Set(targetIds)
    return normalizeCurrentItems(currentItems)
      .filter((item) => selectedIdSet.has(item.id))
      .map((item) => ({
        id: item.id,
        filename: item.filename,
        tags: [...(item.tags ?? [])],
      }))
  }

  function normalizeCurrentItems(value) {
    const currentValue = unref(value)
    if (Array.isArray(currentValue)) {
      return currentValue
    }
    if (Array.isArray(currentValue?.items)) {
      return currentValue.items
    }
    return []
  }

  function handleWildcardExportFailure(result) {
    if (result?.data?.cancelled) {
      return
    }

    pushToast({
      type: 'danger',
      message: result?.message || 'ワイルドカード出力に失敗しました。',
    })
  }

  function pushWildcardExportSuccess(result) {
    const data = result.data ?? {}
    pushToast({
      type: 'success',
      message: `ワイルドカードを出力しました。出力行: ${data.lineCount ?? wildcardExportModal.outputLineCount} 件`,
    })
  }

  return {
    wildcardExportModal,
    openWildcardExportModal,
    closeWildcardExportModal,
    changeWildcardExportMode,
    toggleWildcardExportTag,
    saveWildcardExport,
  }
}
