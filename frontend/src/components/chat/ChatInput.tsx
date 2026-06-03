import { Send } from "lucide-react";
import { useCallback, useEffect, useRef, type KeyboardEvent, type MouseEvent } from "react";

type ChatInputProps = {
  onSend: (content: string) => void;
  disabled?: boolean;
  placeholder?: string;
};

export function ChatInput({
  onSend,
  disabled = false,
  placeholder = "描述你的旅行计划…",
}: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const focusInput = useCallback(() => {
    const textarea = textareaRef.current;
    if (!textarea || disabled) return;
    textarea.focus({ preventScroll: true });
  }, [disabled]);

  const resizeTextarea = useCallback(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`;
  }, []);

  useEffect(() => {
    resizeTextarea();
  }, [resizeTextarea]);

  useEffect(() => {
    focusInput();
  }, [focusInput]);

  const handleSend = () => {
    const textarea = textareaRef.current;
    if (!textarea || disabled) return;

    const value = textarea.value.trim();
    if (!value) return;

    onSend(value);
    textarea.value = "";
    resizeTextarea();
    focusInput();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  const keepFocusOnSendButton = (event: MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
  };

  return (
    <div className="chat-input-wrap">
      <label htmlFor="chat-message-input" className="sr-only">
        消息
      </label>
      <textarea
        id="chat-message-input"
        ref={textareaRef}
        className="chat-input"
        name="message"
        rows={1}
        placeholder={placeholder}
        disabled={disabled}
        autoComplete="off"
        onInput={resizeTextarea}
        onKeyDown={handleKeyDown}
      />
      <button
        type="button"
        className="chat-input-send"
        onMouseDown={keepFocusOnSendButton}
        onClick={handleSend}
        disabled={disabled}
        aria-label="发送消息"
      >
        <Send className="chat-input-send-icon" strokeWidth={2} aria-hidden />
      </button>
    </div>
  );
}
