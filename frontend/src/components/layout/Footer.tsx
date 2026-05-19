import ColorBarStrip from '../effects/ColorBarStrip';

export default function Footer() {
  return (
    <footer className="relative py-8 px-4 sm:px-8 lg:px-14">
      <div className="max-w-5xl mx-auto">
        <ColorBarStrip height={2} className="mb-6" />

        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          {/* 左侧标识 */}
          <div className="flex items-center gap-3">
            <div
              className="chamfer-sm px-2 py-0.5"
              style={{ backgroundColor: '#F5A623' }}
            >
              <span
                className="text-xs font-black"
                style={{ color: '#2A2118', fontFamily: 'var(--font-display)' }}
              >
                DE
              </span>
            </div>
            <span
              className="text-xs opacity-40 tracking-wider"
              style={{ fontFamily: 'var(--font-mono)' }}
            >
              PERSONAL DEV SPACE
            </span>
          </div>

          {/* 右侧信息 */}
          <div className="flex items-center gap-4">
            <span
              className="text-[10px] opacity-30 tracking-wider"
              style={{ fontFamily: 'var(--font-mono)' }}
            >
              BUILT WITH REACT + FASTAPI
            </span>
            <div className="w-1 h-1 rotate-45 opacity-30" style={{ backgroundColor: '#F5A623' }} />
            <span
              className="text-[10px] opacity-30 tracking-wider"
              style={{ fontFamily: 'var(--font-mono)' }}
            >
              {new Date().getFullYear()}
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
