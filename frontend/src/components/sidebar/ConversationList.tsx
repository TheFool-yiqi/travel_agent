import { Check, MapPin, Pencil, Trash2, X } from "lucide-react";
import { useEffect, useRef, useState, type KeyboardEvent } from "react";

import { useToast } from "@/hooks/useToast";
import { ApiError } from "@/lib/api";
import { isUnauthorizedStatus } from "@/lib/authSession";
import { useChatStore } from "@/stores/chatStore";
import type { ConversationResponse } from "@/types/conversation";

function formatConversationDate(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";

  const now = new Date();
  const sameDay =
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate();

  if (sameDay) {
    return date.toLocaleTimeString("zh-CN", {
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  return date.toLocaleDateString("zh-CN", {
    month: "short",
    day: "numeric",
  });
}

type ConversationRowProps = {
  conversation: ConversationResponse;
  isActive: boolean;
  onSelect: () => void;
};

function ConversationRow({ conversation, isActive, onSelect }: ConversationRowProps) {
  const renameConversation = useChatStore((state) => state.renameConversation);
  const deleteConversation = useChatStore((state) => state.deleteConversation);
  const { showToast } = useToast();
  const [editing, setEditing] = useState(false);
  const [draftTitle, setDraftTitle] = useState(conversation.title);
  const [busy, setBusy] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editing) {
      inputRef.current?.focus();
      inputRef.current?.select();
    }
  }, [editing]);

  useEffect(() => {
    if (!editing) {
      setDraftTitle(conversation.title);
    }
  }, [conversation.title, editing]);

  const handleError = (error: unknown, fallback: string) => {
    if (error instanceof ApiError && isUnauthorizedStatus(error.status)) {
      return;
    }
    const message =
      error instanceof ApiError
        ? error.message
        : error instanceof Error
          ? error.message
          : fallback;
    showToast(message, true);
  };

  const saveRename = async () => {
    const nextTitle = draftTitle.trim();
    if (!nextTitle || nextTitle === conversation.title) {
      setEditing(false);
      setDraftTitle(conversation.title);
      return;
    }

    setBusy(true);
    try {
      await renameConversation(conversation.id, nextTitle);
      setEditing(false);
    } catch (error) {
      handleError(error, "重命名失败");
    } finally {
      setBusy(false);
    }
  };

  const cancelRename = () => {
    setDraftTitle(conversation.title);
    setEditing(false);
  };

  const handleDelete = async () => {
    if (!window.confirm(`确定删除「${conversation.title}」吗？此操作不可恢复。`)) {
      return;
    }

    setBusy(true);
    try {
      await deleteConversation(conversation.id);
    } catch (error) {
      handleError(error, "删除失败");
    } finally {
      setBusy(false);
    }
  };

  const handleTitleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") {
      event.preventDefault();
      void saveRename();
    } else if (event.key === "Escape") {
      event.preventDefault();
      cancelRename();
    }
  };

  return (
    <div className={`conversation-item-wrap ${isActive ? "conversation-item-wrap-active" : ""}`}>
      {editing ? (
        <div className="conversation-item-edit">
          <MapPin className="conversation-item-icon" strokeWidth={1.75} aria-hidden />
          <input
            ref={inputRef}
            className="conversation-item-edit-input"
            value={draftTitle}
            maxLength={200}
            disabled={busy}
            aria-label="行程名称"
            onChange={(event) => setDraftTitle(event.target.value)}
            onKeyDown={handleTitleKeyDown}
          />
          <button
            type="button"
            className="conversation-item-action"
            aria-label="保存名称"
            disabled={busy}
            onClick={() => void saveRename()}
          >
            <Check strokeWidth={2} aria-hidden />
          </button>
          <button
            type="button"
            className="conversation-item-action"
            aria-label="取消重命名"
            disabled={busy}
            onClick={cancelRename}
          >
            <X strokeWidth={2} aria-hidden />
          </button>
        </div>
      ) : (
        <>
          <button
            type="button"
            className={`conversation-item ${isActive ? "conversation-item-active" : ""}`}
            aria-current={isActive ? "true" : undefined}
            disabled={busy}
            onClick={onSelect}
          >
            <MapPin className="conversation-item-icon" strokeWidth={1.75} aria-hidden />
            <span className="conversation-item-body">
              <span className="conversation-item-title">{conversation.title}</span>
              <span className="conversation-item-date">
                {formatConversationDate(conversation.updated_at)}
              </span>
            </span>
          </button>
          <div className="conversation-item-actions">
            <button
              type="button"
              className="conversation-item-action"
              aria-label={`重命名 ${conversation.title}`}
              disabled={busy}
              onClick={(event) => {
                event.stopPropagation();
                setEditing(true);
              }}
            >
              <Pencil strokeWidth={1.75} aria-hidden />
            </button>
            <button
              type="button"
              className="conversation-item-action conversation-item-action-danger"
              aria-label={`删除 ${conversation.title}`}
              disabled={busy}
              onClick={(event) => {
                event.stopPropagation();
                void handleDelete();
              }}
            >
              <Trash2 strokeWidth={1.75} aria-hidden />
            </button>
          </div>
        </>
      )}
    </div>
  );
}

type ConversationListProps = {
  conversations: ConversationResponse[];
  onSelect?: (conversationId: string) => void;
  className?: string;
};

export function ConversationList({
  conversations,
  onSelect,
  className,
}: ConversationListProps) {
  const currentConversationId = useChatStore((state) => state.currentConversationId);
  const setCurrentConversationId = useChatStore((state) => state.setCurrentConversationId);

  if (conversations.length === 0) {
    return (
      <p className={`conversation-list-empty ${className ?? ""}`.trim()}>
        暂无行程，点击上方按钮开始规划
      </p>
    );
  }

  return (
    <ul className={`conversation-list ${className ?? ""}`.trim()} role="list">
      {conversations.map((conversation) => {
        const isActive = conversation.id === currentConversationId;

        return (
          <li key={conversation.id}>
            <ConversationRow
              conversation={conversation}
              isActive={isActive}
              onSelect={() => {
                setCurrentConversationId(conversation.id);
                onSelect?.(conversation.id);
              }}
            />
          </li>
        );
      })}
    </ul>
  );
}
