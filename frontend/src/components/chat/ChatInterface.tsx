"use client";

import { useState, useRef, useEffect } from "react";
import styles from "./ChatInterface.module.css";
import { useGenerationStore } from "@/lib/generationStore";
import { ChatMessage, Message } from "./ChatMessage";
import { AgentProgress } from "./AgentProgress";
import { OutlineApproval } from "./OutlineApproval";
import { ArrowUp, Sparkles, Plus, X, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { JobStatus } from "@/types/generation";

export function ChatInterface() {
  const {
    tabs,
    activeTabId,
    addTab,
    removeTab,
    setActiveTab,
    addMessage,
    setTopic,
    startJob,
  } = useGenerationStore();

  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const activeTab = tabs.find((t) => t.id === activeTabId) || tabs[0];
  const { messages, steps, jobStatus, outline, currentJobId, error, isStreaming } = activeTab;

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

    addMessage(activeTab.id, userMessage);
    const originalInput = input;
    setInput("");

    // Set topic in Zustand store for active tab (also sets tab title)
    setTopic(originalInput);

    try {
      // Trigger decoupled job generation
      await startJob();

      const agentInitMessage: Message = {
        id: Math.random().toString(),
        role: "agent",
        content: `I've started the generation pipeline for: **"${originalInput}"**.\n\nRunning agents now...`,
        timestamp: new Date(),
      };
      addMessage(activeTab.id, agentInitMessage);
    } catch (e: any) {
      addMessage(activeTab.id, {
        id: Math.random().toString(),
        role: "agent",
        content: `Sorry, I failed to start the generation: ${e?.message || e || "Unknown error"}`,
        timestamp: new Date(),
      });
    }
  };

  const handleOutlineApproved = () => {
    addMessage(activeTab.id, {
      id: Math.random().toString(),
      role: "agent",
      content: "Outline approved! Writers have been dispatched to craft the platform posts.",
      timestamp: new Date(),
    });
  };

  const showWelcome = messages.length === 0;

  return (
    <div className={styles.container}>
      {/* Scrollable Tab Bar */}
      <div className={styles.tabBar}>
        <div className={styles.tabsListScrollable}>
          {tabs.map((tab) => {
            const isActive = tab.id === activeTabId;
            return (
              <button
                key={tab.id}
                className={`${styles.tabButton} ${isActive ? styles.tabButtonActive : ""}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <div className={styles.tabStatus}>
                  {tab.isStreaming ? (
                    <Loader2 size={12} className="animate-spin" style={{ color: "var(--color-primary)" }} />
                  ) : tab.jobStatus === JobStatus.Completed ? (
                    <CheckCircle2 size={12} style={{ color: "var(--color-success)" }} />
                  ) : tab.jobStatus === JobStatus.Failed ? (
                    <AlertCircle size={12} style={{ color: "var(--color-error)" }} />
                  ) : (
                    <div
                      style={{
                        width: 5,
                        height: 5,
                        borderRadius: "50%",
                        background: "var(--color-text-secondary)",
                        opacity: 0.4,
                      }}
                    />
                  )}
                </div>
                <span className={styles.tabTitle}>{tab.title || "New Run"}</span>
                {tabs.length > 1 && (
                  <span
                    className={styles.closeBtn}
                    onClick={(e) => {
                      e.stopPropagation();
                      removeTab(tab.id);
                    }}
                  >
                    <X size={10} />
                  </span>
                )}
              </button>
            );
          })}
        </div>
        <button
          className={styles.addTabBtn}
          onClick={() => addTab()}
          title="Create new generation tab"
        >
          <Plus size={14} />
        </button>
      </div>

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
              Enter a topic, draft, or brief. The agentic workflow will research, strategize,
              outline, and write for all your platforms.
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
                onClick={() =>
                  handleExampleClick("The ultimate guide to Zustand for state management")
                }
              >
                Zustand vs Redux
              </button>
              <button
                className={styles.exampleChip}
                onClick={() =>
                  handleExampleClick("How to build a top tier open source AI product in 2026")
                }
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
            placeholder="Type a topic or brief, e.g., 'The future of developer tools'..."
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
