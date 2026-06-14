"use client";

import { useState, useCallback } from "react";
import styles from "./GenerationSettings.module.css";
import { ModelToggle } from "./ModelToggle";
import { TagsInput } from "@/components/ui/TagsInput";
import {
  Platform,
  ContentLength,
  ModelMode,
  ReadingLevel,
  CtaType,
} from "@/types/generation";

// We expose a way for ChatInterface to read these settings
// using a simple module-level singleton store approach
export interface GenerationConfig {
  platforms: Platform[];
  contentLength: ContentLength;
  modelMode: ModelMode;
  seoKeywords: string[];
  readingLevel: ReadingLevel;
  ctaType: CtaType;
  subreddit: string;
  includeResearch: boolean;
  creativity: number;
  variants: number;
}

// Module-level singleton for settings (shared without context overhead)
let _config: GenerationConfig = {
  platforms: [Platform.Blog, Platform.LinkedIn],
  contentLength: ContentLength.Medium,
  modelMode: ModelMode.Test,
  seoKeywords: [],
  readingLevel: ReadingLevel.Intermediate,
  ctaType: CtaType.None,
  subreddit: "",
  includeResearch: true,
  creativity: 50,
  variants: 1,
};

let _listeners: Array<() => void> = [];

export function getGenerationConfig(): GenerationConfig {
  return _config;
}

export function subscribeGenerationConfig(cb: () => void) {
  _listeners.push(cb);
  return () => { _listeners = _listeners.filter((l) => l !== cb); };
}

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
  const [platforms, setPlatforms] = useState<Platform[]>(_config.platforms);
  const [contentLength, setContentLength] = useState<ContentLength>(_config.contentLength);
  const [modelMode, setModelMode] = useState<ModelMode>(_config.modelMode);
  const [seoKeywords, setSeoKeywords] = useState<string[]>(_config.seoKeywords);
  const [readingLevel, setReadingLevel] = useState<ReadingLevel>(_config.readingLevel);
  const [ctaType, setCtaType] = useState<CtaType>(_config.ctaType);
  const [subreddit, setSubreddit] = useState<string>(_config.subreddit);
  const [includeResearch, setIncludeResearch] = useState<boolean>(_config.includeResearch);
  const [creativity, setCreativity] = useState<number>(_config.creativity);
  const [variants, setVariants] = useState<number>(_config.variants);

  const update = useCallback(<K extends keyof GenerationConfig>(
    key: K,
    value: GenerationConfig[K]
  ) => {
    _config = { ..._config, [key]: value };
    _listeners.forEach((l) => l());
  }, []);

  const togglePlatform = (p: Platform) => {
    const next = platforms.includes(p)
      ? platforms.filter((x) => x !== p)
      : [...platforms, p];
    setPlatforms(next);
    update("platforms", next);
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
              setContentLength(v);
              update("contentLength", v);
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
          onChange={(tags) => { setSeoKeywords(tags); update("seoKeywords", tags); }}
          placeholder="content marketing, AI tools…"
        />
      </div>

      {/* Reading Level */}
      <div className={styles.fieldGroup}>
        <label className={styles.label}>Reading Level</label>
        <select
          className="select"
          value={readingLevel}
          onChange={(e) => {
            const v = e.target.value as ReadingLevel;
            setReadingLevel(v);
            update("readingLevel", v);
          }}
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
          onChange={(e) => {
            const v = e.target.value as CtaType;
            setCtaType(v);
            update("ctaType", v);
          }}
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
            onChange={(e) => { setSubreddit(e.target.value); update("subreddit", e.target.value); }}
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
            onChange={(e) => {
              setIncludeResearch(e.target.checked);
              update("includeResearch", e.target.checked);
            }}
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
            onChange={(e) => {
              const v = parseInt(e.target.value);
              setCreativity(v);
              update("creativity", v);
            }}
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
          onChange={(e) => {
            const v = Math.max(1, Math.min(5, parseInt(e.target.value) || 1));
            setVariants(v);
            update("variants", v);
          }}
        />
      </div>

      <div className={styles.divider} />
      <div className={styles.sectionLabel}>Model Mode</div>

      {/* Model Toggle */}
      <ModelToggle
        value={modelMode}
        onChange={(mode) => { setModelMode(mode); update("modelMode", mode); }}
      />
    </div>
  );
}
