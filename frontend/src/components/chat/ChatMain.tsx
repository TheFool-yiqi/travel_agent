import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { ApprovalBanner } from "@/components/chat/ApprovalBanner";
import { ChatHeader } from "@/components/chat/ChatHeader";
import { ChatInput } from "@/components/chat/ChatInput";
import { ItineraryCard } from "@/components/chat/ItineraryCard";
import { MessageList } from "@/components/chat/MessageList";
import { StepProgress } from "@/components/chat/StepProgress";
import { useToast } from "@/hooks/useToast";
import { useChatStream } from "@/hooks/useChatStream";
import { ApiError } from "@/lib/api";
import { normalizeItinerary } from "@/types/itinerary";
import {
  createTempMessageId,
  useChatStore,
} from "@/stores/chatStore";

type ChatMainProps = {
  conversationId: string;
  title: string;
};

export function ChatMain({ conversationId, title }: ChatMainProps) {
  const messages = useChatStore((state) => state.messages);
  const historyLoading = useChatStore((state) => state.historyLoading);
  const persistedItinerary = useChatStore((state) => state.persistedItinerary);
  const loadHistory = useChatStore((state) => state.loadHistory);
  const appendMessage = useChatStore((state) => state.appendMessage);
  const updateStreamingMessage = useChatStore((state) => state.updateStreamingMessage);
  const finalizeStreamingMessage = useChatStore((state) => state.finalizeStreamingMessage);
  const {
    sendMessage,
    isStreaming,
    toolCallIndicator,
    currentStep,
    itineraryDays,
    itineraryBudget,
    approvalRequired,
    clearApprovalRequired,
  } = useChatStream(conversationId);
  const { showToast } = useToast();
  const [showTypingIndicator, setShowTypingIndicator] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const streamingMessageIdRef = useRef<string | null>(null);
  const streamingContentRef = useRef("");
  const streamingMetadataRef = useRef<Record<string, unknown>>({});

  useEffect(() => {
    void loadHistory(conversationId).catch((error: unknown) => {
      const message =
        error instanceof ApiError
          ? error.message
          : error instanceof Error
            ? error.message
            : "加载对话历史失败";
      showToast(message, true);
    });
  }, [conversationId, loadHistory, showToast]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, showTypingIndicator, historyLoading]);

  const handleSend = useCallback(
    async (content: string) => {
      const userMessageId = createTempMessageId("user");
      const assistantMessageId = createTempMessageId("assistant");
      const now = new Date().toISOString();

      streamingMessageIdRef.current = assistantMessageId;
      streamingContentRef.current = "";
      streamingMetadataRef.current = {};
      setShowTypingIndicator(true);

      appendMessage({
        id: userMessageId,
        role: "user",
        content,
        created_at: now,
      });

      await sendMessage(content, {
        onToken: (token) => {
          if (streamingContentRef.current === "") {
            setShowTypingIndicator(false);
            appendMessage({
              id: assistantMessageId,
              role: "assistant",
              content: token,
              created_at: now,
              isStreaming: true,
            });
            streamingContentRef.current = token;
            return;
          }

          streamingContentRef.current += token;
          updateStreamingMessage(assistantMessageId, streamingContentRef.current);
        },
        onItinerary: (itinerary, budget) => {
          streamingMetadataRef.current = {
            itinerary,
            ...(budget ? { budget } : {}),
          };
        },
        onDone: () => {
          setShowTypingIndicator(false);
          if (streamingMessageIdRef.current) {
            if (streamingContentRef.current) {
              finalizeStreamingMessage(
                streamingMessageIdRef.current,
                Object.keys(streamingMetadataRef.current).length > 0
                  ? streamingMetadataRef.current
                  : undefined,
              );
            } else {
              void loadHistory(conversationId);
            }
          }
          streamingMessageIdRef.current = null;
          streamingContentRef.current = "";
          streamingMetadataRef.current = {};
        },
        onError: (message) => {
          setShowTypingIndicator(false);
          if (streamingContentRef.current) {
            finalizeStreamingMessage(assistantMessageId);
          } else {
            appendMessage({
              id: assistantMessageId,
              role: "assistant",
              content: message,
              created_at: now,
            });
          }
          showToast(message, true);
          streamingMessageIdRef.current = null;
          streamingContentRef.current = "";
          streamingMetadataRef.current = {};
        },
      });
    },
    [
      appendMessage,
      conversationId,
      finalizeStreamingMessage,
      loadHistory,
      sendMessage,
      showToast,
      updateStreamingMessage,
    ],
  );

  const normalizedDays = useMemo(() => {
    if (itineraryDays.length > 0) {
      return normalizeItinerary(itineraryDays);
    }
    if (persistedItinerary?.days?.length) {
      return normalizeItinerary(persistedItinerary.days);
    }
    for (let index = messages.length - 1; index >= 0; index -= 1) {
      const message = messages[index];
      const raw = message.metadata?.itinerary;
      if (raw) {
        return normalizeItinerary(raw);
      }
    }
    return [];
  }, [itineraryDays, messages, persistedItinerary]);

  const displayBudget = useMemo(() => {
    if (itineraryBudget) {
      return itineraryBudget;
    }
    if (persistedItinerary?.budget) {
      return persistedItinerary.budget;
    }
    for (let index = messages.length - 1; index >= 0; index -= 1) {
      const budget = messages[index].metadata?.budget;
      if (budget && typeof budget === "object") {
        return budget as Record<string, number>;
      }
    }
    return undefined;
  }, [itineraryBudget, messages, persistedItinerary]);

  return (
    <section className="chat-main glass-card">
      <ChatHeader title={title} toolCallIndicator={toolCallIndicator} />
      <StepProgress currentStep={currentStep} />
      <div className="chat-content-row">
        <div
          className="chat-body"
          aria-live="polite"
          aria-relevant="additions"
          aria-busy={isStreaming || historyLoading}
        >
          <MessageList
            messages={messages}
            historyLoading={historyLoading}
            showTypingIndicator={showTypingIndicator}
          />
          <div ref={messagesEndRef} />
        </div>
        {normalizedDays.length > 0 ? (
          <ItineraryCard days={normalizedDays} budget={displayBudget} />
        ) : null}
      </div>
      {toolCallIndicator ? (
        <p className="chat-tool-banner">正在查询 {toolCallIndicator}…</p>
      ) : null}
      {approvalRequired ? (
        <ApprovalBanner
          disabled={isStreaming || historyLoading}
          onConfirm={() => {
            clearApprovalRequired();
            void handleSend("确认行程");
          }}
          onRequestChanges={() => {
            clearApprovalRequired();
            void handleSend("我想修改行程，请根据我的偏好重新调整。");
          }}
        />
      ) : null}
      <div className="chat-footer">
        <ChatInput onSend={handleSend} disabled={isStreaming || historyLoading} />
      </div>
    </section>
  );
}
