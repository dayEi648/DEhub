import { Routes, Route, Navigate } from 'react-router-dom'
import LogManagement from './LogManagement'
import UserManagement from './UserManagement'
import PlaceholderPage from './PlaceholderPage'
import OpenAPIKnowledgePage from './OpenAPIKnowledgePage'

export default function AdminDashboard() {
  return (
    <Routes>
      <Route path="logs" element={<LogManagement />} />
      <Route path="users" element={<UserManagement />} />
      <Route path="openapi-knowledge" element={<OpenAPIKnowledgePage />} />
      <Route path="content" element={<PlaceholderPage />} />
      <Route path="settings" element={<PlaceholderPage />} />
      <Route path="*" element={<Navigate to="/admin/logs" replace />} />
    </Routes>
  )
}
