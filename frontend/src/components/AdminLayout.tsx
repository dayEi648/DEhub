import type { ReactNode } from 'react'
import Sidebar from './Sidebar'

interface AdminLayoutProps {
  children: ReactNode
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  return (
    <div style={{ display: 'flex', minHeight: '100vh', width: '100%' }}>
      <Sidebar />
      <main
        style={{
          marginLeft: 240,
          flex: 1,
          width: 'calc(100% - 240px)',
          backgroundColor: 'var(--color-canvas)',
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {children}
      </main>
    </div>
  )
}
