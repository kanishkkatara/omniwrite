"use client";

import { useState } from "react";
import styles from "./OutlineApproval.module.css";
import { approveOutline } from "@/lib/api";
import { type OutlineData } from "@/types/generation";
import { CheckCheck, Edit3, RefreshCw, Loader2, FileText } from "lucide-react";

interface OutlineApprovalProps {
  jobId: string;
  outline: OutlineData | string;
  onApproved: () => void;
}

function outlineToText(outline: OutlineData | string | null | undefined): string {
  if (!outline) return "";
  if (typeof outline === "string") return outline;
  if ((outline as any).outline) return (outline as any).outline;
  if (outline.raw) return outline.raw;
  if (outline.sections) {
    return outline.sections
      .map((s) => {
        let text = `## ${s.title}`;
        if (s.description) text += `\n${s.description}`;
        if (s.subsections?.length) {
          text += "\n" + s.subsections.map((sub) => `  - ${sub}`).join("\n");
        }
        return text;
      })
      .join("\n\n");
  }
  return "";
}

export function OutlineApproval({ jobId, outline, onApproved }: OutlineApprovalProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedText, setEditedText] = useState(outlineToText(outline));
  const [isApproving, setIsApproving] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);

  const handleApprove = async () => {
    setIsApproving(true);
    try {
      await approveOutline(jobId, true, isEditing ? editedText : undefined);
      onApproved();
    } catch (e) {
      console.error("Approve outline failed:", e);
    } finally {
      setIsApproving(false);
    }
  };

  const handleRegenerate = async () => {
    setIsRegenerating(true);
    try {
      await approveOutline(jobId, false);
    } catch (e) {
      console.error("Regenerate outline failed:", e);
    } finally {
      setIsRegenerating(false);
    }
  };

  return (
    <div className={styles.card}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <div className={styles.headerIcon}>
            <FileText size={14} color="white" />
          </div>
          <div>
            <div className={styles.headerTitle}>Content Outline Ready</div>
            <div className={styles.headerSub}>Review and approve to start writing</div>
          </div>
        </div>
        <div className={styles.pulseBadge}>
          <span className={styles.pulseDot} />
          Awaiting approval
        </div>
      </div>

      {/* Outline content */}
      <div className={styles.outlineContent}>
        {isEditing ? (
          <textarea
            className={styles.editArea}
            value={editedText}
            onChange={(e) => setEditedText(e.target.value)}
            autoFocus
          />
        ) : !outline ? (
          <div className="text-muted italic">Empty outline</div>
        ) : typeof outline === "string" ? (
          <pre className={styles.outlineText}>{outline}</pre>
        ) : (outline as any).outline ? (
          <pre className={styles.outlineText}>{(outline as any).outline}</pre>
        ) : outline.raw ? (
          <pre className={styles.outlineText}>{outline.raw}</pre>
        ) : outline.sections ? (
          outline.sections.map((section, i) => (
            <div key={i} className={styles.section}>
              <div className={styles.sectionTitle}>
                <span className={styles.sectionBullet} />
                {section.title}
              </div>
              {section.description && (
                <div className={styles.sectionDesc}>{section.description}</div>
              )}
              {section.subsections?.map((sub, j) => (
                <div key={j} className={styles.subsection}>
                  {sub}
                </div>
              ))}
            </div>
          ))
        ) : (
          <div className="text-muted italic">Empty outline</div>
        )}
      </div>

      {/* Actions */}
      <div className={styles.actions}>
        <button
          className={styles.approveBtn}
          onClick={handleApprove}
          disabled={isApproving || isRegenerating}
        >
          {isApproving ? (
            <>
              <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> Writing…
            </>
          ) : (
            <>
              <CheckCheck size={14} /> Approve &amp; Write
            </>
          )}
        </button>

        <button
          className={`${styles.editBtn} ${isEditing ? styles.editBtnActive : ""}`}
          onClick={() => setIsEditing((v) => !v)}
          disabled={isApproving || isRegenerating}
        >
          <Edit3 size={13} />
          {isEditing ? "Done editing" : "Edit"}
        </button>

        <button
          className={styles.regenBtn}
          onClick={handleRegenerate}
          disabled={isApproving || isRegenerating}
        >
          {isRegenerating ? (
            <Loader2 size={13} style={{ animation: "spin 1s linear infinite" }} />
          ) : (
            <RefreshCw size={13} />
          )}
          Regenerate
        </button>
      </div>
    </div>
  );
}
