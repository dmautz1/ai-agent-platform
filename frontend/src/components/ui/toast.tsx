import React, { createContext, useContext, useState, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  Info, 
  X,
  Loader2
} from 'lucide-react';

// Toast types
export type ToastType = 'success' | 'error' | 'warning' | 'info' | 'loading';

// Toast interface
export interface Toast {
  id: string;
  type: ToastType;
  title?: string;
  message: string;
  duration?: number;
  persistent?: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
}

// Toast context
interface ToastContextType {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => string;
  removeToast: (id: string) => void;
  removeAllToasts: () => void;
  updateToast: (id: string, updates: Partial<Toast>) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

// Toast provider
interface ToastProviderProps {
  children: React.ReactNode;
  maxToasts?: number;
}

export const ToastProvider: React.FC<ToastProviderProps> = ({ 
  children, 
  maxToasts = 5 
}) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substring(2, 9);
    const newToast: Toast = {
      ...toast,
      id,
      duration: toast.duration ?? (toast.type === 'loading' ? 0 : 5000),
    };

    setToasts(prev => {
      const updated = [newToast, ...prev];
      return updated.slice(0, maxToasts);
    });

    // Auto remove non-persistent toasts
    if (!toast.persistent && toast.type !== 'loading' && newToast.duration! > 0) {
      setTimeout(() => {
        removeToast(id);
      }, newToast.duration);
    }

    return id;
  }, [maxToasts]);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  const removeAllToasts = useCallback(() => {
    setToasts([]);
  }, []);

  const updateToast = useCallback((id: string, updates: Partial<Toast>) => {
    setToasts(prev => prev.map(toast => 
      toast.id === id ? { ...toast, ...updates } : toast
    ));
  }, []);

  return (
    <ToastContext.Provider value={{
      toasts,
      addToast,
      removeToast,
      removeAllToasts,
      updateToast
    }}>
      {children}
      <ToastContainer />
    </ToastContext.Provider>
  );
};

// Toast hook
export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }

  const { addToast, removeToast, updateToast } = context;

  // Helper methods
  const toast = {
    success: (message: string, options?: Partial<Toast>) => 
      addToast({ type: 'success', message, ...options }),
    
    error: (message: string, options?: Partial<Toast>) => 
      addToast({ type: 'error', message, ...options }),
    
    warning: (message: string, options?: Partial<Toast>) => 
      addToast({ type: 'warning', message, ...options }),
    
    info: (message: string, options?: Partial<Toast>) => 
      addToast({ type: 'info', message, ...options }),
    
    loading: (message: string, options?: Partial<Toast>) => 
      addToast({ type: 'loading', message, persistent: true, ...options }),
    
    custom: (toast: Omit<Toast, 'id'>) => addToast(toast),
    
    dismiss: removeToast,
    
    update: updateToast,
    
    promise: async <T,>(
      promise: Promise<T>,
      {
        loading: loadingMessage,
        success: successMessage,
        error: errorMessage,
      }: {
        loading: string;
        success: string | ((data: T) => string);
        error: string | ((error: any) => string);
      }
    ) => {
      const id = addToast({ type: 'loading', message: loadingMessage, persistent: true });
      
      try {
        const result = await promise;
        updateToast(id, {
          type: 'success',
          message: typeof successMessage === 'function' ? successMessage(result) : successMessage,
          persistent: false,
          duration: 5000
        });
        
        // Auto remove after duration
        setTimeout(() => removeToast(id), 5000);
        
        return result;
      } catch (error) {
        updateToast(id, {
          type: 'error',
          message: typeof errorMessage === 'function' ? errorMessage(error) : errorMessage,
          persistent: false,
          duration: 7000
        });
        
        // Auto remove after duration
        setTimeout(() => removeToast(id), 7000);
        
        throw error;
      }
    }
  };

  return toast;
};

// Individual toast component
interface ToastItemProps {
  toast: Toast;
  onRemove: () => void;
}

const ToastItem: React.FC<ToastItemProps> = ({ toast, onRemove }) => {
  const [isExiting, setIsExiting] = useState(false);

  const handleRemove = () => {
    setIsExiting(true);
    setTimeout(onRemove, 150); // Wait for exit animation
  };

  const getIcon = () => {
    switch (toast.type) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'warning':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      case 'info':
        return <Info className="h-5 w-5 text-blue-500" />;
      case 'loading':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
    }
  };

  const getStyles = () => {
    const baseStyles = "relative flex items-start gap-3 p-4 rounded-lg border shadow-lg backdrop-blur-sm transition-all duration-200 max-w-md";
    
    switch (toast.type) {
      case 'success':
        return cn(baseStyles, "bg-green-50 border-green-200 text-green-800 dark:bg-green-950 dark:border-green-800 dark:text-green-200");
      case 'error':
        return cn(baseStyles, "bg-red-50 border-red-200 text-red-800 dark:bg-red-950 dark:border-red-800 dark:text-red-200");
      case 'warning':
        return cn(baseStyles, "bg-yellow-50 border-yellow-200 text-yellow-800 dark:bg-yellow-950 dark:border-yellow-800 dark:text-yellow-200");
      case 'info':
        return cn(baseStyles, "bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-950 dark:border-blue-800 dark:text-blue-200");
      case 'loading':
        return cn(baseStyles, "bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-950 dark:border-blue-800 dark:text-blue-200");
      default:
        return cn(baseStyles, "bg-background border-border");
    }
  };

  return (
    <div
      className={cn(
        getStyles(),
        isExiting && "translate-x-full opacity-0",
        !isExiting && "animate-in slide-in-from-right-full"
      )}
    >
      <div className="flex-shrink-0 mt-0.5">
        {getIcon()}
      </div>
      
      <div className="flex-1 min-w-0">
        {toast.title && (
          <div className="font-medium text-sm mb-1">{toast.title}</div>
        )}
        <div className="text-sm leading-relaxed">{toast.message}</div>
        
        {toast.action && (
          <button
            onClick={toast.action.onClick}
            className="mt-2 text-xs font-medium underline hover:no-underline"
          >
            {toast.action.label}
          </button>
        )}
      </div>
      
      <button
        onClick={handleRemove}
        className="flex-shrink-0 p-1 rounded hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
};

// Toast container
const ToastContainer: React.FC = () => {
  const context = useContext(ToastContext);
  if (!context) return null;
  
  const { toasts, removeToast } = context;

  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 pointer-events-none">
      <div className="flex flex-col gap-2 pointer-events-auto">
        {toasts.map((toast: Toast) => (
          <ToastItem
            key={toast.id}
            toast={toast}
            onRemove={() => removeToast(toast.id)}
          />
        ))}
      </div>
    </div>
  );
};

// Export components and hook
export { ToastContainer, ToastItem }; 