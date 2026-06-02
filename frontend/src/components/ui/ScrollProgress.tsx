import { useScrollProgress } from '../../hooks/useScrollReveal'

export default function ScrollProgress() {
  const progress = useScrollProgress()

  return (
    <div
      className="scroll-progress"
      style={{
        width: `${progress * 100}%`,
        opacity: progress > 0.01 ? 1 : 0,
        transition: 'opacity 0.2s ease',
      }}
    />
  )
}
