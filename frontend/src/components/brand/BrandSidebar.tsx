"use client";

import { useState, useEffect } from "react";
import styles from "./BrandSidebar.module.css";
import { OnboardingWizardWithProvider } from "./OnboardingWizard";
import { GenerationSettings } from "@/components/settings/GenerationSettings";
import { useBrandStore } from "@/lib/brandStore";
import { useGenerationStore } from "@/lib/generationStore";
import { ChevronDown, Sparkles, Building2, Settings2, PlusCircle, PenTool, Globe, Tag } from "lucide-react";
import { ToastProvider } from "@/components/ui/Toast";

// Hash brand name to a consistent color
function brandColor(name: string): string {
  const colors = [
    "#1a8917", "#242424", "#06b6d4", "#10b981",
    "#f59e0b", "#ef4444", "#ec4899", "#3b82f6"
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}

function brandInitials(name: string): string {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? "")
    .join("");
}

export function BrandSidebar() {
  const { brands, activeBrandId, setActiveBrand, fetchBrands, getActiveBrand } = useBrandStore();
  const { reset } = useGenerationStore();

  const [brandOpen, setBrandOpen] = useState(true);
  const [settingsOpen, setSettingsOpen] = useState(true);
  const [showWizard, setShowWizard] = useState(false);

  useEffect(() => {
    fetchBrands();
  }, [fetchBrands]);

  const activeBrand = getActiveBrand();

  const handleNewGeneration = () => {
    reset();
  };

  return (
    <ToastProvider>
      <div className={styles.sidebar}>
        {/* Header */}
        <div className={styles.header}>
          <div className={styles.logoArea}>
            <div className={styles.logoMark}>✦</div>
            <span className={styles.appName}>OmniWrite</span>
          </div>

          {/* Brand Selector */}
          <div className={styles.brandSelector}>
            <span className={styles.brandSelectorLabel}>Active Brand Profile</span>
            <select
              className={styles.brandSelect}
              value={activeBrandId ?? ""}
              onChange={(e) => setActiveBrand(e.target.value || null)}
            >
              <option value="">— No active brand —</option>
              {brands.map((b) => (
                <option key={b.id} value={b.id}>{b.name}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Scrollable sections */}
        <div className={styles.scrollContent}>
          {/* Brand Setup / Details section */}
          <div className={styles.section}>
            <button
              className={styles.sectionHeader}
              onClick={() => setBrandOpen((v) => !v)}
              aria-expanded={brandOpen}
            >
              <span className={styles.sectionHeaderLeft}>
                <span className={styles.sectionIcon}>
                  {activeBrand ? (
                    <span
                      className={styles.brandAvatar}
                      style={{ background: brandColor(activeBrand.name) }}
                    >
                      {brandInitials(activeBrand.name)}
                    </span>
                  ) : (
                    <Building2 size={14} color="var(--color-text-secondary)" />
                  )}
                </span>
                <span className={styles.sectionTitle}>
                  {activeBrand ? "Brand Connection" : "Connect Brand"}
                </span>
              </span>
              <ChevronDown
                size={14}
                className={`${styles.chevron} ${brandOpen ? styles.chevronOpen : ""}`}
              />
            </button>
            {brandOpen && (
              <div className={styles.sectionBody}>
                {activeBrand ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                    <div style={{ fontSize: "12px", color: "var(--color-text-secondary)" }}>
                      <strong>Tagline:</strong> {activeBrand.tagline || "—"}
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "12px" }}>
                      <Tag size={12} className="text-muted" />
                      <span>{activeBrand.industry || "General Industry"}</span>
                    </div>
                    {activeBrand.brand_voice && activeBrand.brand_voice.length > 0 && (
                      <div style={{ display: "flex", flexWrap: "wrap", gap: "4px", marginTop: "4px" }}>
                        {activeBrand.brand_voice.map((v) => (
                          <span key={v} className="badge badge-accent">
                            {v}
                          </span>
                        ))}
                      </div>
                    )}
                    <button
                      className="btn-ghost"
                      style={{ width: "100%", marginTop: "8px", fontSize: "12px", padding: "6px" }}
                      onClick={() => setShowWizard(true)}
                    >
                      Configure Brand Details
                    </button>
                  </div>
                ) : (
                  <div className={styles.noBrand}>
                    <p style={{ marginBottom: "12px", fontSize: "12px", lineHeight: "1.5" }}>
                      No brand profile active. Connect a brand profile to align all outputs with your voice.
                    </p>
                    <button
                      className="btn-primary"
                      style={{ width: "100%", fontSize: "12px", padding: "8px" }}
                      onClick={() => setShowWizard(true)}
                    >
                      <PlusCircle size={14} /> Connect a Brand
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Generation Settings section */}
          <div className={styles.section}>
            <button
              className={styles.sectionHeader}
              onClick={() => setSettingsOpen((v) => !v)}
              aria-expanded={settingsOpen}
            >
              <span className={styles.sectionHeaderLeft}>
                <Settings2 size={14} color="var(--color-text-secondary)" />
                <span className={styles.sectionTitle}>Generation Settings</span>
              </span>
              <ChevronDown
                size={14}
                className={`${styles.chevron} ${settingsOpen ? styles.chevronOpen : ""}`}
              />
            </button>
            {settingsOpen && (
              <div className={styles.sectionBody}>
                <GenerationSettings />
              </div>
            )}
          </div>
        </div>

        {/* Footer: New Generation */}
        <div className={styles.footer}>
          <button className={styles.newGenBtn} onClick={handleNewGeneration}>
            <Sparkles size={16} />
            New Generation
          </button>
        </div>

        {/* Onboarding Wizard Overlay */}
        {showWizard && (
          <OnboardingWizardWithProvider onClose={() => { setShowWizard(false); fetchBrands(); }} />
        )}
      </div>
    </ToastProvider>
  );
}
