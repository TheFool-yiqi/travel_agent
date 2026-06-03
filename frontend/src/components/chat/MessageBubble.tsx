import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import type { ChatMessage } from "@/types/message";

type MessageBubbleProps = {
  message: ChatMessage;
};

function renderPlainContent(content: string) {
  const lines = content.split("\n");

  return lines.map((line, index) => (
    <span key={index}>
      {index > 0 ? <br /> : null}
      {line}
    </span>
  ));
}

function normalizeAssistantContent(content: string): string {
  const withoutPairs = content.replace(/\*\*([^*]+)\*\*/g, "$1");
  return withoutPairs.replace(/\*\*/g, "");
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <article
      className={`message-bubble ${isUser ? "message-bubble-user" : "message-bubble-assistant"}`}
    >
      {!isUser ? <div className="message-bubble-notch" aria-hidden /> : null}
      <div className="message-bubble-content">
        {isUser ? (
          renderPlainContent(message.content)
        ) : (
          <div className="markdown-prose">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {normalizeAssistantContent(message.content)}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </article>
  );
}
