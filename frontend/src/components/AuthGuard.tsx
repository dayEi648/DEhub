import { useEffect, useState, type ReactNode } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { getUser, isLoggedIn } from '../utils/auth'

interface AuthGuardProps {
  children: ReactNode
  requireAdmin?: boolean
}

export default function AuthGuard({ children, requireAdmin = false }: AuthGuardProps) {
  const navigate = useNavigate()
  const [unauthorized, setUnauthorized] = useState(false)

  useEffect(() => {
    const handler = () => setUnauthorized(true)
    window.addEventListener('unauthorized', handler)
    return () => window.removeEventListener('unauthorized', handler)
  }, [navigate])

  if (unauthorized) {
    return <Navigate to="/login" replace />
  }

  if (!isLoggedIn()) {
    return <Navigate to="/login" replace />
  }
  if (requireAdmin) {
    const user = getUser()
    if (!user || (user.permission ?? 0) < 1) {
      return <Navigate to="/" replace />
    }
  }
  return <>{children}</>
}
