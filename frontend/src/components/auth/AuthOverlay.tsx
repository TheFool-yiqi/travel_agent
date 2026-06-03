import { Compass, Loader2 } from "lucide-react";
import { FormEvent, useState } from "react";

import { useToast } from "@/hooks/useToast";
import { BackgroundDecor } from "@/components/layout/BackgroundDecor";
import { ApiError } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

type AuthTab = "login" | "register";

export function AuthOverlay() {
  const [tab, setTab] = useState<AuthTab>("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [inlineError, setInlineError] = useState<string | null>(null);

  const login = useAuthStore((state) => state.login);
  const register = useAuthStore((state) => state.register);
  const { showToast } = useToast();

  const switchTab = (nextTab: AuthTab) => {
    setTab(nextTab);
    setInlineError(null);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setInlineError(null);
    setLoading(true);

    try {
      if (tab === "login") {
        await login(username.trim(), password);
        showToast("欢迎回来");
      } else {
        await register(username.trim(), email.trim(), password);
        showToast("注册成功，欢迎加入");
      }
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.message
          : error instanceof Error
            ? error.message
            : "操作失败，请稍后重试";
      setInlineError(message);
      showToast(message, true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <BackgroundDecor />
      <div className="auth-overlay">
        <div className="auth-card glass-card">
          <div className="stamp-decoration" aria-hidden />

          <div className="auth-brand">
            <Compass className="auth-brand-icon" strokeWidth={1.5} aria-hidden />
            <h1 className="font-serif-brand auth-brand-title">diao-travelagent</h1>
            <p className="font-display-en auth-brand-subtitle">
              Your intelligent travel companion
            </p>
          </div>

          <div className="auth-tabs" role="tablist" aria-label="认证方式">
            <button
              type="button"
              role="tab"
              aria-selected={tab === "login"}
              className={`auth-tab ${tab === "login" ? "auth-tab-active" : ""}`}
              onClick={() => switchTab("login")}
            >
              登录
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={tab === "register"}
              className={`auth-tab ${tab === "register" ? "auth-tab-active" : ""}`}
              onClick={() => switchTab("register")}
            >
              注册
            </button>
          </div>

          <form className="auth-form" onSubmit={handleSubmit}>
            <div className="auth-field">
              <label className="auth-label" htmlFor="auth-username">
                用户名
              </label>
              <input
                id="auth-username"
                className="auth-input"
                type="text"
                name="username"
                autoComplete="username"
                spellCheck={false}
                required
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                disabled={loading}
              />
            </div>

            {tab === "register" ? (
              <div className="auth-field">
                <label className="auth-label" htmlFor="auth-email">
                  邮箱
                </label>
                <input
                  id="auth-email"
                  className="auth-input"
                  type="email"
                  name="email"
                  autoComplete="email"
                  spellCheck={false}
                  required
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  disabled={loading}
                />
              </div>
            ) : null}

            <div className="auth-field">
              <label className="auth-label" htmlFor="auth-password">
                密码
              </label>
              <input
                id="auth-password"
                className="auth-input"
                type="password"
                name="password"
                autoComplete={tab === "login" ? "current-password" : "new-password"}
                spellCheck={false}
                required
                minLength={6}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                disabled={loading}
              />
            </div>

            {inlineError ? (
              <p className="auth-error" role="alert">
                {inlineError}
              </p>
            ) : null}

            <button type="submit" className="auth-submit" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="auth-submit-spinner" aria-hidden />
                  处理中…
                </>
              ) : tab === "login" ? (
                "登录"
              ) : (
                "注册"
              )}
            </button>
          </form>
        </div>
      </div>
    </>
  );
}
