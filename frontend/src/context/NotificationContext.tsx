import { createContext, useCallback, useContext, type ReactNode } from 'react';
import toast, { Toaster } from 'react-hot-toast';

type ToastType = 'success' | 'error' | 'info';

interface NotificationContextValue {
  notify: (message: string, type?: ToastType) => void;
}

const NotificationContext = createContext<NotificationContextValue | null>(null);

export function NotificationProvider({ children }: { children: ReactNode }) {
  const notify = useCallback((message: string, type: ToastType = 'info') => {
    switch (type) {
      case 'success':
        toast.success(message);
        break;
      case 'error':
        toast.error(message);
        break;
      default:
        toast(message);
    }
  }, []);

  return (
    <NotificationContext.Provider value={{ notify }}>
      {children}
      <Toaster position="top-right" />
    </NotificationContext.Provider>
  );
}

export function useNotification() {
  const ctx = useContext(NotificationContext);
  if (!ctx) throw new Error('useNotification must be used within NotificationProvider');
  return ctx;
}
