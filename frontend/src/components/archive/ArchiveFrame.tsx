import type { ReactNode } from 'react';

interface ArchiveFrameProps {
  children: ReactNode;
}

/**
 * 档案柜框架
 * 提供档案柜风格的整体布局：顶部栏 + 左侧边栏 + 内容区域 + 底部栏
 */
export default function ArchiveFrame({ children }: ArchiveFrameProps) {
  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: '#0D0A07' }}>
      {/* 顶部框架 */}
      <header
        className="fixed top-0 left-0 right-0 z-50 flex items-center px-4 sm:px-6 lg:px-8"
        style={{
          height: 80,
          background: 'linear-gradient(180deg, #F5A623 0%, #FAA622 50%, #F5A623 100%)',
          borderBottom: '2px solid #1A1612',
        }}
      >
        {/* 螺丝装饰 - 左上角 */}
        <div
          className="absolute top-2 left-2 w-1 h-1 rounded-full"
          style={{ backgroundColor: '#1A1612' }}
        />
        {/* 螺丝装饰 - 右上角 */}
        <div
          className="absolute top-2 right-2 w-1 h-1 rounded-full"
          style={{ backgroundColor: '#1A1612' }}
        />
        {children}
      </header>

      {/* 左侧边栏 */}
      <aside
        className="fixed left-0 z-40 hidden lg:flex flex-col"
        style={{
          top: 80,
          width: 280,
          height: 'calc(100vh - 120px)',
          background: 'linear-gradient(90deg, #F5A623 0%, #FAA622 50%, #F5A623 100%)',
          borderRight: '2px solid #1A1612',
        }}
      >
        {/* 螺丝装饰 - 左下角 */}
        <div
          className="absolute bottom-2 left-2 w-1 h-1 rounded-full"
          style={{ backgroundColor: '#1A1612' }}
        />
        {/* 螺丝装饰 - 右下角 */}
        <div
          className="absolute bottom-2 right-2 w-1 h-1 rounded-full"
          style={{ backgroundColor: '#1A1612' }}
        />
      </aside>

      {/* 底部框架 */}
      <footer
        className="fixed bottom-0 left-0 right-0 z-50 flex items-center justify-between px-4 sm:px-6 lg:px-8"
        style={{
          height: 40,
          background: 'linear-gradient(180deg, #F5A623 0%, #FAA622 50%, #F5A623 100%)',
          borderTop: '2px solid #1A1612',
        }}
      >
        {/* 螺丝装饰 - 左下角 */}
        <div
          className="absolute top-2 left-2 w-1 h-1 rounded-full"
          style={{ backgroundColor: '#1A1612' }}
        />
        {/* 螺丝装饰 - 右下角 */}
        <div
          className="absolute top-2 right-2 w-1 h-1 rounded-full"
          style={{ backgroundColor: '#1A1612' }}
        />
      </footer>
    </div>
  );
}
