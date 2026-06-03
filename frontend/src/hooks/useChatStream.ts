import { useCallback, useRef, useState } from "react";

import { ApiError, streamChat } from "@/lib/api";
import { isUnauthorizedStatus, notifyUnauthorized } from "@/lib/authSession";
import { parseSSEStream } from "@/lib/sse";
import { useAuthStore } from "@/stores/authStore";

type StreamCallbacks = {
  onToken?: (token: string) => void;
  onStep?: (step: string, label: string) => void;
  onItinerary?: (itinerary: unknown[], budget?: Record<string, number>) => void;
  onDone?: () => void;
  onError?: (message: string) => void;
};

export function useChatStream(conversationId: string | null) {
  const token = useAuthStore((state) => state.token);
  const [isStreaming, setIsStreaming] = useState(false);
  const [toolCallIndicator, setToolCallIndicator] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<string | null>(null);
  const [itineraryDays, setItineraryDays] = useState<unknown[]>([]);
  const [itineraryBudget, setItineraryBudget] = useState<Record<string, number> | undefined>();
  const [approvalRequired, setApprovalRequired] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const isStreamingRef = useRef(false);

  const sendMessage = useCallback(
    async (content: string, callbacks: StreamCallbacks = {}) => {
      if (!conversationId || !token || !content.trim() || isStreamingRef.current) {
        return;
      }

      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      isStreamingRef.current = true;

      setIsStreaming(true);
      setToolCallIndicator(null);
      setCurrentStep(null);
      setApprovalRequired(false);

      try {
        const response = await streamChat(token, conversationId, content.trim());

        if (!response.ok) {
          let message = response.statusText;
          try {
            const body = (await response.json()) as { detail?: string };
            if (typeof body.detail === "string") {
              message = body.detail;
            }
          } catch {
            // keep statusText
          }
          if (isUnauthorizedStatus(response.status)) {
            notifyUnauthorized();
          }
          throw new ApiError(message, response.status);
        }

        if (!response.body) {
          throw new Error("No response body");
        }

        const reader = response.body.getReader();

        for await (const event of parseSSEStream(reader)) {
          if (controller.signal.aborted) {
            break;
          }

          switch (event.type) {
            case "token":
              callbacks.onToken?.(event.content);
              break;
            case "tool_call":
              setToolCallIndicator(event.tool || "工具");
              break;
            case "step":
              setCurrentStep(event.step);
              callbacks.onStep?.(event.step, event.label);
              break;
            case "itinerary":
              setItineraryDays(event.itinerary);
              setItineraryBudget(event.budget);
              callbacks.onItinerary?.(event.itinerary, event.budget);
              break;
            case "approval_required":
              setApprovalRequired(true);
              break;
            case "done":
              callbacks.onDone?.();
              break;
            case "error":
              callbacks.onError?.(event.message);
              break;
          }
        }
      } catch (error) {
        const message =
          error instanceof ApiError
            ? error.message
            : error instanceof Error
              ? error.message
              : "发送失败，请稍后重试";
        callbacks.onError?.(message);
      } finally {
        if (abortRef.current === controller) {
          abortRef.current = null;
        }
        isStreamingRef.current = false;
        setIsStreaming(false);
        setToolCallIndicator(null);
      }
    },
    [conversationId, token],
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
