import { useState, useCallback, createContext, useContext, useRef, useEffect, type ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

type ToastType = 'success' | 'error' | 'info';

interface ToastItem {
  id: number;
  message: string;
  type: ToastType;
}

interface ToastContextValue {
  showToast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const timersRef = useRef<Set<ReturnType<typeof setTimeout>>>(new Set());

  useEffect(() => {
    const timers = timersRef.current;
    return () => {
      timers.forEach(clearTimeout);
      timers.clear();
    };
  }, []);

  const showToast = useCallback((message: string, type: ToastType = 'info') => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, message, type }]);
    const timer = setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
      timersRef.current.delete(timer);
    }, 3000);
    timersRef.current.add(timer);
  }, []);

  const colors: Record<ToastType, string> = {
    success: '#C4D70C',
    error: '#FF4D4D',
    info: '#7FE6EF',
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="fixed top-6 right-6 z-[9995] flex flex-col gap-3 pointer-events-none">
        <AnimatePresence>
          {toasts.map((t) => (
            <motion.div
              key={t.id}
              className="chamfer-sm pointer-events-auto flex items-center gap-3 px-4 py-3 min-w-[240px] max-w-[360px]"
              style={{
                backgroundColor: 'rgba(26, 22, 18, 0.95)',
                border: '1px solid rgba(245, 166, 35, 0.2)',
                boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
              }}
              initial={{ x: 60, opacity: 0, scale: 0.95 }}
              animate={{ x: 0, opacity: 1, scale: 1 }}
              exit={{ x: 40, opacity: 0, scale: 0.95 }}
              transition={{ type: 'spring', damping: 22, stiffness: 400 }}
            >
              <div
                className="w-1 h-full min-h-[20px]"
                style={{ backgroundColor: colors[t.type] }}
              />
              <span
                className="text-sm"
                style={{ color: '#FFF8EE', fontFamily: 'var(--font-body)' }}
              >
                {t.message}
              </span>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}
