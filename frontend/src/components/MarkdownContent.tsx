import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface MarkdownContentProps {
  content: string
}

export default function MarkdownContent({ content }: MarkdownContentProps) {
  return (
    <div className="markdown-body">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h1
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: 32,
                fontWeight: 400,
                lineHeight: 1.15,
                letterSpacing: '-0.5px',
                color: 'var(--color-ink)',
                margin: 'var(--spacing-xl) 0 var(--spacing-md)',
                paddingBottom: 'var(--spacing-sm)',
                borderBottom: '1px solid var(--color-hairline-soft)',
              }}
            >
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: 26,
                fontWeight: 400,
                lineHeight: 1.2,
                letterSpacing: '-0.3px',
                color: 'var(--color-ink)',
                margin: 'var(--spacing-xl) 0 var(--spacing-md)',
                paddingBottom: 'var(--spacing-sm)',
                borderBottom: '1px solid var(--color-hairline-soft)',
              }}
            >
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: 22,
                fontWeight: 400,
                lineHeight: 1.2,
                letterSpacing: '-0.3px',
                color: 'var(--color-ink)',
                margin: 'var(--spacing-lg) 0 var(--spacing-sm)',
              }}
            >
              {children}
            </h3>
          ),
          p: ({ children }) => (
            <p
              style={{
                fontSize: 16,
                lineHeight: 1.75,
                color: 'var(--color-body)',
                margin: '0 0 var(--spacing-md)',
              }}
            >
              {children}
            </p>
          ),
          a: ({ children, href }) => (
            <a
              href={href}
              style={{
                color: 'var(--color-primary)',
                textDecoration: 'none',
                borderBottom: '1px solid var(--color-primary)',
                transition: 'opacity 150ms ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.opacity = '0.8'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.opacity = '1'
              }}
            >
              {children}
            </a>
          ),
          ul: ({ children }) => (
            <ul
              style={{
                fontSize: 16,
                lineHeight: 1.75,
                color: 'var(--color-body)',
                margin: '0 0 var(--spacing-md)',
                paddingLeft: 'var(--spacing-xl)',
              }}
            >
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol
              style={{
                fontSize: 16,
                lineHeight: 1.75,
                color: 'var(--color-body)',
                margin: '0 0 var(--spacing-md)',
                paddingLeft: 'var(--spacing-xl)',
              }}
            >
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li style={{ marginBottom: 'var(--spacing-xs)' }}>{children}</li>
          ),
          blockquote: ({ children }) => (
            <blockquote
              style={{
                margin: 'var(--spacing-md) 0',
                padding: 'var(--spacing-md) var(--spacing-lg)',
                borderLeft: '3px solid var(--color-primary)',
                backgroundColor: 'var(--color-surface-soft)',
                borderRadius: '0 var(--rounded-sm) var(--rounded-sm) 0',
                color: 'var(--color-body-strong)',
                fontStyle: 'italic',
              }}
            >
              {children}
            </blockquote>
          ),
          code: ({ children, className }) => {
            const isInline = !className
            if (isInline) {
              return (
                <code
                  style={{
                    fontFamily: 'var(--font-code)',
                    fontSize: 14,
                    backgroundColor: 'var(--color-surface-soft)',
                    padding: '2px 6px',
                    borderRadius: 'var(--rounded-xs)',
                    color: 'var(--color-primary-active)',
                  }}
                >
                  {children}
                </code>
              )
            }
            return (
              <pre
                style={{
                  backgroundColor: 'var(--color-surface-dark)',
                  color: 'var(--color-on-dark)',
                  padding: 'var(--spacing-lg)',
                  borderRadius: 'var(--rounded-lg)',
                  overflowX: 'auto',
                  fontFamily: 'var(--font-code)',
                  fontSize: 14,
                  lineHeight: 1.6,
                  margin: 'var(--spacing-md) 0',
                }}
              >
                <code>{children}</code>
              </pre>
            )
          },
          hr: () => (
            <hr
              style={{
                border: 'none',
                borderTop: '1px solid var(--color-hairline-soft)',
                margin: 'var(--spacing-xl) 0',
              }}
            />
          ),
          img: ({ src, alt }) => (
            <img
              src={src}
              alt={alt}
              style={{
                maxWidth: '100%',
                borderRadius: 'var(--rounded-lg)',
                margin: 'var(--spacing-md) 0',
              }}
            />
          ),
          table: ({ children }) => (
            <div style={{ overflowX: 'auto', margin: 'var(--spacing-md) 0' }}>
              <table
                style={{
                  width: '100%',
                  borderCollapse: 'collapse',
                  fontSize: 14,
                  lineHeight: 1.6,
                }}
              >
                {children}
              </table>
            </div>
          ),
          th: ({ children }) => (
            <th
              style={{
                padding: 'var(--spacing-sm) var(--spacing-md)',
                backgroundColor: 'var(--color-surface-soft)',
                borderBottom: '2px solid var(--color-hairline)',
                textAlign: 'left',
                fontWeight: 600,
                color: 'var(--color-ink)',
              }}
            >
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td
              style={{
                padding: 'var(--spacing-sm) var(--spacing-md)',
                borderBottom: '1px solid var(--color-hairline-soft)',
                color: 'var(--color-body)',
              }}
            >
              {children}
            </td>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
