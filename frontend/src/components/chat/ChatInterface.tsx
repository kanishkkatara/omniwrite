"use client";

import { useState, useRef, useEffect } from "react";
import styles from "./ChatInterface.module.css";
import { useGenerationStore } from "@/lib/generationStore";
import { useJobStream } from "@/lib/hooks/useJobStream";
import { ChatMessage, Message } from "./ChatMessage";
import { AgentProgress } from "./AgentProgress";
import { OutlineApproval } from "./OutlineApproval";
import { ArrowUp, Sparkles, Clipboard, Check } from "lucide-react";
import { JobStatus } from "@/types/generation";

export function ChatInterface() {
  const {
    currentJobId,
    startJob,
    topic,
    isStreaming,
    error,
    jobStatus,
  } = useGenerationStore();

  const { steps, outline } = useJobStream(currentJobId);

  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Set up auto-scrolling
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, steps]);

  const handleExampleClick = (example: string) => {
    setInput(example);
  };

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return;

    const userMessage: Message = {
      id: Math.random().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const originalInput = input;
    setInput("");

    try {
      const jobId = await startJob({
        topic: originalInput,
        platforms: ["blog", "linkedin", "reddit", "linkedin_comment"] as any,
      });

      const agentInitMessage: Message = {
        id: Math.random().toString(),
        role: "agent",
        content: `I've started the generation pipeline for: **"${originalInput}"**.\n\nRunning agents now...`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, agentInitMessage]);
    } catch (e: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: Math.random().toString(),
          role: "agent",
          content: `Sorry, I failed to start the generation: ${e?.message || e || "Unknown error"}`,
          timestamp: new Date(),
        },
      ]);
    }
  };

  const handleOutlineApproved = () => {
    setMessages((prev) => [
      ...prev,
      {
        id: Math.random().toString(),
        role: "agent",
        content: "Outline approved! Writers have been dispatched to craft the platform posts.",
        timestamp: new Date(),
      },
    ]);
  };

  const showWelcome = messages.length === 0;

  return (
    <div className={styles.container}>
      {showWelcome ? (
        <div className={styles.welcome}>
          <div className={styles.welcomeBg} />
          <div className={styles.welcomeGlowOrb} />
          <div className={styles.welcomeContent}>
            <div className={styles.welcomeIconWrapper}>
              <Sparkles size={32} color="white" />
            </div>
            <h1 className={styles.welcomeTitle}>Create Outstanding Content</h1>
            <p className={styles.welcomeSub}>
              Enter a topic, draft, or brief. The agentic workflow will research, strategize, outline, and write for all your platforms.
            </p>
            <div className={styles.exampleChips}>
              <button
                className={styles.exampleChip}
                onClick={() => handleExampleClick("Why RAG is broken at scale, and how to fix it")}
              >
                RAG scale issues
              </button>
              <button
                className={styles.exampleChip}
                onClick={() => handleExampleClick("The ultimate guide to Zustand for state management")}
              >
                Zustand vs Redux
              </button>
              <button
                className={styles.exampleChip}
                onClick={() => handleExampleClick("How to build a top tier open source AI product in 2026")}
              >
                OSS AI product
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className={styles.messages}>
          {messages.map((msg) => (
            <ChatMessage key={msg.id} message={msg} />
          ))}

          {/* Render Active Job Status & Progress */}
          {steps.length > 0 && <AgentProgress steps={steps} />}

          {/* Human-in-the-loop outline approval */}
          {jobStatus === JobStatus.AwaitingOutlineApproval && outline && currentJobId && (
            <OutlineApproval
              jobId={currentJobId}
              outline={outline}
              onApproved={handleOutlineApproved}
            />
          )}

          {error && (
            <div className="alert alert-error" style={{ margin: "12px 0" }}>
              {error}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      )}

      {/* Input area */}
      <div className={styles.inputArea}>
        <div className={styles.inputWrapper}>
          <textarea
            className={styles.textarea}
            placeholder="Type a topic or story, e.g., 'The future of developer tools'..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
          />
          <div className={styles.inputActions}>
            <button
              className={styles.sendBtn}
              onClick={handleSend}
              disabled={!input.trim() || isStreaming}
            >
              <ArrowUp size={18} />
            </button>
          </div>
        </div>
        <div className={styles.inputHint}>
          <span className={styles.hint}>Press Enter to send, Shift+Enter for new line</span>
          <span className={styles.charCount}>{input.length}/2000</span>
        </div>
      </div>
    </div>
  );
}
