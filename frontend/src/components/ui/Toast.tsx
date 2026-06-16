"use client";

import { createContext, useContext, useState, useCallback, useEffect, useId } from "react";
import styles from "./Toast.module.css";
import { CheckCircle, XCircle, Info, AlertTriangle, X } from "lucide-react";

type ToastType = "success" | "error" | "info" | "warning";

interface Toast {
  id: string;
  message: string;
  type: ToastType;
  leaving?: boolean;
}

interface ToastContextValue {
  showToast: (message: string, type?: ToastType) => void;
  success: (message: string) => void;
  error: (message: string) => void;
  info: (message: string) => void;
  warning: (message: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.map((t) => (t.id === id ? { ...t, leaving: true } : t)));
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 220);
  }, []);

  const showToast = useCallback(
    (message: string, type: ToastType = "info") => {
      const id = `toast-${Date.now()}-${Math.random()}`;
      setToasts((prev) => [...prev, { id, message, type }]);
      setTimeout(() => removeToast(id), 3500);
    },
    [removeToast]
  );

  const value: ToastContextValue = {
    showToast,
    success: (msg) => showToast(msg, "success"),
    error: (msg) => showToast(msg, "error"),
    info: (msg) => showToast(msg, "info"),
    warning: (msg) => showToast(msg, "warning"),
  };

  const iconMap = {
    success: <CheckCircle size={16} />,
    error: <XCircle size={16} />,
    info: <Info size={16} />,
    warning: <AlertTriangle size={16} />,
  };

  const styleMap = {
    success: styles.toastSuccess,
    error: styles.toastError,
    info: styles.toastInfo,
    warning: styles.toastWarning,
  };

  const iconStyleMap = {
    success: styles.iconSuccess,
    error: styles.iconError,
    info: styles.iconInfo,
    warning: styles.iconWarning,
  };

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className={styles.container} role="region" aria-label="Notifications">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`${styles.toast} ${styleMap[toast.type]} ${toast.leaving ? styles.toastLeave : ""}`}
            role="alert"
          >
            <span className={`${styles.icon} ${iconStyleMap[toast.type]}`}>
              {iconMap[toast.type]}
            </span>
            <div className={styles.content}>
              <p className={styles.message}>{toast.message}</p>
            </div>
            <button
              className={styles.close}
              onClick={() => removeToast(toast.id)}
              aria-label="Dismiss notification"
            >
              <X size={14} />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
