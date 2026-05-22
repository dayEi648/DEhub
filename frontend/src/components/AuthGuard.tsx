import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { getUser, isLoggedIn } from '../utils/auth'

interface AuthGuardProps {
  children: ReactNode
  requireAdmin?: boolean
}

export default function AuthGuard({ children, requireAdmin = false }: AuthGuardProps) {
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
