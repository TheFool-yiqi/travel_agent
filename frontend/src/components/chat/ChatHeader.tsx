import { Bot, MapPin } from "lucide-react";

type ChatHeaderProps = {
  title: string;
  toolCallIndicator?: string | null;
};

export function ChatHeader({ title, toolCallIndicator }: ChatHeaderProps) {
  return (
    <header className="chat-header">
      <div className="chat-header-main">
        <div className="chat-header-icon-wrap">
          <Bot className="chat-header-icon" strokeWidth={1.75} aria-hidden />
        </div>
        <div className="chat-header-text">
          <h2 className="font-serif-brand chat-header-title">{title}</h2>
          {toolCallIndicator ? (
            <p className="chat-header-tool-indicator">正在调用 {toolCallIndicator}…</p>
          ) : null}
        </div>
      </div>
      <span className="chat-header-badge">
        <MapPin className="chat-header-badge-icon" strokeWidth={2} aria-hidden />
        准备出发
      </span>
    </header>
  );
}
