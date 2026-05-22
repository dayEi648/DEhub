import type { ReactNode } from 'react'
import Sidebar from './Sidebar'

interface AdminLayoutProps {
  children: ReactNode
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  return (
    <div className="admin-layout">
      <Sidebar />
      <main className="admin-layout__main">
        {children}
      </main>
    </div>
  )
}
