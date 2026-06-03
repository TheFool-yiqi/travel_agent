import { TypingIndicator } from "@/components/chat/TypingIndicator";
import type { ChatMessage } from "@/types/message";

import { MessageBubble } from "./MessageBubble";
import { WelcomeScreen } from "./WelcomeScreen";

type MessageListProps = {
  messages: ChatMessage[];
  historyLoading: boolean;
  showTypingIndicator: boolean;
};

export function MessageList({
  messages,
  historyLoading,
  showTypingIndicator,
}: MessageListProps) {
  if (historyLoading) {
    return (
      <div className="message-list message-list-loading">
        <TypingIndicator />
      </div>
    );
  }

  if (messages.length === 0 && !showTypingIndicator) {
    return (
      <div className="message-list message-list-empty">
        <WelcomeScreen />
      </div>
    );
  }

  return (
    <div className="message-list">
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
      {showTypingIndicator ? <TypingIndicator /> : null}
    </div>
  );
}
