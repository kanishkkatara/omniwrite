"use client";

import styles from "./VoiceSelector.module.css";
import { BrandVoice } from "@/types/brand";
import { Check } from "lucide-react";

const VOICE_OPTIONS: Array<{ value: BrandVoice; label: string; icon: string }> = [
  { value: BrandVoice.Authoritative, label: "Authoritative", icon: "🎯" },
  { value: BrandVoice.Conversational, label: "Conversational", icon: "💬" },
  { value: BrandVoice.Witty, label: "Witty", icon: "✨" },
  { value: BrandVoice.Empathetic, label: "Empathetic", icon: "💙" },
  { value: BrandVoice.Bold, label: "Bold", icon: "⚡" },
  { value: BrandVoice.Educational, label: "Educational", icon: "📚" },
  { value: BrandVoice.Inspirational, label: "Inspirational", icon: "🚀" },
  { value: BrandVoice.Professional, label: "Professional", icon: "💼" },
  { value: BrandVoice.Casual, label: "Casual", icon: "😊" },
  { value: BrandVoice.Humorous, label: "Humorous", icon: "😄" },
];

const MAX_SELECTIONS = 3;

interface VoiceSelectorProps {
  selected: BrandVoice[];
  onChange: (voices: BrandVoice[]) => void;
}

export function VoiceSelector({ selected, onChange }: VoiceSelectorProps) {
  const toggle = (voice: BrandVoice) => {
    if (selected.includes(voice)) {
      onChange(selected.filter((v) => v !== voice));
    } else if (selected.length < MAX_SELECTIONS) {
      onChange([...selected, voice]);
    }
  };

  return (
    <div>
      <div className={styles.voiceGrid}>
        {VOICE_OPTIONS.map((opt) => {
          const isSelected = selected.includes(opt.value);
          const isDisabled = !isSelected && selected.length >= MAX_SELECTIONS;
          return (
            <button
              key={opt.value}
              type="button"
              className={`${styles.voiceBtn} ${isSelected ? styles.voiceBtnSelected : ""}`}
              onClick={() => toggle(opt.value)}
              disabled={isDisabled}
              aria-pressed={isSelected}
              style={{ opacity: isDisabled ? 0.45 : 1 }}
            >
              <span className={styles.voiceIcon}>{opt.icon}</span>
              <span className={styles.voiceLabel}>{opt.label}</span>
              {isSelected && <Check size={12} className={styles.checkmark} />}
            </button>
          );
        })}
      </div>
      <p className={styles.maxHint}>
        Select up to {MAX_SELECTIONS} voices ({selected.length}/{MAX_SELECTIONS})
      </p>
    </div>
  );
}
