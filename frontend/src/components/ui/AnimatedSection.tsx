import React from 'react'
import { useScrollReveal } from '../../hooks/useScrollReveal'

type AnimationType = 'fadeIn' | 'fadeInUp' | 'fadeInDown' | 'fadeInLeft' | 'fadeInRight' | 'scaleIn'

interface AnimatedSectionProps {
  children: React.ReactNode
  animation?: AnimationType
  delay?: number
  threshold?: number
  className?: string
  style?: React.CSSProperties
  as?: keyof React.JSX.IntrinsicElements
}

export default function AnimatedSection({
  children,
  animation = 'fadeInUp',
  delay = 0,
  threshold = 0.1,
  className = '',
  style,
  as: Tag = 'div',
}: AnimatedSectionProps) {
  const { ref, isRevealed } = useScrollReveal<HTMLDivElement>({ threshold, triggerOnce: true })

  const animationClass = isRevealed ? `animate-${animation}` : ''
  const delayClass = delay > 0 ? `delay-${Math.min(Math.round(delay * 10), 8)}` : ''

  return React.createElement(
    Tag as string,
    {
      ref: ref as React.Ref<HTMLDivElement>,
      className: `will-reveal ${animationClass} ${delayClass} ${className}`.trim(),
      style: {
        ...style,
        animationDelay: delay ? `${delay}s` : undefined,
      },
    },
    children
  )
}
