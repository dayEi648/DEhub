import { Routes, Route, Navigate } from 'react-router-dom'
import LogManagement from './LogManagement'
import AgentMonitoringPage from './AgentMonitoringPage'
import AgentTraceDetailPage from './AgentTraceDetailPage'
import AgentMonitoringDashboard from './AgentMonitoringDashboard'
import UserManagement from './UserManagement'
import OpenAPIKnowledgePage from './OpenAPIKnowledgePage'

export default function AdminDashboard() {
  return (
    <Routes>
      <Route path="logs" element={<LogManagement />} />
      {/* 注意：具体路由必须放在动态参数路由之前 */}
      <Route path="agent-monitoring/dashboard" element={<AgentMonitoringDashboard />} />
      <Route path="agent-monitoring/:traceId" element={<AgentTraceDetailPage />} />
      <Route path="agent-monitoring" element={<AgentMonitoringPage />} />
      <Route path="users" element={<UserManagement />} />
      <Route path="openapi-knowledge" element={<OpenAPIKnowledgePage />} />
      <Route path="*" element={<Navigate to="/admin/logs" replace />} />
    </Routes>
  )
}
