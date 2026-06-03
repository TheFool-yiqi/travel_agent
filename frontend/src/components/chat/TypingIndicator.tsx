export function TypingIndicator() {
  return (
    <div className="typing-indicator" aria-label="助手正在输入">
      <span className="typing-dots">
        <span className="typing-dot" />
        <span className="typing-dot" />
        <span className="typing-dot" />
      </span>
    </div>
  );
}
