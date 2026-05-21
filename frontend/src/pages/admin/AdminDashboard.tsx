import { Routes, Route } from 'react-router-dom'
import LogManagement from './LogManagement'
import UserManagement from './UserManagement'
import PlaceholderPage from './PlaceholderPage'

export default function AdminDashboard() {
  return (
    <Routes>
      <Route path="logs" element={<LogManagement />} />
      <Route path="users" element={<UserManagement />} />
      <Route path="content" element={<PlaceholderPage />} />
      <Route path="settings" element={<PlaceholderPage />} />
      <Route path="*" element={<PlaceholderPage />} />
    </Routes>
  )
}
