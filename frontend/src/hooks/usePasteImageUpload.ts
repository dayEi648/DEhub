import { useCallback } from 'react'
import { toast } from 'sonner'
import { uploadImage } from '../api/upload'
import { validateImageFile } from '../utils/upload'
import { parseErrorMessage } from '../utils/error'

export function usePasteImageUpload(scene: string) {
  const handlePaste = useCallback(
    async (
      e: React.ClipboardEvent<HTMLTextAreaElement>,
      insert: (markdown: string, start: number, end: number) => void,
    ) => {
      const items = e.clipboardData.items
      let imageFile: File | null = null
      for (let i = 0; i < items.length; i++) {
        const item = items[i]
        if (item.type.startsWith('image/')) {
          const file = item.getAsFile()
          if (file) {
            imageFile = file
            break
          }
        }
      }
      if (!imageFile) return

      e.preventDefault()
      const error = validateImageFile(imageFile)
      if (error) {
        toast.error(error)
        return
      }

      const textarea = e.currentTarget
      const start = textarea.selectionStart
      const end = textarea.selectionEnd

      await toast.promise(
        uploadImage(imageFile, scene).then((res) => {
          const imageUrl = res.data.url
          const alt = imageFile!.name.replace(/\.[^/.]+$/, '') || '图片'
          const markdown = `![${alt}](${imageUrl})`
          insert(markdown, start, end)
          setTimeout(() => {
            textarea.selectionStart = textarea.selectionEnd = start + markdown.length
            textarea.focus()
          }, 0)
        }),
        {
          loading: '正在上传图片...',
          success: '图片上传成功',
          error: (err: unknown) => parseErrorMessage(err, '图片上传失败'),
        },
      )
    },
    [scene],
  )

  return { handlePaste }
}
