import { motion, AnimatePresence } from 'framer-motion';
import type { ReactNode } from 'react';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: ReactNode;
  confirmText?: string;
  cancelText?: string;
  danger?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmDialog({
  open,
  title,
  message,
  confirmText = '确认',
  cancelText = '取消',
  danger = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-[9990] flex items-center justify-center px-4"
          style={{ backgroundColor: 'rgba(10, 8, 6, 0.85)' }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onCancel}
        >
          <motion.div
            className="chamfer w-full max-w-sm p-6 relative"
            style={{
              backgroundColor: 'rgba(26, 22, 18, 0.98)',
              border: '1px solid rgba(245, 166, 35, 0.25)',
              boxShadow: '0 12px 40px rgba(0,0,0,0.6)',
            }}
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            transition={{ type: 'spring', damping: 22, stiffness: 400 }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* 顶部彩条 */}
            <div
              className="absolute top-0 left-0 right-0 h-1"
              style={{
                background: danger
                  ? 'linear-gradient(90deg, #C22303, #FF4D4D)'
                  : 'linear-gradient(90deg, #F5A623, #FFE52C)',
              }}
            />

            <h3
              className="text-lg font-bold mb-3 mt-2"
              style={{ fontFamily: 'var(--font-display)', color: danger ? '#FF4D4D' : '#F5A623' }}
            >
              {title}
            </h3>
            <div className="text-sm mb-6 leading-relaxed" style={{ color: '#FFF8EE', opacity: 0.85 }}>
              {message}
            </div>

            <div className="flex gap-3 justify-end">
              <button
                className="chamfer-sm px-4 py-2 text-xs font-bold tracking-wider"
                style={{
                  backgroundColor: 'transparent',
                  color: '#FFF8EE',
                  border: '1px solid rgba(247, 243, 232, 0.2)',
                  fontFamily: 'var(--font-display)',
                }}
                onClick={onCancel}
                data-cursor-hover
              >
                {cancelText}
              </button>
              <button
                className="chamfer-sm px-4 py-2 text-xs font-bold tracking-wider"
                style={{
                  backgroundColor: danger ? '#C22303' : '#F5A623',
                  color: danger ? '#FFF8EE' : '#1A1612',
                  fontFamily: 'var(--font-display)',
                }}
                onClick={onConfirm}
                data-cursor-hover
              >
                {confirmText}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
