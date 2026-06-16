"use client";

import { useState } from "react";
import styles from "./GenerationSettingsModal.module.css";
import { ModelToggle } from "./ModelToggle";
import { TagsInput } from "@/components/ui/TagsInput";
import { useGenerationStore } from "@/lib/generationStore";
import { Platform, ContentLength, ModelMode, ReadingLevel, CtaType } from "@/types/generation";
import { X, Sliders, Layout, Cpu, Edit3 } from "lucide-react";

const PLATFORM_OPTIONS = [
  { value: Platform.Blog, label: "Blog Post", icon: "📝" },
  { value: Platform.Reddit, label: "Reddit Post", icon: "🤖" },
  { value: Platform.LinkedIn, label: "LinkedIn Post", icon: "💼" },
  { value: Platform.LinkedInComment, label: "LinkedIn Comment", icon: "💬" },
];

const LENGTH_LABELS = {
  [ContentLength.Short]: "Short",
  [ContentLength.Medium]: "Medium",
  [ContentLength.Long]: "Long",
};

const TEST_MODEL_PRESETS = [
  { value: "gpt-4.1-nano", label: "gpt-4.1-nano (Default)" },
  { value: "openai/gpt-4o-mini", label: "GPT-4o Mini" },
  { value: "anthropic/claude-3-5-haiku", label: "Claude 3.5 Haiku" },
  { value: "google/gemini-1.5-flash", label: "Gemini 1.5 Flash" },
  { value: "groq/llama3-8b-8192", label: "Llama 3 8B (Groq)" },
  { value: "custom", label: "Custom Model Name..." },
];

const PROD_MODEL_PRESETS = [
  { value: "claude-sonnet-4-5", label: "claude-sonnet-4-5 (Default)" },
  { value: "anthropic/claude-3-5-sonnet", label: "Claude 3.5 Sonnet" },
  { value: "openai/gpt-4o", label: "GPT-4o" },
  { value: "google/gemini-1.5-pro", label: "Gemini 1.5 Pro" },
  { value: "groq/llama3-70b-8192", label: "Llama 3 70B (Groq)" },
  { value: "custom", label: "Custom Model Name..." },
];

export function GenerationSettingsModal() {
  const {
    platforms: storePlatforms,
    contentLength: storeContentLength,
    modelMode: storeModelMode,
    testModel: storeTestModel,
    productionModel: storeProductionModel,
    seoKeywords: storeSeoKeywords,
    readingLevel: storeReadingLevel,
    ctaType: storeCtaType,
    subreddit: storeSubreddit,
    includeResearch: storeIncludeResearch,
    creativity: storeCreativity,
    variants: storeVariants,
    setConfigValue,
    setIsConfigModalOpen,
  } = useGenerationStore();

  // Local state for scratchpad configuration updates
  const [platforms, setPlatforms] = useState<Platform[]>(storePlatforms);
  const [contentLength, setContentLength] = useState<ContentLength>(storeContentLength);
  const [modelMode, setModelMode] = useState<ModelMode>(storeModelMode);
  const [seoKeywords, setSeoKeywords] = useState<string[]>(storeSeoKeywords);
  const [readingLevel, setReadingLevel] = useState<ReadingLevel>(storeReadingLevel);
  const [ctaType, setCtaType] = useState<CtaType>(storeCtaType);
  const [subreddit, setSubreddit] = useState<string>(storeSubreddit);
  const [includeResearch, setIncludeResearch] = useState<boolean>(storeIncludeResearch);
  const [creativity, setCreativity] = useState<number>(storeCreativity);
  const [variants, setVariants] = useState<number>(storeVariants);

  // Check if initial models are presets or custom
  const isCustomTestInit = !TEST_MODEL_PRESETS.slice(0, -1).some((m) => m.value === storeTestModel);
  const isCustomProdInit = !PROD_MODEL_PRESETS.slice(0, -1).some(
    (m) => m.value === storeProductionModel
  );

  const [selectedTestPreset, setSelectedTestPreset] = useState<string>(
    isCustomTestInit ? "custom" : storeTestModel
  );
  const [selectedProdPreset, setSelectedProdPreset] = useState<string>(
    isCustomProdInit ? "custom" : storeProductionModel
  );

  const [customTestVal, setCustomTestVal] = useState<string>(
    isCustomTestInit ? storeTestModel : ""
  );
  const [customProdVal, setCustomProdVal] = useState<string>(
    isCustomProdInit ? storeProductionModel : ""
  );

  const [testModel, setTestModel] = useState<string>(storeTestModel);
  const [productionModel, setProductionModel] = useState<string>(storeProductionModel);

  const togglePlatform = (p: Platform) => {
    setPlatforms((prev) => (prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p]));
  };

  const handleTestPresetChange = (val: string) => {
    setSelectedTestPreset(val);
    if (val !== "custom") {
      setTestModel(val);
    } else {
      setTestModel(customTestVal || "gpt-4.1-nano");
    }
  };

  const handleCustomTestChange = (val: string) => {
    setCustomTestVal(val);
    setTestModel(val);
  };

  const handleProdPresetChange = (val: string) => {
    setSelectedProdPreset(val);
    if (val !== "custom") {
      setProductionModel(val);
    } else {
      setProductionModel(customProdVal || "claude-sonnet-4-5");
    }
  };

  const handleCustomProdChange = (val: string) => {
    setCustomProdVal(val);
    setProductionModel(val);
  };

  const handleSave = () => {
    setConfigValue("platforms", platforms);
    setConfigValue("contentLength", contentLength);
    setConfigValue("modelMode", modelMode);
    setConfigValue("testModel", testModel);
    setConfigValue("productionModel", productionModel);
    setConfigValue("seoKeywords", seoKeywords);
    setConfigValue("readingLevel", readingLevel);
    setConfigValue("ctaType", ctaType);
    setConfigValue("subreddit", subreddit);
    setConfigValue("includeResearch", includeResearch);
    setConfigValue("creativity", creativity);
    setConfigValue("variants", variants);
    setIsConfigModalOpen(false);
  };

  const handleClose = () => {
    setIsConfigModalOpen(false);
  };

  const lengthValue =
    contentLength === ContentLength.Short ? 0 : contentLength === ContentLength.Medium ? 1 : 2;

  const lengthOptions = [ContentLength.Short, ContentLength.Medium, ContentLength.Long];

  return (
    <div className={styles.overlay} onClick={handleClose}>
      <div className={styles.modalContainer} onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <header className={styles.modalHeader}>
          <div className={styles.headerTitleArea}>
            <h2 className={styles.modalTitle}>
              <Sliders size={18} color="var(--color-primary)" />
              Pipeline Configuration
            </h2>
            <p className={styles.modalSubtitle}>
              Configure distribution channels, style preferences, and LLM parameters.
            </p>
          </div>
          <button className={styles.closeButton} onClick={handleClose} aria-label="Close settings">
            <X size={18} />
          </button>
        </header>

        {/* Modal Body */}
        <div className={styles.modalBody}>
          {/* Left Column: Format & Distribution */}
          <div className={styles.column}>
            <div className={styles.sectionTitle}>
              <Layout size={13} />
              Distribution & Format
            </div>

            {/* Target Platforms */}
            <div className={styles.fieldGroup}>
              <label className={styles.label}>Target Channels</label>
              <div className={styles.platformGrid}>
                {PLATFORM_OPTIONS.map((opt) => {
                  const isActive = platforms.includes(opt.value);
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      className={`${styles.platformBtn} ${isActive ? styles.platformBtnActive : ""}`}
                      onClick={() => togglePlatform(opt.value)}
                      aria-pressed={isActive}
                    >
                      <span className={styles.platformIcon}>{opt.icon}</span>
                      <span>{opt.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Conditional Subreddit Input */}
            {platforms.includes(Platform.Reddit) && (
              <div className={styles.fieldGroup} style={{ animation: "fadeIn 0.2s ease" }}>
                <label className={styles.label}>Target Subreddit</label>
                <input
                  className="input"
                  value={subreddit}
                  onChange={(e) => setSubreddit(e.target.value)}
                  placeholder="e.g. r/startups"
                />
              </div>
            )}

            {/* Content Length */}
            <div className={styles.fieldGroup}>
              <label className={styles.label}>
                Content Length:{" "}
                <span className={styles.labelValue}>{LENGTH_LABELS[contentLength]}</span>
              </label>
              <div className={styles.sliderWrapper}>
                <input
                  type="range"
                  className={styles.slider}
                  min={0}
                  max={2}
                  step={1}
                  value={lengthValue}
                  onChange={(e) => {
                    const v = lengthOptions[parseInt(e.target.value)];
                    setContentLength(v);
                  }}
                />
                <div className={styles.sliderLabels}>
                  <span className={styles.sliderLabel}>Short</span>
                  <span className={styles.sliderLabel}>Medium</span>
                  <span className={styles.sliderLabel}>Long</span>
                </div>
              </div>
            </div>

            {/* Call to Action & Reading Level Row */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              <div className={styles.fieldGroup}>
                <label className={styles.label}>Call to Action</label>
                <select
                  className="select"
                  value={ctaType}
                  onChange={(e) => setCtaType(e.target.value as CtaType)}
                >
                  <option value={CtaType.None}>No Call to Action</option>
                  <option value={CtaType.Subscribe}>Subscribe</option>
                  <option value={CtaType.LearnMore}>Learn More</option>
                  <option value={CtaType.ContactUs}>Contact Us</option>
                  <option value={CtaType.BuyNow}>Buy Now</option>
                  <option value={CtaType.GetStarted}>Get Started</option>
                </select>
              </div>

              <div className={styles.fieldGroup}>
                <label className={styles.label}>Reading Level</label>
                <select
                  className="select"
                  value={readingLevel}
                  onChange={(e) => setReadingLevel(e.target.value as ReadingLevel)}
                >
                  <option value={ReadingLevel.Beginner}>Beginner</option>
                  <option value={ReadingLevel.Intermediate}>Intermediate</option>
                  <option value={ReadingLevel.Expert}>Expert</option>
                </select>
              </div>
            </div>
          </div>

          {/* Right Column: AI Orchestration & Tuning */}
          <div className={styles.column}>
            <div className={styles.sectionTitle}>
              <Cpu size={13} />
              AI Orchestration
            </div>

            {/* Model Mode Toggle */}
            <div className={styles.fieldGroup}>
              <label className={styles.label}>Model Mode</label>
              <ModelToggle value={modelMode} onChange={setModelMode} />
            </div>

            {/* Model Presets Selection */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              <div className={styles.fieldGroup}>
                <label className={styles.label}>Test Model Mode</label>
                <select
                  className="select"
                  value={selectedTestPreset}
                  onChange={(e) => handleTestPresetChange(e.target.value)}
                >
                  {TEST_MODEL_PRESETS.map((m) => (
                    <option key={m.value} value={m.value}>
                      {m.label}
                    </option>
                  ))}
                </select>
                {selectedTestPreset === "custom" && (
                  <input
                    className="input"
                    style={{ marginTop: "6px", animation: "fadeIn 0.15s ease" }}
                    value={customTestVal}
                    onChange={(e) => handleCustomTestChange(e.target.value)}
                    placeholder="e.g. openai/gpt-4o-mini"
                  />
                )}
              </div>

              <div className={styles.fieldGroup}>
                <label className={styles.label}>Prod Model Mode</label>
                <select
                  className="select"
                  value={selectedProdPreset}
                  onChange={(e) => handleProdPresetChange(e.target.value)}
                >
                  {PROD_MODEL_PRESETS.map((m) => (
                    <option key={m.value} value={m.value}>
                      {m.label}
                    </option>
                  ))}
                </select>
                {selectedProdPreset === "custom" && (
                  <input
                    className="input"
                    style={{ marginTop: "6px", animation: "fadeIn 0.15s ease" }}
                    value={customProdVal}
                    onChange={(e) => handleCustomProdChange(e.target.value)}
                    placeholder="e.g. anthropic/claude-3-5-sonnet"
                  />
                )}
              </div>
            </div>

            {/* Web Research Toggle */}
            <div className={styles.toggleRow}>
              <div className={styles.toggleInfo}>
                <span className={styles.toggleLabel}>Deep Web Research</span>
                <span className={styles.toggleDesc}>
                  Perform web-search queries to fetch real-time facts and references.
                </span>
              </div>
              <label className={styles.toggle}>
                <input
                  type="checkbox"
                  className={styles.toggleInput}
                  checked={includeResearch}
                  onChange={(e) => setIncludeResearch(e.target.checked)}
                />
                <span className={styles.toggleSlider} />
              </label>
            </div>

            {/* Creativity Slider */}
            <div className={styles.fieldGroup}>
              <label className={styles.label}>
                Creativity: <span className={styles.labelValue}>{creativity}%</span>
              </label>
              <div className={styles.sliderWrapper}>
                <input
                  type="range"
                  className={styles.slider}
                  min={0}
                  max={100}
                  step={10}
                  value={creativity}
                  onChange={(e) => setCreativity(parseInt(e.target.value))}
                />
                <div className={styles.sliderLabels}>
                  <span className={styles.sliderLabel}>Conservative</span>
                  <span className={styles.sliderLabel}>Creative</span>
                </div>
              </div>
            </div>

            {/* SEO Keywords & Variants */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr auto",
                gap: "16px",
                alignItems: "flex-end",
              }}
            >
              <div className={styles.fieldGroup}>
                <label className={styles.label}>SEO Keywords</label>
                <TagsInput
                  tags={seoKeywords}
                  onChange={setSeoKeywords}
                  placeholder="Add keywords…"
                />
              </div>

              <div className={styles.fieldGroup}>
                <label className={styles.label}>Variants</label>
                <input
                  type="number"
                  className={styles.numberInput}
                  min={1}
                  max={5}
                  value={variants}
                  onChange={(e) =>
                    setVariants(Math.max(1, Math.min(5, parseInt(e.target.value) || 1)))
                  }
                />
              </div>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <footer className={styles.modalFooter}>
          <button className={styles.cancelBtn} onClick={handleClose}>
            Cancel
          </button>
          <button className={styles.saveBtn} onClick={handleSave}>
            Save Changes
          </button>
        </footer>
      </div>
    </div>
  );
}
