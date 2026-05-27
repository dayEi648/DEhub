import { User } from 'lucide-react'

interface UserAvatarProps {
  url: string | null
  name?: string
  size?: number
  iconSize?: number
  style?: React.CSSProperties
}

export default function UserAvatar({ url, name = '', size = 32, iconSize = 14, style }: UserAvatarProps) {
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: 'var(--rounded-full)',
        backgroundColor: 'var(--color-surface-card)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'var(--color-primary)',
        flexShrink: 0,
        overflow: 'hidden',
        fontSize: iconSize,
        ...style,
      }}
    >
      {url ? (
        <img src={url} alt={name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
      ) : (
        <User size={iconSize} />
      )}
    </div>
  )
}
