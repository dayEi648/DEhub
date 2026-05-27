import { useState } from 'react'
import { Send } from 'lucide-react'
import { usePasteImageUpload } from '../hooks/usePasteImageUpload'

interface ReplyEditorProps {
  placeholder: string
  onSubmit: (content: string) => void | Promise<void>
  onCancel?: () => void
  submitText?: string
  pasteScene?: string
}

export default function ReplyEditor({
  placeholder,
  onSubmit,
  onCancel,
  submitText = '回复',
  pasteScene,
}: ReplyEditorProps) {
  const [value, setValue] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { handlePaste } = usePasteImageUpload(pasteScene || 'generic')

  const handleSubmit = async () => {
    if (!value.trim()) return
    setSubmitting(true)
    await onSubmit(value.trim())
    setSubmitting(false)
    setValue('')
  }

  const pasteProps = pasteScene
    ? {
        onPaste: (e: React.ClipboardEvent<HTMLTextAreaElement>) =>
          handlePaste(e, (md, s, end) => setValue((prev) => prev.slice(0, s) + md + prev.slice(end))),
      }
    : {}

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)', marginTop: 'var(--spacing-sm)' }}>
      <textarea
        placeholder={placeholder}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        {...pasteProps}
        style={{
          width: '100%',
          minHeight: 60,
          padding: 'var(--spacing-sm)',
          borderRadius: 'var(--rounded-md)',
          border: '1px solid var(--color-hairline)',
          backgroundColor: 'var(--color-canvas)',
          fontSize: 14,
          lineHeight: 1.6,
          color: 'var(--color-ink)',
          resize: 'vertical',
          outline: 'none',
          fontFamily: 'var(--font-body)',
        }}
      />
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--spacing-sm)' }}>
        {onCancel && (
          <button
            onClick={onCancel}
            style={{
              padding: '8px 16px',
              backgroundColor: 'transparent',
              color: 'var(--color-muted)',
              borderRadius: 'var(--rounded-md)',
              fontSize: 13,
              fontWeight: 500,
              border: '1px solid var(--color-hairline)',
              cursor: 'pointer',
            }}
          >
            取消
          </button>
        )}
        <button
          onClick={handleSubmit}
          disabled={submitting || !value.trim()}
          style={{
            padding: '8px 16px',
            backgroundColor: !value.trim() ? 'var(--color-primary-disabled)' : 'var(--color-primary)',
            color: !value.trim() ? 'var(--color-muted)' : 'var(--color-on-primary)',
            borderRadius: 'var(--rounded-md)',
            fontSize: 13,
            fontWeight: 500,
            border: 'none',
            cursor: !value.trim() ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 4,
          }}
        >
          <Send size={12} />
          {submitting ? '发送中...' : submitText}
        </button>
      </div>
    </div>
  )
}
