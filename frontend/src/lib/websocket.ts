import { API_BASE_URL } from "@/lib/config";
import { parseSSEStream, type SSEEvent } from "@/lib/sse";

export type { SSEEvent as StreamEvent };

function httpToWebSocketBase(httpUrl: string): string {
  return httpUrl.replace(/^http:\/\//, "ws://").replace(/^https:\/\//, "wss://");
}

/** Build authenticated WebSocket URL for chat streaming. */
export function buildChatWebSocketUrl(
  conversationId: string,
  token?: string,
): string {
  const base = httpToWebSocketBase(API_BASE_URL);
  const url = new URL(`${base}/chat/ws/${conversationId}`);
  if (token) {
    url.searchParams.set("token", token);
  }
  return url.toString();
}

export type WebSocketChatMessage =
  | { type: "auth"; token: string }
  | { type: "message"; content: string }
  | { type: "ping" };

export type WebSocketFrame = SSEEvent | { type: "pong" };

export class TravelWebSocketClient {
  private socket: WebSocket | null = null;

  connect(url: string): Promise<void> {
    return new Promise((resolve, reject) => {
      this.close();
      const socket = new WebSocket(url);
      this.socket = socket;

      socket.onopen = () => resolve();
      socket.onerror = () => reject(new Error("WebSocket connection failed"));
    });
  }

  sendAuth(token: string): void {
    this.send({ type: "auth", token });
  }

  sendMessage(content: string): void {
    this.send({ type: "message", content });
  }

  send(payload: WebSocketChatMessage): void {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      throw new Error("WebSocket is not connected");
    }
    this.socket.send(JSON.stringify(payload));
  }

  onFrame(handler: (frame: WebSocketFrame) => void): () => void {
    const socket = this.socket;
    if (!socket) {
      return () => undefined;
    }

    const listener = (event: MessageEvent<string>) => {
      try {
        handler(JSON.parse(event.data) as WebSocketFrame);
      } catch {
        // ignore malformed frames
      }
    };

    socket.addEventListener("message", listener);
    return () => socket.removeEventListener("message", listener);
  }

  close(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }
}

/** Parse SSE-style events from a WebSocket message stream helper (for tests). */
export async function* framesFromReadableStream(
  reader: ReadableStreamDefaultReader<Uint8Array>,
): AsyncGenerator<SSEEvent> {
  for await (const event of parseSSEStream(reader)) {
    yield event;
  }
}
