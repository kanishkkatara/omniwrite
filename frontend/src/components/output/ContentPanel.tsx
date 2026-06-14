"use client";

import { useState } from "react";
import styles from "./ContentPanel.module.css";
import { useGenerationStore } from "@/lib/generationStore";
import { regeneratePlatform } from "@/lib/api";
import { Platform } from "@/types/generation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Copy, Check, RefreshCw, Send, Loader2, Sparkles } from "lucide-react";

export function ContentPanel() {
  const {
    currentJobId,
    outputs,
    costSummary,
    jobStatus,
    setOutput,
  } = useGenerationStore();

  const [activeTab, setActiveTab] = useState<Platform>(Platform.Blog);
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [showFeedbackInput, setShowFeedbackInput] = useState(false);

  const activeOutput = outputs.find((o) => o.platform === activeTab);

  const handleCopy = async () => {
    if (!activeOutput?.content) return;
    try {
      await navigator.clipboard.writeText(activeOutput.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy text: ", err);
    }
  };

  const handleRegenerate = async () => {
    if (!currentJobId) return;
    setIsRegenerating(true);
    try {
      await regeneratePlatform(currentJobId, activeTab, feedback || undefined);
      setShowFeedbackInput(false);
      setFeedback("");
      
      // Since regenerate runs in background on API, we mock an update
      // or we can poll for updates.
      // For instant response we tell the user it is regenerating
      setOutput({
        platform: activeTab,
        content: "*Regenerating content based on feedback... Please wait.*",
      });
    } catch (e) {
      console.error("Regeneration failed:", e);
    } finally {
      setIsRegenerating(false);
    }
  };

  const hasOutputs = outputs.length > 0;

  const platforms = [
    { label: "Blog Post", value: Platform.Blog },
    { label: "Reddit Writeup", value: Platform.Reddit },
    { label: "LinkedIn Post", value: Platform.LinkedIn },
    { label: "First Comment", value: Platform.LinkedInComment },
  ];

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <div className={styles.title}>Generated Content</div>
      </div>

      {!hasOutputs ? (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>
            <Sparkles size={20} className="text-muted" />
          </div>
          <div className={styles.emptyText}>No content generated yet</div>
          <div className={styles.emptySub}>
            Start a new generation run in the chat interface to see your adaptions here.
          </div>
        </div>
      ) : (
        <>
          {/* Tabs */}
          <div className={styles.tabsList}>
            {platforms.map((p) => {
              const hasContent = outputs.some((o) => o.platform === p.value);
              return (
                <button
                  key={p.value}
                  className={`${styles.tabButton} ${
                    activeTab === p.value ? styles.tabButtonActive : ""
                  }`}
                  onClick={() => {
                    setActiveTab(p.value);
                    setShowFeedbackInput(false);
                  }}
                  disabled={!hasContent}
                  style={{ opacity: hasContent ? 1 : 0.4 }}
                >
                  {p.label}
                </button>
              );
            })}
          </div>

          {/* Body Viewer */}
          <div className={styles.scrollArea}>
            <div className={styles.toolbar}>
              <button
                className={`${styles.toolBtn} ${copied ? styles.copiedBtn : ""}`}
                onClick={handleCopy}
                disabled={!activeOutput?.content}
              >
                {copied ? <Check size={14} /> : <Copy size={14} />}
                {copied ? "Copied" : "Copy to Clipboard"}
              </button>

              <button
                className={styles.toolBtn}
                onClick={() => setShowFeedbackInput((v) => !v)}
                disabled={!activeOutput?.content || isRegenerating}
              >
                <RefreshCw size={14} />
                Regenerate platform
              </button>
            </div>

            {showFeedbackInput && (
              <div className={styles.feedbackPanel}>
                <textarea
                  className={styles.feedbackInput}
                  placeholder="Tell the AI what to improve or rewrite in this platform post..."
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                />
                <div className={styles.feedbackActions}>
                  <button
                    className="btn btn-ghost btn-xs"
                    onClick={() => setShowFeedbackInput(false)}
                  >
                    Cancel
                  </button>
                  <button
                    className="btn btn-primary btn-xs"
                    onClick={handleRegenerate}
                    disabled={isRegenerating}
                    style={{ gap: "4px" }}
                  >
                    {isRegenerating ? (
                      <Loader2 size={12} className="animate-spin" />
                    ) : (
                      <Send size={12} />
                    )}
                    Send Feedback
                  </button>
                </div>
              </div>
            )}

            <div className={styles.contentWrapper}>
              {activeOutput?.content ? (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {activeOutput.content}
                </ReactMarkdown>
              ) : (
                <span className="text-muted italic">Waiting for content generation...</span>
              )}
            </div>
          </div>

          {/* Footer stats */}
          {costSummary && (
            <div className={styles.footer}>
              <div className={styles.statGroup}>
                <div className={styles.statItem}>
                  <span className={styles.statLabel}>Model</span>
                  <span className={styles.statValue}>
                    {costSummary.model_used || "LiteLLM"}
                  </span>
                </div>
                <div className={styles.statItem}>
                  <span className={styles.statLabel}>Latency</span>
                  <span className={styles.statValue}>
                    {costSummary.total_duration_seconds
                      ? `${costSummary.total_duration_seconds.toFixed(1)}s`
                      : "—"}
                  </span>
                </div>
              </div>
              <div className={styles.costBadge}>
                ${costSummary.total_cost ? costSummary.total_cost.toFixed(4) : "0.00"}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
