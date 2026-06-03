import { X } from "lucide-react";
import { useEffect, useRef } from "react";

import { ConversationList } from "@/components/sidebar/ConversationList";
import type { ConversationResponse } from "@/types/conversation";

type MobileSessionDrawerProps = {
  open: boolean;
  onClose: () => void;
  conversations: ConversationResponse[];
};

export function MobileSessionDrawer({
  open,
  onClose,
  conversations,
}: MobileSessionDrawerProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    document.body.style.overflow = "hidden";
    panelRef.current?.focus();

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open) {
    return null;
  }

  return (
    <div className="mobile-drawer-root" role="presentation">
      <button
        type="button"
        className="mobile-drawer-backdrop"
        aria-label="关闭行程列表"
        onClick={onClose}
      />
      <div
        ref={panelRef}
        className="mobile-drawer-panel glass-card"
        role="dialog"
        aria-modal="true"
        aria-label="我的行程"
        tabIndex={-1}
      >
        <header className="mobile-drawer-header">
          <h2 className="font-serif-brand mobile-drawer-title">我的行程</h2>
          <button
            type="button"
            className="mobile-drawer-close"
            aria-label="关闭"
            onClick={onClose}
          >
            <X strokeWidth={1.75} aria-hidden />
          </button>
        </header>
        <div className="mobile-drawer-body">
          <ConversationList
            conversations={conversations}
            onSelect={onClose}
            className="mobile-drawer-list"
          />
        </div>
      </div>
    </div>
  );
}
