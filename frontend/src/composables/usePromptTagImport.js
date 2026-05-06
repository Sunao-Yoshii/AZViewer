import { ref } from 'vue'
import { importPromptTags } from '../services/backendApi'

const CONFIRM_MESSAGE = [
  '画像メタデータから Stable Diffusion WebUI のプロンプト情報とモデル情報を読み取ります。',
  'タグは未登録画像のみ、モデルは未設定画像のみ対象です。',
  '実行しますか？',
].join('\n')

function buildSuccessMessage(data) {
  return [
    'プロンプト情報の読み取りが完了しました。',
    `タグ対象: ${data.targetCount ?? 0} 件 / タグ登録: ${data.taggedCount ?? 0} 件 / タグスキップ: ${data.skippedCount ?? 0} 件 / タグ失敗: ${data.failedCount ?? 0} 件`,
    `モデル対象: ${data.modelTargetCount ?? 0} 件 / モデル登録: ${data.modelLinkedCount ?? 0} 件 / モデルスキップ: ${data.modelSkippedCount ?? 0} 件 / モデル失敗: ${data.modelFailedCount ?? 0} 件`,
  ].join('\n')
}

export function usePromptTagImport({ pushToast, loading, refresh }) {
  const isImporting = ref(false)

  async function handleImportPromptTags() {
    if (!window.confirm(CONFIRM_MESSAGE)) {
      return
    }

    isImporting.value = true
    loading.showLoading(
      'プロンプト情報を読み取り中',
      '画像メタデータからタグを一括登録しています...',
    )

    try {
      const result = await importPromptTags()
      if (!result.success) {
        pushToast({
          type: 'error',
          message: result.message || 'プロンプト情報の読み取り中にエラーが発生しました。',
        })
        return
      }

      const data = result.data ?? {}
      pushToast({
        type: 'success',
        message: buildSuccessMessage(data),
      })

      if ((data.failedCount ?? 0) > 0 || (data.modelFailedCount ?? 0) > 0) {
        pushToast({
          type: 'warning',
          message: `一部画像の処理に失敗しました。タグ失敗: ${data.failedCount ?? 0} 件 / モデル失敗: ${data.modelFailedCount ?? 0} 件`,
        })
      }

      await refresh()
    } finally {
      isImporting.value = false
      loading.hideLoading()
    }
  }

  return {
    isImporting,
    handleImportPromptTags,
  }
}
