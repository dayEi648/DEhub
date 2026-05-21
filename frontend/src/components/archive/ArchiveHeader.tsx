import { useNavigate } from 'react-router-dom';

interface ArchiveHeaderProps {
  totalFiles?: number;
  fileNumber?: string;
  mode?: 'list' | 'detail';
  backPath?: string;
}

/**
 * 档案柜顶部信息栏
 * 显示返回按钮、档案柜标识、文件计数、信号强度
 */
export default function ArchiveHeader({
  totalFiles = 0,
  fileNumber,
  mode = 'list',
  backPath,
}: ArchiveHeaderProps) {
  const navigate = useNavigate();

  const handleBack = () => {
    if (backPath) {
      navigate(backPath);
    } else {
      navigate(-1);
    }
  };

  return (
    <>
      {/* 左侧：返回按钮 + 档案柜标识 */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleBack}
          className="text-[11px] tracking-wider font-black px-3 py-1 transition-all duration-150 hover:brightness-110"
          style={{
            color: '#1A1612',
            fontFamily: 'var(--font-mono)',
            backgroundColor: 'rgba(26, 22, 18, 0.1)',
          }}
          data-cursor-hover
        >
          {backPath === '/' ? '← 首页' : '← 返回'}
        </button>
        <div className="w-px h-5 bg-[#1A1612]/20 hidden sm:block" />
        <div className="w-2 h-2 rotate-45" style={{ backgroundColor: '#1A1612' }} />
        <span
          className="text-[12px] tracking-[0.35em] font-black"
          style={{ color: '#1A1612', fontFamily: 'var(--font-display)' }}
        >
          档案柜
        </span>
      </div>

      {/* 右侧：文件计数 / 文件编号 + 信号强度 */}
      <div className="flex items-center gap-4">
        {mode === 'detail' && fileNumber ? (
          <span
            className="text-[10px] tracking-wider font-bold hidden sm:block"
            style={{ color: '#1A1612', fontFamily: 'var(--font-mono)' }}
          >
            档案: {fileNumber}
          </span>
        ) : (
          <span
            className="text-[10px] tracking-wider font-bold hidden sm:block"
            style={{ color: '#1A1612', fontFamily: 'var(--font-mono)' }}
          >
            {totalFiles} 份档案
          </span>
        )}
        <div className="flex items-center gap-1">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="w-1.5 h-1.5 rounded-full"
              style={{
                backgroundColor: '#1A1612',
                opacity: i <= 4 ? 1 : 0.3,
              }}
            />
          ))}
          <span
            className="text-[9px] tracking-wider ml-1 hidden sm:block"
            style={{ color: '#1A1612', fontFamily: 'var(--font-mono)', opacity: 0.7 }}
          >
            信号强
          </span>
        </div>
      </div>
    </>
  );
}
