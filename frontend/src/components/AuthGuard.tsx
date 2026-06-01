import { useEffect, useState } from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { getUser, isAuthenticated, clearAuth } from '../utils/auth'

interface AuthGuardProps {
  requireAdmin?: boolean
}

export default function AuthGuard({ requireAdmin = false }: AuthGuardProps) {
  const [unauthorized, setUnauthorized] = useState(false)
  const [authChecked, setAuthChecked] = useState(false)

  useEffect(() => {
    const handler = () => setUnauthorized(true)
    window.addEventListener('unauthorized', handler)
    return () => window.removeEventListener('unauthorized', handler)
  }, [])

  useEffect(() => {
    setAuthChecked(true)
  }, [])

  if (!authChecked) {
    return null
  }

  if (unauthorized) {
    clearAuth()
    return <Navigate to="/login" replace />
  }

  if (!isAuthenticated()) {
    clearAuth()
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
