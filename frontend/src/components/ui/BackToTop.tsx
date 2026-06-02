import { ArrowUp } from 'lucide-react'
import { useBackToTop } from '../../hooks/useScrollReveal'

export default function BackToTop() {
  const { visible, scrollToTop } = useBackToTop(400)

  return (
    <button
      className={`back-to-top ${visible ? 'is-visible' : ''}`}
      onClick={scrollToTop}
      aria-label="回到顶部"
      title="回到顶部"
    >
      <ArrowUp size={18} />
    </button>
  )
}
