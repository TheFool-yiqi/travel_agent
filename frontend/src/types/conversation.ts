/** Matches backend session status literals. */
export type SessionStatus = "active" | "archived" | "deleted";

/** Matches backend `ConversationResponse`. */
export interface ConversationResponse {
  id: string;
  user_id: string;
  title: string;
  status: SessionStatus | string;
  extra_info: Record<string, unknown>;
  thread_id: string | null;
  created_at: string;
  updated_at: string;
}
