"use client";

import styles from "./ChatMessage.module.css";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export type MessageRole = "agent" | "user";

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  isTyping?: boolean;
}

interface ChatMessageProps {
  message: Message;
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isAgent = message.role === "agent";

  return (
    <div className={`${styles.messageWrapper} ${isAgent ? styles.messageWrapperAgent : styles.messageWrapperUser}`}>
      <div className={`${styles.message} ${isAgent ? styles.messageAgent : styles.messageUser}`}>
        {/* Avatar */}
        <div className={`${styles.avatar} ${isAgent ? styles.avatarAgent : styles.avatarUser}`}>
          {isAgent ? "✦" : "👤"}
        </div>

        {/* Bubble */}
        <div className={`${styles.bubble} ${isAgent ? styles.bubbleAgent : styles.bubbleUser}`}>
          {message.isTyping ? (
            <div className={styles.typingDots}>
              <span className={styles.dot} />
              <span className={styles.dot} />
              <span className={styles.dot} />
            </div>
          ) : (
            <div className={styles.bubbleContent}>
              {isAgent ? (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </ReactMarkdown>
              ) : (
                <span>{message.content}</span>
              )}
            </div>
          )}
          <div className={styles.timestamp}>{formatTime(message.timestamp)}</div>
        </div>
      </div>
    </div>
  );
}
