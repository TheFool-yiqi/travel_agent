import { create } from "zustand";

import {
  ApiError,
  createConversation as apiCreateConversation,
  deleteConversation as apiDeleteConversation,
  getChatHistory,
  getItinerary,
  listConversations,
  updateConversation as apiUpdateConversation,
} from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";
import type { ConversationResponse } from "@/types/conversation";
import type { ItineraryResponse } from "@/types/itinerary";
import type { ChatMessage, MessageResponse } from "@/types/message";

interface ChatState {
  conversations: ConversationResponse[];
  currentConversationId: string | null;
  messages: ChatMessage[];
  persistedItinerary: ItineraryResponse | null;
  historyLoading: boolean;
  loading: boolean;
  loadConversations: () => Promise<void>;
  createConversation: (options?: { title?: string }) => Promise<ConversationResponse>;
  renameConversation: (id: string, title: string) => Promise<void>;
  deleteConversation: (id: string) => Promise<void>;
  setCurrentConversationId: (id: string | null) => void;
  loadHistory: (conversationId: string) => Promise<void>;
  setMessages: (messages: ChatMessage[]) => void;
  appendMessage: (message: ChatMessage) => void;
  updateStreamingMessage: (messageId: string, content: string) => void;
  finalizeStreamingMessage: (messageId: string, metadata?: Record<string, unknown>) => void;
  reset: () => void;
}

const initialState = {
  conversations: [] as ConversationResponse[],
  currentConversationId: null as string | null,
  messages: [] as ChatMessage[],
  persistedItinerary: null as ItineraryResponse | null,
  historyLoading: false,
  loading: false,
};

function getToken(): string | null {
  return useAuthStore.getState().token;
}

function toChatMessage(message: MessageResponse): ChatMessage | null {
  if (message.role !== "user" && message.role !== "assistant") {
    return null;
  }

  return {
    id: message.id,
    role: message.role,
    content: message.content,
    created_at: message.created_at,
    metadata: message.metadata,
  };
}

export const useChatStore = create<ChatState>()((set, get) => ({
  ...initialState,

  loadConversations: async () => {
    const token = getToken();
    if (!token) return;

    set({ loading: true });
    try {
      const conversations = await listConversations(token);
      set((state) => {
        let currentConversationId = state.currentConversationId;
        if (
          currentConversationId &&
          !conversations.some((conversation) => conversation.id === currentConversationId)
        ) {
          currentConversationId = null;
        }
        if (!currentConversationId && conversations.length > 0) {
          currentConversationId = conversations[0].id;
        }
        return { conversations, loading: false, currentConversationId };
      });
    } catch (error) {
      set({ loading: false });
      throw error;
    }
  },

  createConversation: async (options = {}) => {
    const token = getToken();
    if (!token) {
      throw new Error("Not authenticated");
    }

    const conversation = await apiCreateConversation(token, {
      title: options.title ?? "新行程",
    });

    set((state) => ({
      conversations: [conversation, ...state.conversations],
      currentConversationId: conversation.id,
      messages: [],
    }));

    await get().loadHistory(conversation.id);

    return conversation;
  },

  renameConversation: async (id, title) => {
    const token = getToken();
    if (!token) {
      throw new Error("Not authenticated");
    }

    const trimmed = title.trim();
    if (!trimmed) {
      throw new Error("标题不能为空");
    }

    const updated = await apiUpdateConversation(token, id, { title: trimmed });
    set((state) => ({
      conversations: state.conversations.map((conversation) =>
        conversation.id === id ? updated : conversation,
      ),
    }));
  },

  deleteConversation: async (id) => {
    const token = getToken();
    if (!token) {
      throw new Error("Not authenticated");
    }

    await apiDeleteConversation(token, id);
    set((state) => {
      const conversations = state.conversations.filter((conversation) => conversation.id !== id);
      const wasCurrent = state.currentConversationId === id;
      return {
        conversations,
        currentConversationId: wasCurrent
          ? (conversations[0]?.id ?? null)
          : state.currentConversationId,
        messages: wasCurrent ? [] : state.messages,
        persistedItinerary: wasCurrent ? null : state.persistedItinerary,
      };
    });
  },

  setCurrentConversationId: (id) => {
    set({ currentConversationId: id, messages: [] });
  },

  loadHistory: async (conversationId) => {
    const token = getToken();
    if (!token) return;

    set({ historyLoading: true, messages: [], persistedItinerary: null });
    try {
      const [historyResult, itineraryResult] = await Promise.allSettled([
        getChatHistory(token, conversationId),
        getItinerary(token, conversationId),
      ]);

      if (historyResult.status === "rejected") {
        throw historyResult.reason;
      }

      const { messages } = historyResult.value;
      const chatMessages = messages
        .map(toChatMessage)
        .filter((message): message is ChatMessage => message !== null);

      let persistedItinerary: ItineraryResponse | null = null;
      if (itineraryResult.status === "fulfilled") {
        persistedItinerary = itineraryResult.value;
      } else if (
        !(itineraryResult.reason instanceof ApiError && itineraryResult.reason.status === 404)
      ) {
        throw itineraryResult.reason;
      }

      set({ messages: chatMessages, persistedItinerary, historyLoading: false });
    } catch (error) {
      set({ historyLoading: false });
      throw error;
    }
  },

  setMessages: (messages) => {
    set({ messages });
  },

  appendMessage: (message) => {
    set((state) => ({
      messages: [...state.messages, message],
    }));
  },

  updateStreamingMessage: (messageId, content) => {
    set((state) => ({
      messages: state.messages.map((message) =>
        message.id === messageId ? { ...message, content } : message,
      ),
    }));
  },

  finalizeStreamingMessage: (messageId, metadata) => {
    set((state) => ({
      messages: state.messages.map((message) =>
        message.id === messageId
          ? {
              ...message,
              isStreaming: false,
              ...(metadata ? { metadata: { ...message.metadata, ...metadata } } : {}),
            }
          : message,
      ),
    }));
  },

  reset: () => {
    set(initialState);
  },
}));

export function createTempMessageId(prefix: string): string {
  return `${prefix}-${crypto.randomUUID()}`;
}
