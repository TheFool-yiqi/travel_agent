import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { ToastContext } from "@/contexts/toastContext";

type ToastState = {
  message: string;
  isError: boolean;
};

const TOAST_DURATION_MS = 4000;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toast, setToast] = useState<ToastState | null>(null);

  const showToast = useCallback((message: string, isError = false) => {
    setToast({ message, isError });
  }, []);

  useEffect(() => {
    if (!toast) return;

    const timer = window.setTimeout(() => {
      setToast(null);
    }, TOAST_DURATION_MS);

    return () => window.clearTimeout(timer);
  }, [toast]);

  const value = useMemo(() => ({ showToast }), [showToast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      {toast ? (
        <div
          className={`toast ${toast.isError ? "toast-error" : "toast-info"}`}
          role="status"
          aria-live="polite"
          aria-atomic="true"
        >
          {toast.message}
        </div>
      ) : null}
    </ToastContext.Provider>
  );
}
