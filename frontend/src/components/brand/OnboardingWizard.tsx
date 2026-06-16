"use client";

import { useState, useEffect } from "react";
import styles from "./OnboardingWizard.module.css";
import { useBrandStore } from "@/lib/brandStore";
import { VoiceSelector } from "./VoiceSelector";
import { TagsInput } from "@/components/ui/TagsInput";
import { useToast, ToastProvider } from "@/components/ui/Toast";
import { BrandVoice, WritingPerspective, Industry, type BrandProfileCreate } from "@/types/brand";
import { Check, ArrowRight, ArrowLeft, Loader2 } from "lucide-react";

const PERSPECTIVE_OPTIONS = [
  { value: WritingPerspective.FirstPersonSingular, label: "First Person", sub: "I, me, my" },
  { value: WritingPerspective.FirstPersonPlural, label: "We / Us", sub: "we, our" },
  { value: WritingPerspective.SecondPerson, label: "Second Person", sub: "you, your" },
  { value: WritingPerspective.ThirdPerson, label: "Third Person", sub: "they, the brand" },
];

const INDUSTRY_OPTIONS = [
  { value: Industry.Technology, label: "Technology" },
  { value: Industry.Healthcare, label: "Healthcare" },
  { value: Industry.Finance, label: "Finance" },
  { value: Industry.Education, label: "Education" },
  { value: Industry.Ecommerce, label: "E-Commerce" },
  { value: Industry.Marketing, label: "Marketing" },
  { value: Industry.SaaS, label: "SaaS" },
  { value: Industry.Media, label: "Media" },
  { value: Industry.Consulting, label: "Consulting" },
  { value: Industry.Retail, label: "Retail" },
  { value: Industry.Manufacturing, label: "Manufacturing" },
  { value: Industry.RealEstate, label: "Real Estate" },
  { value: Industry.Nonprofit, label: "Nonprofit" },
  { value: Industry.Legal, label: "Legal" },
  { value: Industry.Other, label: "Other" },
];

interface OnboardingWizardProps {
  onClose?: () => void;
}

export function OnboardingWizard({ onClose }: OnboardingWizardProps) {
  const { createBrand, updateBrand, getActiveBrand, isLoading } = useBrandStore();
  const toast = useToast();
  const activeBrand = getActiveBrand();

  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState<BrandProfileCreate>({
    name: "",
    tagline: "",
    industry: undefined,
    target_audience: [],
    brand_voice: [],
    writing_perspective: undefined,
    competitor_brands: [],
    avoid_topics: [],
    sample_content: "",
    website_url: "",
    custom_instructions: "",
  });

  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (activeBrand) {
      setFormData({
        name: activeBrand.name ?? "",
        tagline: activeBrand.tagline ?? "",
        industry: activeBrand.industry,
        target_audience: activeBrand.target_audience ?? [],
        brand_voice: activeBrand.brand_voice ?? [],
        writing_perspective: activeBrand.writing_perspective,
        competitor_brands: activeBrand.competitor_brands ?? [],
        avoid_topics: activeBrand.avoid_topics ?? [],
        sample_content: activeBrand.sample_content ?? "",
        website_url: activeBrand.website_url ?? "",
        custom_instructions: activeBrand.custom_instructions ?? "",
      });
    }
  }, [activeBrand]);

  const set = <K extends keyof BrandProfileCreate>(key: K, value: BrandProfileCreate[K]) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
  };

  const handleNext = () => {
    if (step === 1 && !formData.name.trim()) {
      toast.error("Brand name is required");
      return;
    }
    setStep((s) => Math.min(s + 1, 4));
  };

  const handleBack = () => {
    setStep((s) => Math.max(s - 1, 1));
  };

  const handleSave = async () => {
    if (!formData.name.trim()) {
      toast.error("Brand name is required");
      setStep(1);
      return;
    }
    setIsSaving(true);
    try {
      if (activeBrand) {
        await updateBrand(activeBrand.id, formData);
        toast.success("Brand updated successfully");
      } else {
        await createBrand(formData);
        toast.success("Brand connected successfully");
      }
      if (onClose) onClose();
    } catch {
      toast.error("Failed to connect brand. Is the API online?");
    } finally {
      setIsSaving(false);
    }
  };

  const steps = [
    { number: 1, name: "Core Identity", desc: "Define your company and niche" },
    { number: 2, name: "Voice & Tone", desc: "Select personality parameters" },
    { number: 3, name: "Audience & Site", desc: "Configure target segment & domain" },
    { number: 4, name: "Style & Guardrails", desc: "Avoid-lists and writing samples" },
  ];

  return (
    <div className={styles.overlay}>
      {/* Navigation */}
      <div className={styles.navbar}>
        <div className={styles.navLeft}>
          <div className={styles.logoMark}>✦</div>
          <span className={styles.navTitle}>Brand Connection Workspace</span>
        </div>
        {onClose && (
          <button className="btn-ghost btn-xs" onClick={onClose}>
            Close
          </button>
        )}
      </div>

      {/* Main Container */}
      <div className={styles.wizardContainer}>
        {/* Sidebar Stepper */}
        <div className={styles.stepperCol}>
          <span className={styles.stepperTitle}>Connection Steps</span>
          <div
            style={{ display: "flex", flexDirection: "column", gap: "36px", position: "relative" }}
          >
            {steps.map((s, idx) => {
              const isActive = step === s.number;
              const isCompleted = step > s.number;
              return (
                <div
                  key={s.number}
                  className={`${styles.stepLink} ${isActive ? styles.stepLinkActive : ""} ${
                    isCompleted ? styles.stepLinkCompleted : ""
                  }`}
                  onClick={() => setStep(s.number)}
                >
                  <div className={styles.stepIcon}>
                    {isCompleted ? <Check size={12} /> : s.number}
                  </div>
                  <div className={styles.stepDetails}>
                    <span className={styles.stepName}>{s.name}</span>
                    <span className={styles.stepDesc}>{s.desc}</span>
                  </div>
                  {idx < steps.length - 1 && (
                    <div
                      className={`${styles.stepConnector} ${
                        isCompleted ? styles.stepConnectorCompleted : ""
                      }`}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Workspace panel */}
        <div className={styles.workspace}>
          {step === 1 && (
            <>
              <div className={styles.workspaceHeader}>
                <h2 className={styles.workspaceTitle}>Core Identity</h2>
                <p className={styles.workspaceDesc}>
                  Enter the foundation details of the brand context. This shapes the initial content
                  drafts.
                </p>
              </div>
              <div className={styles.formGrid}>
                <div className={styles.fieldGroup}>
                  <label>
                    Brand Name <span>*</span>
                  </label>
                  <input
                    className="input"
                    value={formData.name}
                    onChange={(e) => set("name", e.target.value)}
                    placeholder="Acme Corp"
                  />
                  <span className={styles.fieldHelp}>
                    Used as the brand identifier across content.
                  </span>
                </div>
                <div className={styles.fieldGroup}>
                  <label>One-Liner / Tagline</label>
                  <input
                    className="input"
                    value={formData.tagline ?? ""}
                    onChange={(e) => set("tagline", e.target.value)}
                    placeholder="Making enterprise data flow in real-time"
                  />
                  <span className={styles.fieldHelp}>A short, punchy summary of what you do.</span>
                </div>
                <div className={styles.fieldGroup}>
                  <label>Industry / Niche</label>
                  <select
                    className="select"
                    value={formData.industry ?? ""}
                    onChange={(e) => set("industry", (e.target.value as Industry) || undefined)}
                  >
                    <option value="">Select industry...</option>
                    {INDUSTRY_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </>
          )}

          {step === 2 && (
            <>
              <div className={styles.workspaceHeader}>
                <h2 className={styles.workspaceTitle}>Voice & Perspective</h2>
                <p className={styles.workspaceDesc}>
                  Determine the tone attributes and perspective guidelines.
                </p>
              </div>
              <div className={styles.formGrid}>
                <div className={styles.fieldGroup}>
                  <label>Brand Voice Attributes</label>
                  <VoiceSelector
                    selected={formData.brand_voice ?? []}
                    onChange={(voices: BrandVoice[]) => set("brand_voice", voices)}
                  />
                  <span className={styles.fieldHelp}>Choose up to 4 personality markers.</span>
                </div>
                <div className={styles.fieldGroup}>
                  <label>Writing Perspective</label>
                  <div className={styles.perspectiveGrid}>
                    {PERSPECTIVE_OPTIONS.map((opt) => (
                      <button
                        key={opt.value}
                        type="button"
                        className={`${styles.perspectiveBtn} ${
                          formData.writing_perspective === opt.value
                            ? styles.perspectiveBtnActive
                            : ""
                        }`}
                        onClick={() => set("writing_perspective", opt.value)}
                      >
                        <span className={styles.perspectiveTitle}>{opt.label}</span>
                        <span className={styles.perspectiveSub}>{opt.sub}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </>
          )}

          {step === 3 && (
            <>
              <div className={styles.workspaceHeader}>
                <h2 className={styles.workspaceTitle}>Target Audience & Domain</h2>
                <p className={styles.workspaceDesc}>
                  Configure who you are speaking to, and connect your home page.
                </p>
              </div>
              <div className={styles.formGrid}>
                <div className={styles.fieldGroup}>
                  <label>Target Audience Segments</label>
                  <TagsInput
                    tags={formData.target_audience ?? []}
                    onChange={(tags) => set("target_audience", tags)}
                    placeholder="Engineering leads, CTOs..."
                  />
                  <span className={styles.fieldHelp}>Press Enter to create segment tokens.</span>
                </div>
                <div className={styles.fieldGroup}>
                  <label>Website URL</label>
                  <input
                    className="input"
                    type="url"
                    value={formData.website_url ?? ""}
                    onChange={(e) => set("website_url", e.target.value)}
                    placeholder="https://acme.com"
                  />
                  <span className={styles.fieldHelp}>
                    Used to scrape context or reference products.
                  </span>
                </div>
              </div>
            </>
          )}

          {step === 4 && (
            <>
              <div className={styles.workspaceHeader}>
                <h2 className={styles.workspaceTitle}>Guardrails & Style Matching</h2>
                <p className={styles.workspaceDesc}>
                  Define banned topics, competitor filters, and provide style guide content.
                </p>
              </div>
              <div className={styles.formGrid}>
                <div className={styles.fieldGroup}>
                  <label>Banned Words / Topics to Avoid</label>
                  <TagsInput
                    tags={formData.avoid_topics ?? []}
                    onChange={(tags) => set("avoid_topics", tags)}
                    placeholder="Politics, cryptotech..."
                  />
                </div>
                <div className={styles.fieldGroup}>
                  <label>Competitor Brands</label>
                  <TagsInput
                    tags={formData.competitor_brands ?? []}
                    onChange={(tags) => set("competitor_brands", tags)}
                    placeholder="Segment, Fivetran..."
                  />
                </div>
                <div className={styles.fieldGroup}>
                  <label>Reference Writing Sample</label>
                  <textarea
                    className="textarea"
                    value={formData.sample_content ?? ""}
                    onChange={(e) => set("sample_content", e.target.value)}
                    placeholder="Paste a blog post or social caption that perfectly models your voice..."
                    rows={5}
                    maxLength={2000}
                  />
                  <span className={styles.fieldHelp}>
                    {(formData.sample_content ?? "").length}/2000 characters
                  </span>
                </div>
              </div>
            </>
          )}

          {/* Stepper Footer */}
          <div className={styles.footer}>
            <button
              className="btn-ghost"
              onClick={handleBack}
              disabled={step === 1}
              style={{ gap: "4px" }}
            >
              <ArrowLeft size={14} /> Back
            </button>
            {step < 4 ? (
              <button className="btn-primary" onClick={handleNext} style={{ gap: "4px" }}>
                Next <ArrowRight size={14} />
              </button>
            ) : (
              <button
                className="btn-primary"
                onClick={handleSave}
                disabled={isSaving}
                style={{ gap: "4px" }}
              >
                {isSaving ? (
                  <>
                    <Loader2 size={14} className="animate-spin" /> Connecting...
                  </>
                ) : (
                  "Create Brand Connection"
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export function OnboardingWizardWithProvider({ onClose }: OnboardingWizardProps) {
  return (
    <ToastProvider>
      <OnboardingWizard onClose={onClose} />
    </ToastProvider>
  );
}
