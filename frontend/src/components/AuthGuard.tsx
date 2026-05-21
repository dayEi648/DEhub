import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { isLoggedIn } from '../utils/auth'

interface AuthGuardProps {
  children: ReactNode
}

export default function AuthGuard({ children }: AuthGuardProps) {
  if (!isLoggedIn()) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}
