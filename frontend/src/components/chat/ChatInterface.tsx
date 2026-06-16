"use client";

import { useState, useRef, useEffect } from "react";
import styles from "./ChatInterface.module.css";
import { useGenerationStore } from "@/lib/generationStore";
import { ChatMessage, Message } from "./ChatMessage";
import { AgentProgress } from "./AgentProgress";
import { ArrowUp, Sparkles, Plus, X, Loader2, CheckCircle2, AlertCircle, Terminal, ChevronDown, ChevronUp } from "lucide-react";
import { JobStatus, Platform } from "@/types/generation";
import { streamChatWithContent } from "@/lib/api";

export function ChatInterface() {
  const {
    tabs,
    activeTabId,
    addTab,
    removeTab,
    setActiveTab,
    addMessage,
    updateMessage,
    setTopic,
    startJob,
    setIsStreaming,
    setStatus,
    setOutput,
    connectTabStream,
    updateTab,
  } = useGenerationStore();

  const [input, setInput] = useState("");
  const [consoleOpen, setConsoleOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const activeTab = tabs.find((t) => t.id === activeTabId) || tabs[0];
  const { messages, steps, jobStatus, outline, currentJobId, error, isStreaming } = activeTab;

  const activePlatform = activeTab.activePlatform || Platform.Blog;
  const platformLabels: Record<Platform, string> = {
    [Platform.Blog]: "Blog Post",
    [Platform.Reddit]: "Reddit Adapt",
    [Platform.LinkedIn]: "LinkedIn Post",
    [Platform.LinkedInComment]: "First Comment",
  };
  const activePlatformLabel = platformLabels[activePlatform] || activePlatform;

  const isInputDisabled = !input.trim() || isStreaming || jobStatus === JobStatus.AwaitingOutlineApproval;

  const placeholderText =
    jobStatus === JobStatus.AwaitingOutlineApproval
      ? "Please review and approve the outline in the right panel first..."
      : isStreaming
      ? "AI is writing... Please wait."
      : currentJobId
      ? `Ask for changes to the active platform content (${activePlatformLabel})...`
      : "Type a topic or brief, e.g., 'The future of developer tools'...";

  // Set up auto-scrolling
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, steps]);

  const handleExampleClick = (example: string) => {
    setInput(example);
  };

  const handleSend = async () => {
    if (!input.trim() || isStreaming || jobStatus === JobStatus.AwaitingOutlineApproval) return;

    const userMessage: Message = {
      id: Math.random().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    addMessage(activeTab.id, userMessage);
    const originalInput = input;
    setInput("");

    const typingMsgId = `typing-${Date.now()}`;
    addMessage(activeTab.id, {
      id: typingMsgId,
      role: "agent",
      content: "",
      timestamp: new Date(),
      isTyping: true,
    });

    // If currentJobId exists, treat the send action as platform regeneration feedback
    if (currentJobId) {
      const activePlatform = activeTab.activePlatform || Platform.Blog;
      const platformLabels: Record<Platform, string> = {
        [Platform.Blog]: "Blog Post",
        [Platform.Reddit]: "Reddit Adapt",
        [Platform.LinkedIn]: "LinkedIn Post",
        [Platform.LinkedInComment]: "First Comment",
      };
      const activePlatformLabel = platformLabels[activePlatform] || activePlatform;

      try {
        setIsStreaming(true);

        let responseType: "chat" | "update" | null = null;
        let accumulatedContent = "";

        // Call the streaming chat & classification endpoint
        await streamChatWithContent(
          currentJobId,
          {
            message: originalInput,
            active_platform: activePlatform,
          },
          (chunk) => {
            if (!responseType) {
              responseType = chunk.response_type;

              if (responseType === "update") {
                setStatus(JobStatus.Running);

                // Update store state with placeholder while background agents work
                setOutput({
                  platform: activePlatform,
                  content: "*Regenerating content based on feedback... Please wait.*",
                });

                // Update the typing bubble — safe: uses fresh state via updateMessage
                updateTab(activeTab.id, { activeMessageId: typingMsgId });
                updateMessage(activeTab.id, typingMsgId, {
                  content: `I'm revising the **${activePlatformLabel}** content based on your feedback: "${originalInput}"...`,
                  isTyping: true,
                });

                // Connect SSE stream to receive live progress logs
                connectTabStream(activeTab.id, currentJobId);
              }
            }

            if (responseType === "chat") {
              accumulatedContent += chunk.content;
              // Safe update: updateMessage reads from fresh store state
              updateMessage(activeTab.id, typingMsgId, {
                content: accumulatedContent,
                isTyping: false,
              });
            }
          }
        );

        if (responseType === "chat") {
          setIsStreaming(false);
        }
      } catch (e: any) {
        setIsStreaming(false);
        updateMessage(activeTab.id, typingMsgId, {
          content: `Failed to revise content: ${e?.message || e || "Unknown error"}`,
          isTyping: false,
        });
      }
      return;
    }

    // Otherwise, this is a new job (start first time)
    // Set topic in Zustand store for active tab (also sets tab title)
    setTopic(originalInput);

    try {
      // Track this bubble message for streaming pipeline steps
      updateTab(activeTab.id, { activeMessageId: typingMsgId });

      // Trigger decoupled job generation
      await startJob();

      // Update the typing message to notify that generation is active, but keep isTyping: true
      updateMessage(activeTab.id, typingMsgId, {
        content: `I've started the generation pipeline for: **"${originalInput}"**...`,
        isTyping: true,
      });
    } catch (e: any) {
      updateMessage(activeTab.id, typingMsgId, {
        content: `Sorry, I failed to start the generation: ${e?.message || e || "Unknown error"}`,
        isTyping: false,
      });
    }
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
        <>
          {/* Collapsible Agent Console — sits above messages, collapsed by default */}
          {steps.length > 0 && (
            <div className={styles.consoleTray}>
              <button
                className={styles.consoleTrayToggle}
                onClick={() => setConsoleOpen((v) => !v)}
              >
                <Terminal size={12} />
                <span>Agent Console</span>
                <span className={styles.consoleTrayStepCount}>{steps.length} step{steps.length !== 1 ? "s" : ""}</span>
                {consoleOpen ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
              </button>
              {consoleOpen && (
                <div className={styles.consoleTrayBody}>
                  <AgentProgress steps={steps} />
                </div>
              )}
            </div>
          )}

          <div className={styles.messages}>
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}

            {error && (
              <div className="alert alert-error" style={{ margin: "12px 0" }}>
                {error}
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </>
      )}

      {/* Input area */}
      <div className={styles.inputArea}>
        <div className={styles.inputWrapper}>
          <textarea
            className={styles.textarea}
            placeholder={placeholderText}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isStreaming || jobStatus === JobStatus.AwaitingOutlineApproval}
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
              disabled={isInputDisabled}
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
