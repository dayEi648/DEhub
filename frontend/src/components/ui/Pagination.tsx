import { motion } from 'framer-motion';

interface PaginationProps {
  current: number;
  total: number;
  pageSize?: number;
  onChange: (page: number) => void;
}

export default function Pagination({ current, total, pageSize = 20, onChange }: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const pages: number[] = [];

  const add = (n: number) => {
    if (n >= 1 && n <= totalPages && !pages.includes(n)) pages.push(n);
  };

  add(1);
  add(totalPages);
  add(current);
  add(current - 1);
  add(current + 1);
  add(current - 2);
  add(current + 2);
  pages.sort((a, b) => a - b);

  const items: (number | '...')[] = [];
  let prev = 0;
  for (const p of pages) {
    if (p - prev > 1) items.push('...');
    items.push(p);
    prev = p;
  }

  return (
    <div className="flex items-center gap-1">
      <button
        className="px-2 py-1 text-[10px] font-bold tracking-wider"
        style={{
          color: current <= 1 ? 'rgba(247,243,232,0.2)' : '#FFF8EE',
          fontFamily: 'var(--font-mono)',
          cursor: current <= 1 ? 'not-allowed' : 'pointer',
        }}
        onClick={() => current > 1 && onChange(current - 1)}
        disabled={current <= 1}
        data-cursor-hover={current > 1 ? true : undefined}
      >
        &lt;
      </button>

      {items.map((item, idx) =>
        item === '...' ? (
          <span
            key={`dot-${idx}`}
            className="px-1 text-[10px]"
            style={{ color: 'rgba(247,243,232,0.3)', fontFamily: 'var(--font-mono)' }}
          >
            ...
          </span>
        ) : (
          <motion.button
            key={item}
            className="px-2.5 py-1 text-[10px] font-bold tracking-wider min-w-[28px]"
            style={{
              backgroundColor: current === item ? '#F5A623' : 'transparent',
              color: current === item ? '#1A1612' : '#FFF8EE',
              fontFamily: 'var(--font-mono)',
              border: current === item ? 'none' : '1px solid rgba(247,243,232,0.1)',
            }}
            onClick={() => onChange(item)}
            whileHover={current !== item ? { scale: 1.1, backgroundColor: 'rgba(245,166,35,0.15)' } : {}}
            whileTap={{ scale: 0.95 }}
            data-cursor-hover
          >
            {item}
          </motion.button>
        )
      )}

      <button
        className="px-2 py-1 text-[10px] font-bold tracking-wider"
        style={{
          color: current >= totalPages ? 'rgba(247,243,232,0.2)' : '#FFF8EE',
          fontFamily: 'var(--font-mono)',
          cursor: current >= totalPages ? 'not-allowed' : 'pointer',
        }}
        onClick={() => current < totalPages && onChange(current + 1)}
        disabled={current >= totalPages}
        data-cursor-hover={current < totalPages ? true : undefined}
      >
        &gt;
      </button>
    </div>
  );
}
