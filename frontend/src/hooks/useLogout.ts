import { useNavigate } from 'react-router-dom'
import { logout } from '../api/users'
import { clearAuth } from '../utils/auth'

export function useLogout() {
  const navigate = useNavigate()

  return async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token')
      await logout(refreshToken ? { refresh_token: refreshToken } : {})
    } catch {
      // ignore
    } finally {
      clearAuth()
      navigate('/login', { replace: true })
    }
  }
}
