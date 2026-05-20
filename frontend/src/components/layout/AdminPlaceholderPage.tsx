import { motion } from 'framer-motion';
import AdminShell from './AdminShell';
import type { AdminPage } from '../../api/types';

interface AdminPlaceholderPageProps {
  page: AdminPage;
  icon: string;
  title: string;
  subtitle: string;
}

/**
 * 管理后台占位页面
 * 用于功能尚未开发完成的分区页面
 */
export default function AdminPlaceholderPage({ page, icon, title, subtitle }: AdminPlaceholderPageProps) {
  return (
    <AdminShell activePage={page}>
      <div className="flex flex-col items-center justify-center py-16 sm:py-24">
        <motion.div
          className="w-16 h-16 mb-5 rotate-45 flex items-center justify-center"
          style={{ border: '2px solid rgba(26, 22, 18, 0.2)' }}
          initial={{ scale: 0, rotate: -45 }}
          animate={{ scale: 1, rotate: 45 }}
          transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
        >
          <span className="text-2xl -rotate-45">{icon}</span>
        </motion.div>
        <motion.h2
          className="text-xl font-black tracking-tight mb-2"
          style={{ fontFamily: 'var(--font-display)', color: '#1A1612' }}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          {title}
        </motion.h2>
        <motion.p
          className="text-sm mb-2"
          style={{ color: 'rgba(26,22,18,0.5)' }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
        >
          {subtitle}
        </motion.p>
        <motion.p
          className="text-[10px] tracking-wider"
          style={{ color: 'rgba(26,22,18,0.35)', fontFamily: 'var(--font-mono)' }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          即将上线
        </motion.p>
      </div>
    </AdminShell>
  );
}
