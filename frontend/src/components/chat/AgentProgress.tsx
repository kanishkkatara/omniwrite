"use client";

import { useState, useEffect, useRef } from "react";
import styles from "./AgentProgress.module.css";
import { AgentStepStatus, type AgentStep } from "@/types/generation";
import { Terminal, ChevronDown, ChevronUp } from "lucide-react";

interface AgentProgressProps {
  steps: AgentStep[];
}

export function AgentProgress({ steps }: AgentProgressProps) {
  const [showLogs, setShowLogs] = useState(true);
  const consoleEndRef = useRef<HTMLDivElement>(null);

  const doneCount = steps.filter((s) => s.status === AgentStepStatus.Done).length;
  const totalCount = steps.length;
  const progressPct = totalCount > 0 ? Math.round((doneCount / totalCount) * 100) : 0;

  // Auto-scroll terminal to bottom when logs update
  useEffect(() => {
    if (showLogs) {
      consoleEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [steps, showLogs]);

  if (steps.length === 0) return null;

  // Generate ASCII progress bar e.g. [████████░░░░░░░░]
  const barLength = 20;
  const filledLength = Math.round((progressPct / 100) * barLength);
  const emptyLength = barLength - filledLength;
  const asciiBar = "█".repeat(filledLength) + "░".repeat(emptyLength);

  // Return a mock timestamp based on step index to simulate terminal logs
  const getLogTime = (idx: number) => {
    const time = new Date();
    time.setSeconds(time.getSeconds() - (steps.length - idx) * 3);
    return time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  return (
    <div className={styles.terminal}>
      {/* Title bar */}
      <div className={styles.titleBar}>
        <div className={styles.windowButtons}>
          <span className={`${styles.dot} ${styles.red}`} />
          <span className={`${styles.dot} ${styles.yellow}`} />
          <span className={`${styles.dot} ${styles.green}`} />
        </div>
        <div className={styles.consoleTitle}>
          <Terminal size={12} className={styles.terminalIcon} />
          <span>omniwrite-agent-console</span>
        </div>
        <button
          className={styles.toggleBtn}
          onClick={() => setShowLogs((v) => !v)}
          aria-expanded={showLogs}
        >
          {showLogs ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          <span>{showLogs ? "Collapse" : "Expand"}</span>
        </button>
      </div>

      {/* Terminal logs pane */}
      {showLogs && (
        <div className={styles.consoleBody}>
          {/* ASCII progress line */}
          <div className={styles.asciiProgressLine}>
            <span className={styles.prompt}>$</span>
            <span className={styles.logText}> omniwrite --status-pipeline</span>
          </div>
          <div className={styles.progressBarLine}>
            <span className={styles.barLabel}>Progress:</span>
            <span className={styles.bar}>[{asciiBar}]</span>
            <span className={styles.pct}>{progressPct}%</span>
            <span className={styles.count}>({doneCount}/{totalCount})</span>
          </div>

          <div className={styles.divider} />

          {/* Scrolling log lines */}
          <div className={styles.logs}>
            {steps.map((step, idx) => {
              const timeStr = getLogTime(idx);
              let statusLabel = "[INFO]";
              let statusClass = styles.info;

              if (step.status === AgentStepStatus.Running) {
                statusLabel = "[RUNNING]";
                statusClass = styles.running;
              } else if (step.status === AgentStepStatus.Done) {
                statusLabel = "[SUCCESS]";
                statusClass = styles.success;
              } else if (step.status === AgentStepStatus.Error) {
                statusLabel = "[FAILED]";
                statusClass = styles.failed;
              } else if (step.status === AgentStepStatus.Pending) {
                statusLabel = "[WAITING]";
                statusClass = styles.waiting;
              }

              return (
                <div key={step.id || idx} className={styles.logLine}>
                  <span className={styles.timestamp}>[{timeStr}]</span>
                  <span className={`${styles.statusLabel} ${statusClass}`}>{statusLabel}</span>
                  <span className={styles.stepName}>{step.name}:</span>
                  <span className={styles.message}>
                    {step.status === AgentStepStatus.Running && !step.message
                      ? "processing node..."
                      : step.message || "node complete."}
                  </span>
                </div>
              );
            })}

            {/* Pulsing prompt cursor at the bottom if pipeline is running */}
            {progressPct < 100 && (
              <div className={styles.cursorLine}>
                <span className={styles.timestamp}>[{new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}]</span>
                <span className={styles.promptSymbol}>&gt;</span>
                <span className={styles.pulseCursor}>█</span>
              </div>
            )}
            <div ref={consoleEndRef} />
          </div>
        </div>
      )}
    </div>
  );
}
