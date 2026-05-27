import { useEffect, useState } from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { getUser, isLoggedIn } from '../utils/auth'

interface AuthGuardProps {
  requireAdmin?: boolean
}

export default function AuthGuard({ requireAdmin = false }: AuthGuardProps) {
  const [unauthorized, setUnauthorized] = useState(false)

  useEffect(() => {
    const handler = () => setUnauthorized(true)
    window.addEventListener('unauthorized', handler)
    return () => window.removeEventListener('unauthorized', handler)
  }, [])

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
  return <Outlet />
}
