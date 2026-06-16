"use client";

import { useCallback } from "react";
import styles from "./GenerationSettings.module.css";
import { ModelToggle } from "./ModelToggle";
import { TagsInput } from "@/components/ui/TagsInput";
import { useGenerationStore } from "@/lib/generationStore";
import {
  Platform,
  ContentLength,
  ModelMode,
  ReadingLevel,
  CtaType,
} from "@/types/generation";

const PLATFORM_OPTIONS = [
  { value: Platform.Blog, label: "Blog", icon: "📝" },
  { value: Platform.Reddit, label: "Reddit", icon: "🤖" },
  { value: Platform.LinkedIn, label: "LinkedIn", icon: "💼" },
  { value: Platform.LinkedInComment, label: "LI Comment", icon: "💬" },
];

const LENGTH_LABELS = {
  [ContentLength.Short]: "Short",
  [ContentLength.Medium]: "Medium",
  [ContentLength.Long]: "Long",
};

export function GenerationSettings() {
  const {
    platforms,
    contentLength,
    modelMode,
    seoKeywords,
    readingLevel,
    ctaType,
    subreddit,
    includeResearch,
    creativity,
    variants,
    setConfigValue,
  } = useGenerationStore();

  const togglePlatform = (p: Platform) => {
    const next = platforms.includes(p)
      ? platforms.filter((x) => x !== p)
      : [...platforms, p];
    setConfigValue("platforms", next);
  };

  const lengthValue =
    contentLength === ContentLength.Short ? 0
    : contentLength === ContentLength.Medium ? 1
    : 2;

  const lengthOptions = [ContentLength.Short, ContentLength.Medium, ContentLength.Long];

  return (
    <div className={styles.settings}>
      {/* Platforms */}
      <div className={styles.fieldGroup}>
        <label className={styles.label}>Platforms</label>
        <div className={styles.platformGrid}>
          {PLATFORM_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              className={`${styles.platformBtn} ${platforms.includes(opt.value) ? styles.platformBtnActive : ""}`}
              onClick={() => togglePlatform(opt.value)}
              aria-pressed={platforms.includes(opt.value)}
            >
              <span className={styles.platformIcon}>{opt.icon}</span>
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content Length */}
      <div className={styles.fieldGroup}>
        <label className={styles.label}>
          Content Length — <strong style={{ color: "var(--color-text)" }}>{LENGTH_LABELS[contentLength]}</strong>
        </label>
        <div className={styles.sliderWrapper}>
          <input
            type="range"
            className={styles.slider}
            min={0} max={2} step={1}
            value={lengthValue}
            onChange={(e) => {
              const v = lengthOptions[parseInt(e.target.value)];
              setConfigValue("contentLength", v);
            }}
          />
          <div className={styles.sliderLabels}>
            <span className={styles.sliderLabel}>Short</span>
            <span className={styles.sliderLabel}>Medium</span>
            <span className={styles.sliderLabel}>Long</span>
          </div>
        </div>
      </div>

      {/* SEO Keywords */}
      <div className={styles.fieldGroup}>
        <label className={styles.label}>SEO Keywords</label>
        <TagsInput
          tags={seoKeywords}
          onChange={(tags) => setConfigValue("seoKeywords", tags)}
          placeholder="content marketing, AI tools…"
        />
      </div>

      {/* Reading Level */}
      <div className={styles.fieldGroup}>
        <label className={styles.label}>Reading Level</label>
        <select
          className="select"
          value={readingLevel}
          onChange={(e) => setConfigValue("readingLevel", e.target.value as ReadingLevel)}
        >
          <option value={ReadingLevel.Beginner}>Beginner</option>
          <option value={ReadingLevel.Intermediate}>Intermediate</option>
          <option value={ReadingLevel.Expert}>Expert</option>
        </select>
      </div>

      {/* CTA Type */}
      <div className={styles.fieldGroup}>
        <label className={styles.label}>Call to Action</label>
        <select
          className="select"
          value={ctaType}
          onChange={(e) => setConfigValue("ctaType", e.target.value as CtaType)}
        >
          <option value={CtaType.None}>No CTA</option>
          <option value={CtaType.Subscribe}>Subscribe</option>
          <option value={CtaType.LearnMore}>Learn More</option>
          <option value={CtaType.ContactUs}>Contact Us</option>
          <option value={CtaType.BuyNow}>Buy Now</option>
          <option value={CtaType.GetStarted}>Get Started</option>
        </select>
      </div>

      {/* Subreddit (if Reddit selected) */}
      {platforms.includes(Platform.Reddit) && (
        <div className={styles.fieldGroup}>
          <label className={styles.label}>Subreddit</label>
          <input
            className="input"
            value={subreddit}
            onChange={(e) => setConfigValue("subreddit", e.target.value)}
            placeholder="r/startups"
          />
        </div>
      )}

      <div className={styles.divider} />
      <div className={styles.sectionLabel}>Advanced</div>

      {/* Include Research toggle */}
      <div className={styles.toggleRow}>
        <span className={styles.toggleLabel}>Web Research 🔍</span>
        <label className={styles.toggle}>
          <input
            type="checkbox"
            className={styles.toggleInput}
            checked={includeResearch}
            onChange={(e) => setConfigValue("includeResearch", e.target.checked)}
          />
          <span className={styles.toggleSlider} />
        </label>
      </div>

      {/* Creativity Slider */}
      <div className={styles.fieldGroup}>
        <label className={styles.label}>
          Creativity — <strong style={{ color: "var(--color-text)" }}>{creativity}%</strong>
        </label>
        <div className={styles.sliderWrapper}>
          <input
            type="range"
            className={styles.slider}
            min={0} max={100} step={10}
            value={creativity}
            onChange={(e) => setConfigValue("creativity", parseInt(e.target.value))}
          />
          <div className={styles.sliderLabels}>
            <span className={styles.sliderLabel}>Conservative</span>
            <span className={styles.sliderLabel}>Creative</span>
          </div>
        </div>
      </div>

      {/* Variants */}
      <div className={styles.toggleRow}>
        <span className={styles.toggleLabel}>Variants</span>
        <input
          type="number"
          className={styles.numberInput}
          min={1} max={5}
          value={variants}
          onChange={(e) => setConfigValue("variants", Math.max(1, Math.min(5, parseInt(e.target.value) || 1)))}
        />
      </div>

      <div className={styles.divider} />
      <div className={styles.sectionLabel}>Model Mode</div>

      {/* Model Toggle */}
      <ModelToggle
        value={modelMode}
        onChange={(mode) => setConfigValue("modelMode", mode)}
      />
    </div>
  );
}
