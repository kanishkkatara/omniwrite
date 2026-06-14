"use client";

import styles from "./AgentProgress.module.css";
import { AgentStepStatus, type AgentStep } from "@/types/generation";
import { CheckCircle, XCircle } from "lucide-react";

interface AgentProgressProps {
  steps: AgentStep[];
}

function StatusIndicator({ status }: { status: AgentStepStatus }) {
  switch (status) {
    case AgentStepStatus.Running:
      return (
        <div className={styles.statusIcon}>
          <div className={`${styles.spinner} ${styles.spinnerGlow}`} />
        </div>
      );
    case AgentStepStatus.Done:
      return (
        <div className={styles.statusIcon}>
          <CheckCircle size={16} className={styles.checkIcon} />
        </div>
      );
    case AgentStepStatus.Error:
      return (
        <div className={styles.statusIcon}>
          <XCircle size={16} className={styles.errorIcon} />
        </div>
      );
    default:
      return (
        <div className={styles.statusIcon}>
          <div className={styles.statusDot} />
        </div>
      );
  }
}

export function AgentProgress({ steps }: AgentProgressProps) {
  const doneCount = steps.filter((s) => s.status === AgentStepStatus.Done).length;
  const totalCount = steps.length;
  const progressPct = totalCount > 0 ? Math.round((doneCount / totalCount) * 100) : 0;

  const runningStep = steps.find((s) => s.status === AgentStepStatus.Running);

  function stepClass(status: AgentStepStatus) {
    switch (status) {
      case AgentStepStatus.Running: return styles.stepRunning;
      case AgentStepStatus.Done: return styles.stepDone;
      case AgentStepStatus.Error: return styles.stepError;
      default: return styles.stepPending;
    }
  }

  if (steps.length === 0) return null;

  return (
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <span className={styles.title}>Agent Progress</span>
        <span className={styles.stepCount}>{doneCount}/{totalCount} complete</span>
      </div>

      {/* Progress bar */}
      <div className={styles.progressBar}>
        <div
          className={styles.progressFill}
          style={{ width: `${progressPct}%` }}
        />
      </div>

      {/* Steps */}
      <div className={styles.steps}>
        {steps.map((step, idx) => (
          <div
            key={step.id || step.name || idx}
            className={`${styles.step} ${stepClass(step.status)}`}
          >
            <StatusIndicator status={step.status} />
            <div className={styles.stepContent}>
              <div className={styles.stepName}>{step.name}</div>
              {step.message && (
                <div className={styles.stepMessage}>{step.message}</div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Current step message */}
      {runningStep?.message && (
        <div className={styles.currentMessage}>
          ⚡ {runningStep.message}
        </div>
      )}
    </div>
  );
}
