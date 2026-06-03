import { MessageSquare } from "lucide-react";
import { useEffect } from "react";

import { ChatMain } from "@/components/chat/ChatMain";
import { AppShell } from "@/components/layout/AppShell";
import { Sidebar } from "@/components/sidebar/Sidebar";
import { useToast } from "@/hooks/useToast";
import { ApiError } from "@/lib/api";
import { isUnauthorizedStatus } from "@/lib/authSession";
import { useChatStore } from "@/stores/chatStore";

export default function HomePage() {
  const loadConversations = useChatStore((state) => state.loadConversations);
  const currentConversationId = useChatStore((state) => state.currentConversationId);
  const conversations = useChatStore((state) => state.conversations);
  const { showToast } = useToast();

  useEffect(() => {
    void loadConversations().catch((error: unknown) => {
      if (error instanceof ApiError && isUnauthorizedStatus(error.status)) {
        return;
      }
      const message =
        error instanceof ApiError
          ? error.message
          : error instanceof Error
            ? error.message
            : "加载行程列表失败";
      showToast(message, true);
    });
  }, [loadConversations, showToast]);

  const currentConversation = conversations.find(
    (conversation) => conversation.id === currentConversationId,
  );

  return (
    <AppShell sidebar={<Sidebar />}>
      <main className="main-content flex flex-1">
        {currentConversation ? (
          <ChatMain
            conversationId={currentConversation.id}
            title={currentConversation.title}
          />
        ) : (
          <div className="chat-empty-state">
            <div className="chat-placeholder glass-card">
              <MessageSquare
                className="chat-placeholder-icon"
                strokeWidth={1.5}
                aria-hidden
              />
              <h2 className="font-serif-brand chat-placeholder-title">选择或创建行程</h2>
              <p className="chat-placeholder-text">
                从左侧选择已有行程，或点击「规划新行程」开始
              </p>
            </div>
          </div>
        )}
      </main>
    </AppShell>
  );
}
