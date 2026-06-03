import { useAuthStore } from "@/stores/authStore";

function getInitial(username: string): string {
  const trimmed = username.trim();
  if (!trimmed) return "?";
  return trimmed.charAt(0).toUpperCase();
}

export function UserPassport() {
  const user = useAuthStore((state) => state.user);

  if (!user) return null;

  const displayName = user.display_name?.trim() || user.username;

  return (
    <div className="user-passport">
      <div className="user-passport-avatar" aria-hidden>
        {getInitial(displayName)}
      </div>
      <div className="user-passport-info">
        <span className="user-passport-label font-display-en">PASSPORT</span>
        <span className="user-passport-name">{displayName}</span>
      </div>
    </div>
  );
}
