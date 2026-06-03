import { ArrowLeft, LogOut } from "lucide-react";
import { Link } from "react-router-dom";

import { useAuthStore } from "@/stores/authStore";

export default function SettingsPage() {
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  return (
    <main className="settings-page">
      <div className="settings-card glass-card">
        <Link to="/" className="settings-back">
          <ArrowLeft size={18} aria-hidden />
          返回对话
        </Link>
        <h1 className="font-serif-brand settings-title">设置</h1>
        <p className="settings-subtitle">diao-travelagent</p>
        {user ? (
          <p className="settings-user">
            当前用户：<strong>{user.username}</strong>
          </p>
        ) : null}
        <p className="settings-hint">更多偏好与通知选项将在后续版本提供。</p>
        <button type="button" className="btn-primary settings-logout" onClick={logout}>
          <LogOut size={18} aria-hidden />
          退出登录
        </button>
      </div>
    </main>
  );
}
