"use client";

import { useState, useCallback, useEffect } from "react";
import styles from "./ThreePanelLayout.module.css";
import { BrandSidebar } from "@/components/brand/BrandSidebar";
import { ChatInterface } from "@/components/chat/ChatInterface";
import { ContentPanel } from "@/components/output/ContentPanel";
import { OnboardingWizardWithProvider } from "@/components/brand/OnboardingWizard";
import { GenerationSettingsModal } from "@/components/settings/GenerationSettingsModal";
import { useBrandStore } from "@/lib/brandStore";
import { useGenerationStore } from "@/lib/generationStore";
import { PanelLeft, PanelRight, Loader2, Github } from "lucide-react";

export function ThreePanelLayout() {
  const {
    brands,
    fetchBrands,
    isLoading,
    isWizardOpen,
    setIsWizardOpen,
  } = useBrandStore();
  const { isConfigModalOpen } = useGenerationStore();
  const [leftOpen, setLeftOpen] = useState(false);
  const [rightOpen, setRightOpen] = useState(false);
  const [hasFetched, setHasFetched] = useState(false);

  useEffect(() => {
    fetchBrands().then(() => setHasFetched(true));
  }, [fetchBrands]);

  const closeAll = useCallback(() => {
    setLeftOpen(false);
    setRightOpen(false);
  }, []);

  const anyOpen = leftOpen || rightOpen;

  // Show loading spinner while verifying brands
  if (isLoading && !hasFetched) {
    return (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          height: "100vh",
          background: "#faf9f6",
          gap: "12px",
          fontFamily: "var(--font-family)",
        }}
      >
        <Loader2 className="animate-spin" size={32} color="#1a8917" />
        <span style={{ fontSize: "14px", color: "#667085" }}>Loading Brand Workspaces...</span>
      </div>
    );
  }

  const showOnboarding = hasFetched && brands.length === 0;

  return (
    <div className={styles.appContainer}>
      {/* Top persistent Header bar */}
      <header className={styles.appHeader}>
        <div className={styles.headerLeft}>
          <span className={styles.logoMark}>✦</span>
          <span className={styles.logoText}>OmniWrite</span>
          <span className={styles.versionBadge}>v0.1.0-alpha</span>
          <div className={styles.statusIndicator}>
            <span className={styles.statusDotActive} />
            <span>Engine Connected</span>
          </div>
        </div>
        <div className={styles.headerRight}>
          <a
            href="https://github.com/kanishkkatara/omniwrite"
            target="_blank"
            rel="noopener noreferrer"
            className={styles.headerLink}
          >
            <Github size={14} />
            <span>GitHub</span>
          </a>
        </div>
      </header>

      <div className={styles.layout}>
        {anyOpen && (
          <div className={styles.backdrop} onClick={closeAll} />
        )}

        {/* Left Panel */}
        <div className={`${styles.leftPanel} ${leftOpen ? styles.open : ""}`}>
          <BrandSidebar />
        </div>

        {/* Center Panel */}
        <div className={styles.centerPanel}>
          <ChatInterface />
        </div>

        {/* Right Panel */}
        <div className={`${styles.rightPanel} ${rightOpen ? styles.open : ""}`}>
          <ContentPanel />
        </div>

        {/* Mobile toggle buttons */}
        <div className={styles.panelToggle} style={{ left: 16 }}>
          <button
            className="btn-ghost"
            onClick={() => { setLeftOpen((v) => !v); setRightOpen(false); }}
            aria-label="Toggle sidebar"
            style={{ padding: "8px" }}
          >
            <PanelLeft size={18} />
          </button>
        </div>
        <div className={styles.panelToggle} style={{ right: 16 }}>
          <button
            className="btn-ghost"
            onClick={() => { setRightOpen((v) => !v); setLeftOpen(false); }}
            aria-label="Toggle output panel"
            style={{ padding: "8px" }}
          >
            <PanelRight size={18} />
          </button>
        </div>
      </div>

      {/* Full-screen wizard on onboarding or manual trigger */}
      {(showOnboarding || isWizardOpen) && (
        <OnboardingWizardWithProvider onClose={() => { setIsWizardOpen(false); fetchBrands(); }} />
      )}

      {/* Spacious settings configuration modal */}
      {isConfigModalOpen && (
        <GenerationSettingsModal />
      )}
    </div>
  );
}
