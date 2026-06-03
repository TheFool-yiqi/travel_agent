/** 401 时触发登出，避免 api ↔ authStore 循环依赖 */

const UNAUTHORIZED_EVENT = "diao-travelagent:unauthorized";

export function notifyUnauthorized(): void {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent(UNAUTHORIZED_EVENT));
  }
}

export function onUnauthorized(listener: () => void): () => void {
  if (typeof window === "undefined") {
    return () => undefined;
  }
  window.addEventListener(UNAUTHORIZED_EVENT, listener);
  return () => window.removeEventListener(UNAUTHORIZED_EVENT, listener);
}

export function isUnauthorizedStatus(status: number): boolean {
  return status === 401;
}
