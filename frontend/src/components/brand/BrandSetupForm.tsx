"use client";

import { useState, useEffect } from "react";
import styles from "./BrandSetupForm.module.css";
import { useBrandStore } from "@/lib/brandStore";
import { VoiceSelector } from "./VoiceSelector";
import { TagsInput } from "@/components/ui/TagsInput";
import { useToast } from "@/components/ui/Toast";
import {
  BrandVoice,
  WritingPerspective,
  Industry,
  type BrandProfileCreate,
} from "@/types/brand";
import { CheckCircle, Loader2 } from "lucide-react";

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

interface BrandSetupFormProps {
  onSaved?: () => void;
}

export function BrandSetupForm({ onSaved }: BrandSetupFormProps) {
  const { createBrand, updateBrand, getActiveBrand, isLoading } = useBrandStore();
  const toast = useToast();

  const activeBrand = getActiveBrand();

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

  const [saved, setSaved] = useState(false);
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
  }, [activeBrand?.id]);

  const set = <K extends keyof BrandProfileCreate>(key: K, value: BrandProfileCreate[K]) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
    setSaved(false);
  };

  const handleSave = async () => {
    if (!formData.name.trim()) {
      toast.error("Brand name is required");
      return;
    }
    setIsSaving(true);
    try {
      if (activeBrand) {
        await updateBrand(activeBrand.id, formData);
        toast.success("Brand updated successfully");
      } else {
        await createBrand(formData);
        toast.success("Brand created successfully");
      }
      setSaved(true);
      onSaved?.();
    } catch {
      toast.error("Failed to save brand. Is the backend running?");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <form
      className={styles.form}
      onSubmit={(e) => { e.preventDefault(); handleSave(); }}
    >
      {/* Name + Tagline */}
      <div className={styles.fieldGroup}>
        <label className={`${styles.label} ${styles.labelRequired}`}>Brand Name</label>
        <input
          className="input"
          value={formData.name}
          onChange={(e) => set("name", e.target.value)}
          placeholder="Acme Inc."
          required
        />
      </div>

      <div className={styles.fieldGroup}>
        <label className={styles.label}>Tagline</label>
        <input
          className="input"
          value={formData.tagline ?? ""}
          onChange={(e) => set("tagline", e.target.value)}
          placeholder="Making work easier for everyone"
        />
      </div>

      {/* Industry */}
      <div className={styles.fieldGroup}>
        <label className={styles.label}>Industry</label>
        <select
          className="select"
          value={formData.industry ?? ""}
          onChange={(e) => set("industry", (e.target.value as Industry) || undefined)}
        >
          <option value="">Select industry…</option>
          {INDUSTRY_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>

      {/* Target Audience */}
      <div className={styles.fieldGroup}>
        <label className={styles.label}>Target Audience</label>
        <TagsInput
          tags={formData.target_audience ?? []}
          onChange={(tags) => set("target_audience", tags)}
          placeholder="Startup founders, developers…"
        />
      </div>

      {/* Brand Voice */}
      <div className={styles.fieldGroup}>
        <label className={styles.label}>Brand Voice</label>
        <VoiceSelector
          selected={formData.brand_voice ?? []}
          onChange={(voices: BrandVoice[]) => set("brand_voice", voices)}
        />
      </div>

      {/* Writing Perspective */}
      <div className={styles.fieldGroup}>
        <label className={styles.label}>Writing Perspective</label>
        <div className={styles.perspectiveGrid}>
          {PERSPECTIVE_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              className={`${styles.perspectiveBtn} ${formData.writing_perspective === opt.value ? styles.perspectiveBtnActive : ""}`}
              onClick={() => set("writing_perspective", opt.value)}
            >
              <div>{opt.label}</div>
              <div style={{ opacity: 0.6, fontSize: "10px", marginTop: "2px" }}>{opt.sub}</div>
            </button>
          ))}
        </div>
      </div>

      <div className={styles.divider} />
      <div className={styles.sectionTitle}>Content Guidelines</div>

      {/* Competitor Brands */}
      <div className={styles.fieldGroup}>
        <label className={styles.label}>Competitor Brands</label>
        <TagsInput
          tags={formData.competitor_brands ?? []}
          onChange={(tags) => set("competitor_brands", tags)}
          placeholder="HubSpot, Mailchimp…"
        />
      </div>

      {/* Avoid Topics */}
      <div className={styles.fieldGroup}>
        <label className={styles.label}>Topics to Avoid</label>
        <TagsInput
          tags={formData.avoid_topics ?? []}
          onChange={(tags) => set("avoid_topics", tags)}
          placeholder="Politics, religion…"
        />
      </div>

      {/* Sample Content */}
      <div className={styles.fieldGroup}>
        <label className={styles.label}>Sample Content</label>
        <textarea
          className="textarea"
          value={formData.sample_content ?? ""}
          onChange={(e) => set("sample_content", e.target.value)}
          placeholder="Paste a sample piece of content that represents your brand voice…"
          rows={4}
          maxLength={2000}
        />
        <div className={styles.charCount}>
          {(formData.sample_content ?? "").length}/2000
        </div>
      </div>

      {/* Website URL */}
      <div className={styles.fieldGroup}>
        <label className={styles.label}>Website URL</label>
        <input
          className="input"
          type="url"
          value={formData.website_url ?? ""}
          onChange={(e) => set("website_url", e.target.value)}
          placeholder="https://acme.com"
        />
      </div>

      {/* Custom Instructions */}
      <div className={styles.fieldGroup}>
        <label className={styles.label}>Custom Instructions</label>
        <textarea
          className="textarea"
          value={formData.custom_instructions ?? ""}
          onChange={(e) => set("custom_instructions", e.target.value)}
          placeholder="Any specific instructions for content generation…"
          rows={3}
        />
      </div>

      {/* Save */}
      <div className={styles.saveRow}>
        <button
          type="submit"
          className="btn-primary"
          disabled={isSaving || isLoading}
          style={{ flex: 1 }}
        >
          {isSaving ? (
            <>
              <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} />
              Saving…
            </>
          ) : activeBrand ? "Update Brand" : "Save Brand"}
        </button>
        {saved && (
          <div className={styles.savedMsg}>
            <CheckCircle size={14} />
            Saved
          </div>
        )}
      </div>
    </form>
  );
}
