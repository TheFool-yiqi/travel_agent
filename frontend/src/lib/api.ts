import { API_BASE_URL } from "@/lib/config";
import { isUnauthorizedStatus, notifyUnauthorized } from "@/lib/authSession";
import type { ConversationResponse } from "@/types/conversation";
import type { ItineraryResponse } from "@/types/itinerary";
import type { MessageResponse } from "@/types/message";
import type { TokenResponse, UserResponse } from "@/types/user";

export type ChatHistoryResponse = {
  conversation: ConversationResponse;
  messages: MessageResponse[];
};

type FastApiValidationError = {
  msg?: string;
  loc?: unknown[];
};

type FastApiErrorBody = {
  detail?: string | FastApiValidationError[];
};

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function parseErrorDetail(body: FastApiErrorBody): string {
  const { detail } = body;
  if (!detail) return "Request failed";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => item.msg ?? JSON.stringify(item))
      .join("; ");
  }
  return "Request failed";
}

type FetchApiOptions = RequestInit & {
  token?: string;
};

async function fetchApi<T>(path: string, options: FetchApiOptions = {}): Promise<T> {
  const { token, headers: initHeaders, ...rest } = options;
  const headers = new Headers(initHeaders);

  if (rest.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers,
  });

  if (!response.ok) {
    let message = response.statusText;
    try {
      const body = (await response.json()) as FastApiErrorBody;
      message = parseErrorDetail(body);
    } catch {
      // keep statusText
    }
    if (isUnauthorizedStatus(response.status)) {
      notifyUnauthorized();
    }
    throw new ApiError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export function registerUser(data: {
  username: string;
  email: string;
  password: string;
}): Promise<TokenResponse> {
  return fetchApi<TokenResponse>("/users/register", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function loginUser(data: {
  username: string;
  password: string;
}): Promise<TokenResponse> {
  return fetchApi<TokenResponse>("/users/login", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getMe(token: string): Promise<UserResponse> {
  return fetchApi<UserResponse>("/users/me", { token });
}

export function listConversations(token: string): Promise<ConversationResponse[]> {
  return fetchApi<ConversationResponse[]>("/conversations", { token });
}

export function createConversation(
  token: string,
  data: { title?: string } = {},
): Promise<ConversationResponse> {
  return fetchApi<ConversationResponse>("/conversations", {
    method: "POST",
    token,
    body: JSON.stringify(data),
  });
}

export function updateConversation(
  token: string,
  id: string,
  data: { title?: string },
): Promise<ConversationResponse> {
  return fetchApi<ConversationResponse>(`/conversations/${id}`, {
    method: "PATCH",
    token,
    body: JSON.stringify(data),
  });
}

export function deleteConversation(token: string, id: string): Promise<{ message: string }> {
  return fetchApi<{ message: string }>(`/conversations/${id}`, {
    method: "DELETE",
    token,
  });
}

export function getConversation(
  token: string,
  id: string,
): Promise<ConversationResponse> {
  return fetchApi<ConversationResponse>(`/conversations/${id}`, { token });
}

export function getChatHistory(
  token: string,
  conversationId: string,
): Promise<ChatHistoryResponse> {
  return fetchApi<ChatHistoryResponse>(`/chat/history/${conversationId}`, { token });
}

export function getItinerary(
  token: string,
  sessionId: string,
): Promise<ItineraryResponse> {
  return fetchApi<ItineraryResponse>(`/itineraries/sessions/${sessionId}`, { token });
}

export function streamChat(
  token: string,
  conversationId: string,
  content: string,
): Promise<Response> {
  const headers = new Headers({
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  });

  return fetch(`${API_BASE_URL}/chat/stream/${conversationId}`, {
    method: "POST",
    headers,
    body: JSON.stringify({ content }),
  });
}
