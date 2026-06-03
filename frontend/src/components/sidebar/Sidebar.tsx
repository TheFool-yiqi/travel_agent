import { Compass, List, LogOut, Route, Settings } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

import { ConversationList } from "@/components/sidebar/ConversationList";
import { MobileSessionDrawer } from "@/components/sidebar/MobileSessionDrawer";
import { UserPassport } from "@/components/sidebar/UserPassport";
import { useToast } from "@/hooks/useToast";
import { ApiError } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";
import { useChatStore } from "@/stores/chatStore";

export function Sidebar() {
  const logout = useAuthStore((state) => state.logout);
  const conversations = useChatStore((state) => state.conversations);
  const createConversation = useChatStore((state) => state.createConversation);
  const resetChat = useChatStore((state) => state.reset);
  const { showToast } = useToast();
  const [creating, setCreating] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const handleNewTrip = async () => {
    if (creating) return;

    setCreating(true);
    try {
      await createConversation({ title: "新行程" });
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.message
          : error instanceof Error
            ? error.message
            : "创建行程失败";
      showToast(message, true);
    } finally {
      setCreating(false);
    }
  };

  const handleLogout = () => {
    resetChat();
    logout();
  };

  return (
    <>
      <aside className="sidebar glass-card">
        <header className="sidebar-header">
          <Compass className="sidebar-logo-icon" strokeWidth={1.5} aria-hidden />
          <div className="sidebar-brand">
            <h1 className="font-serif-brand sidebar-title">diao-travelagent</h1>
            <p className="font-display-en sidebar-subtitle">Travel Planner</p>
          </div>
        </header>

        <UserPassport />

        <button
          type="button"
          className="mobile-drawer-trigger"
          aria-label="打开行程列表"
          aria-expanded={drawerOpen}
          onClick={() => setDrawerOpen(true)}
        >
          <List className="mobile-drawer-trigger-icon" strokeWidth={1.75} aria-hidden />
        </button>

        <button
          type="button"
          className="new-chat-btn"
          onClick={() => void handleNewTrip()}
          disabled={creating}
          aria-label={creating ? "创建行程中" : "规划新行程"}
        >
          <Route className="new-chat-btn-icon" strokeWidth={1.75} aria-hidden />
          <span className="new-chat-btn-label">
            {creating ? "创建中…" : "规划新行程"}
          </span>
        </button>

        <div className="sidebar-section">
          <h2 className="sidebar-section-title">我的行程</h2>
          <ConversationList conversations={conversations} />
        </div>

        <div className="sidebar-footer">
          <Link to="/settings" className="logout-btn settings-link-btn">
            <Settings className="logout-btn-icon" strokeWidth={1.75} aria-hidden />
            <span className="logout-btn-label">设置</span>
          </Link>
          <button
            type="button"
            className="logout-btn"
            onClick={handleLogout}
            aria-label="退出登录"
          >
            <LogOut className="logout-btn-icon" strokeWidth={1.75} aria-hidden />
            <span className="logout-btn-label">退出登录</span>
          </button>
        </div>
      </aside>

      <MobileSessionDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        conversations={conversations}
      />
    </>
  );
}
