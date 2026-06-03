import { createContext } from "react";

export type ToastContextValue = {
  showToast: (message: string, isError?: boolean) => void;
};

export const ToastContext = createContext<ToastContextValue | null>(null);
