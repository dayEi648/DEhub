import { useState } from 'react';
import { motion } from 'framer-motion';

interface ArchiveSidebarProps {
  totalFiles: number;
  searchType: 'title' | 'tag';
  sortBy: 'latest' | 'hot';
  onSearch: (query: string, type: 'title' | 'tag') => void;
  onSortChange: (sort: 'latest' | 'hot') => void;
}

/**
 * 档案柜左侧边栏（控制面板）
 * 承载搜索、排序、统计功能
 */
export default function ArchiveSidebar({
  totalFiles,
  searchType,
  sortBy,
  onSearch,
  onSortChange,
}: ArchiveSidebarProps) {
  const [inputValue, setInputValue] = useState('');
  const [localSearchType, setLocalSearchType] = useState<'title' | 'tag'>(searchType);

  const handleSearch = () => {
    onSearch(inputValue.trim(), localSearchType);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="flex flex-col h-full p-4 overflow-y-auto">
      {/* 1. 档案柜标识区 */}
      <div className="mb-6" style={{ height: 120 }}>
        <div className="flex items-start gap-2">
          {/* 标签槽装饰 */}
          <div className="w-2 h-16 mt-1" style={{ backgroundColor: '#1A1612' }} />
          <div>
            <h1
              className="text-[28px] font-black leading-tight"
              style={{ color: '#1A1612', fontFamily: 'var(--font-display)' }}
            >
              ARCHIVE
            </h1>
            <span
              className="text-[10px] tracking-[0.3em]"
              style={{
                color: '#1A1612',
                fontFamily: 'var(--font-mono)',
                opacity: 0.6,
              }}
            >
              DOCUMENTARY
            </span>
          </div>
        </div>
      </div>

      {/* 2. 搜索区 */}
      <div className="mb-6" style={{ height: 160 }}>
        <div className="flex flex-col gap-2">
          {/* 搜索输入框 */}
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="检索档案..."
            className="w-full px-3 py-2 text-sm outline-none"
            style={{
              backgroundColor: '#1A1612',
              color: '#FFF8EE',
              fontFamily: 'var(--font-mono)',
              border: '2px solid #FFE52C',
            }}
          />

          {/* 搜索类型切换 */}
          <div className="flex gap-0">
            <button
              onClick={() => setLocalSearchType('title')}
              className="flex-1 px-3 py-1.5 text-[10px] font-bold tracking-wider transition-all duration-150"
              style={{
                backgroundColor: localSearchType === 'title' ? '#1A1612' : 'transparent',
                color: localSearchType === 'title' ? '#FFE52C' : '#1A1612',
                fontFamily: 'var(--font-mono)',
                borderLeft: localSearchType === 'title' ? '3px solid #FFE52C' : '3px solid transparent',
              }}
              data-cursor-hover
            >
              标题
            </button>
            <button
              onClick={() => setLocalSearchType('tag')}
              className="flex-1 px-3 py-1.5 text-[10px] font-bold tracking-wider transition-all duration-150"
              style={{
                backgroundColor: localSearchType === 'tag' ? '#1A1612' : 'transparent',
                color: localSearchType === 'tag' ? '#FFE52C' : '#1A1612',
                fontFamily: 'var(--font-mono)',
                borderLeft: localSearchType === 'tag' ? '3px solid #FFE52C' : '3px solid transparent',
              }}
              data-cursor-hover
            >
              标签
            </button>
          </div>

          {/* 搜索按钮 */}
          <motion.button
            onClick={handleSearch}
            className="w-full px-4 py-2 text-xs font-bold tracking-wider chamfer-sm"
            style={{
              backgroundColor: '#1A1612',
              color: '#FFE52C',
              fontFamily: 'var(--font-mono)',
            }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            data-cursor-hover
          >
            SEARCH
          </motion.button>
        </div>
      </div>

      {/* 3. 排序区 */}
      <div className="mb-6" style={{ height: 100 }}>
        <span
          className="text-[9px] tracking-wider block mb-2"
          style={{
            color: '#1A1612',
            fontFamily: 'var(--font-mono)',
            opacity: 0.5,
          }}
        >
          SORT
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => onSortChange('latest')}
            className="flex-1 px-3 py-1.5 text-[10px] font-bold tracking-wider transition-all duration-200 flex items-center justify-center gap-1"
            style={{
              backgroundColor: sortBy === 'latest' ? '#1A1612' : 'transparent',
              color: sortBy === 'latest' ? '#FFE52C' : '#1A1612',
              fontFamily: 'var(--font-mono)',
              border: sortBy === 'latest' ? 'none' : '1px solid rgba(26, 22, 18, 0.3)',
            }}
            data-cursor-hover
          >
            最新
            {sortBy === 'latest' && (
              <div className="w-1.5 h-1.5 rotate-45" style={{ backgroundColor: '#FFE52C' }} />
            )}
          </button>
          <button
            onClick={() => onSortChange('hot')}
            className="flex-1 px-3 py-1.5 text-[10px] font-bold tracking-wider transition-all duration-200 flex items-center justify-center gap-1"
            style={{
              backgroundColor: sortBy === 'hot' ? '#1A1612' : 'transparent',
              color: sortBy === 'hot' ? '#FFE52C' : '#1A1612',
              fontFamily: 'var(--font-mono)',
              border: sortBy === 'hot' ? 'none' : '1px solid rgba(26, 22, 18, 0.3)',
            }}
            data-cursor-hover
          >
            热门
            {sortBy === 'hot' && (
              <div className="w-1.5 h-1.5 rotate-45" style={{ backgroundColor: '#FFE52C' }} />
            )}
          </button>
        </div>
      </div>

      {/* 4. 档案统计区 */}
      <div className="mt-auto">
        <div className="flex flex-col gap-2">
          <div className="flex items-baseline gap-2">
            <span
              className="text-[24px] font-black"
              style={{ color: '#1A1612', fontFamily: 'var(--font-display)' }}
            >
              {totalFiles}
            </span>
            <span
              className="text-[10px] tracking-wider"
              style={{ color: '#1A1612', fontFamily: 'var(--font-mono)', opacity: 0.7 }}
            >
              FILES
            </span>
          </div>
          <div className="flex items-center gap-1">
            <span
              className="text-[9px] tracking-wider"
              style={{ color: '#1A1612', fontFamily: 'var(--font-mono)', opacity: 0.6 }}
            >
              SIGNAL:
            </span>
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="w-1.5 h-1.5 rounded-full"
                style={{
                  backgroundColor: '#1A1612',
                  opacity: i <= 3 ? 1 : 0.3,
                }}
              />
            ))}
          </div>
          <span
            className="text-[10px] tracking-wider"
            style={{ color: '#1A1612', fontFamily: 'var(--font-mono)', opacity: 0.5 }}
          >
            {new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
      </div>
    </div>
  );
}
