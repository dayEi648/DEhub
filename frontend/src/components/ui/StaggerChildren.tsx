import React from 'react'
import { useScrollReveal } from '../../hooks/useScrollReveal'

type AnimationType = 'fadeIn' | 'fadeInUp' | 'fadeInDown' | 'scaleIn'

interface StaggerChildrenProps {
  children: React.ReactNode
  animation?: AnimationType
  staggerDelay?: number
  threshold?: number
  className?: string
  style?: React.CSSProperties
  childClassName?: string
  childStyle?: React.CSSProperties
}

export default function StaggerChildren({
  children,
  animation = 'fadeInUp',
  staggerDelay = 0.08,
  threshold = 0.05,
  className = '',
  style,
  childClassName = '',
  childStyle,
}: StaggerChildrenProps) {
  const { ref, isRevealed } = useScrollReveal<HTMLDivElement>({ threshold, triggerOnce: true })

  const childArray = React.Children.toArray(children)

  return (
    <div ref={ref} className={className} style={style}>
      {childArray.map((child, index) => (
        <div
          key={index}
          className={`will-reveal ${isRevealed ? `animate-${animation}` : ''} ${childClassName}`}
          style={{
            ...childStyle,
            animationDelay: isRevealed ? `${index * staggerDelay}s` : undefined,
          }}
        >
          {child}
        </div>
      ))}
    </div>
  )
}
