import { useCallback, useRef, useState } from "react";

import { ApiError } from "@/lib/api";
import {
  buildChatWebSocketUrl,
  TravelWebSocketClient,
  type WebSocketFrame,
} from "@/lib/websocket";
import { useAuthStore } from "@/stores/authStore";

type StreamCallbacks = {
  onToken?: (token: string) => void;
  onStep?: (step: string, label: string) => void;
  onItinerary?: (itinerary: unknown[], budget?: Record<string, number>) => void;
  onDone?: () => void;
  onError?: (message: string) => void;
};

/**
 * WebSocket travel stream hook (exported for future use; ChatMain still uses SSE).
 */
export function useTravelStream(conversationId: string | null) {
  const token = useAuthStore((state) => state.token);
  const clientRef = useRef<TravelWebSocketClient | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [toolCallIndicator, setToolCallIndicator] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<string | null>(null);
  const [itineraryDays, setItineraryDays] = useState<unknown[]>([]);
  const [itineraryBudget, setItineraryBudget] = useState<Record<string, number> | undefined>();
  const [approvalRequired, setApprovalRequired] = useState(false);

  const sendMessage = useCallback(
    async (content: string, callbacks: StreamCallbacks = {}) => {
      if (!conversationId || !token || !content.trim() || isStreaming) {
        return;
      }

      clientRef.current?.close();
      const client = new TravelWebSocketClient();
      clientRef.current = client;

      setIsStreaming(true);
      setToolCallIndicator(null);
      setCurrentStep(null);
      setApprovalRequired(false);

      const url = buildChatWebSocketUrl(conversationId, token);

      try {
        await client.connect(url);

        let settled = false;
        const unsubscribe = client.onFrame((frame: WebSocketFrame) => {
          if (frame.type === "pong") {
            return;
          }

          switch (frame.type) {
            case "token":
              callbacks.onToken?.(frame.content);
              break;
            case "tool_call":
              setToolCallIndicator(frame.tool || "工具");
              break;
            case "step":
              setCurrentStep(frame.step);
              callbacks.onStep?.(frame.step, frame.label);
              break;
            case "itinerary":
              setItineraryDays(frame.itinerary);
              setItineraryBudget(frame.budget);
              callbacks.onItinerary?.(frame.itinerary, frame.budget);
              break;
            case "approval_required":
              setApprovalRequired(true);
              break;
            case "done":
              settled = true;
              callbacks.onDone?.();
              break;
            case "error":
              settled = true;
              callbacks.onError?.(frame.message);
              break;
          }
        });

        client.sendMessage(content.trim());

        await new Promise<void>((resolve) => {
          const timer = window.setInterval(() => {
            if (settled) {
              window.clearInterval(timer);
              unsubscribe();
              resolve();
            }
          }, 50);
        });
      } catch (error) {
        const message =
          error instanceof ApiError
            ? error.message
            : error instanceof Error
              ? error.message
              : "WebSocket 流式失败";
        callbacks.onError?.(message);
      } finally {
        client.close();
        if (clientRef.current === client) {
          clientRef.current = null;
        }
        setIsStreaming(false);
        setToolCallIndicator(null);
      }
    },
    [conversationId, isStreaming, token],
  );

  return {
    sendMessage,
    isStreaming,
    toolCallIndicator,
    currentStep,
    itineraryDays,
    itineraryBudget,
    approvalRequired,
    clearApprovalRequired: () => setApprovalRequired(false),
  };
}
