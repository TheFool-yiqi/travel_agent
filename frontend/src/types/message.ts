/** Matches backend `MessageRole`. */
export type MessageRole = "user" | "assistant" | "system" | "tool";

/** Matches backend `MessageResponse` (ORM extra_info serialized as metadata). */
export interface MessageResponse {
  id: string;
  conversation_id: string;
  role: MessageRole | string;
  content: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

/** UI message for chat display (includes optimistic / streaming entries). */
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  metadata?: Record<string, unknown>;
  isStreaming?: boolean;
}
