import type { ReactNode } from "react";

import { BackgroundDecor } from "@/components/layout/BackgroundDecor";

type AppShellProps = {
  children: ReactNode;
  sidebar?: ReactNode;
};

export function AppShell({ children, sidebar }: AppShellProps) {
  return (
    <>
      <BackgroundDecor />
      <div className="app-container">
        {sidebar}
        {children}
      </div>
    </>
  );
}
