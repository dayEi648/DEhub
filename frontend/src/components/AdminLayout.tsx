import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'

export default function AdminLayout() {
  return (
    <div className="admin-layout">
      <Sidebar />
      <main className="admin-layout__main">
        <Outlet />
      </main>
    </div>
  )
}
