"use client";

import styles from "./ModelToggle.module.css";
import { ModelMode } from "@/types/generation";
import { Zap, Sparkles } from "lucide-react";

interface ModelToggleProps {
  value: ModelMode;
  onChange: (mode: ModelMode) => void;
}

export function ModelToggle({ value, onChange }: ModelToggleProps) {
  return (
    <div>
      <div className={styles.toggle}>
        {/* TEST */}
        <button
          type="button"
          className={`${styles.card} ${styles.cardTest} ${value === ModelMode.Test ? styles.cardSelected : ""}`}
          onClick={() => onChange(ModelMode.Test)}
          aria-pressed={value === ModelMode.Test}
        >
          <div className={styles.cardHeader}>
            <span className={styles.cardIcon}><Zap size={14} color={value === ModelMode.Test ? "var(--color-accent)" : "var(--color-muted)"} /></span>
            <span className={styles.cardLabel} style={{ color: value === ModelMode.Test ? "var(--color-accent)" : "var(--color-text)" }}>
              TEST
            </span>
          </div>
          <span className={styles.cardModel}>gpt-4.1-nano</span>
          <span className={`${styles.cardCost} ${styles.cardTestCost}`}>~$0.001–0.01</span>
        </button>

        {/* PRODUCTION */}
        <button
          type="button"
          className={`${styles.card} ${styles.cardProduction} ${value === ModelMode.Production ? styles.cardSelected : ""}`}
          onClick={() => onChange(ModelMode.Production)}
          aria-pressed={value === ModelMode.Production}
        >
          <div className={styles.cardHeader}>
            <span className={styles.cardIcon}><Sparkles size={14} color={value === ModelMode.Production ? "var(--color-primary-light)" : "var(--color-muted)"} /></span>
            <span className={styles.cardLabel} style={{ color: value === ModelMode.Production ? "var(--color-primary-light)" : "var(--color-text)" }}>
              PROD
            </span>
          </div>
          <span className={styles.cardModel}>claude-sonnet</span>
          <span className={`${styles.cardCost} ${styles.cardProdCost}`}>~$0.05–0.50</span>
        </button>
      </div>
      <p className={styles.costNote}>
        Estimated cost per generation run
      </p>
    </div>
  );
}
