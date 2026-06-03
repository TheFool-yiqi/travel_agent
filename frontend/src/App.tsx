import { useEffect, useState } from "react";
import { BrowserRouter } from "react-router-dom";

import { AuthOverlay } from "@/components/auth/AuthOverlay";
import { ToastProvider } from "@/components/ui/Toast";
import { AppRoutes } from "@/routes";
import { selectIsAuthenticated, useAuthStore } from "@/stores/authStore";

export default function App() {
  const [ready, setReady] = useState(false);
  const isAuthenticated = useAuthStore(selectIsAuthenticated);
  const hydrateFromStorage = useAuthStore((state) => state.hydrateFromStorage);

  useEffect(() => {
    const finish = () => {
      void hydrateFromStorage().finally(() => {
        setReady(true);
      });
    };

    if (useAuthStore.persist.hasHydrated()) {
      finish();
      return;
    }

    return useAuthStore.persist.onFinishHydration(finish);
  }, [hydrateFromStorage]);

  if (!ready) {
    return null;
  }

  return (
    <ToastProvider>
      {isAuthenticated ? (
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      ) : (
        <AuthOverlay />
      )}
    </ToastProvider>
  );
}
