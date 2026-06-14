"use client";

import { useState, useCallback, useEffect } from "react";
import styles from "./ThreePanelLayout.module.css";
import { BrandSidebar } from "@/components/brand/BrandSidebar";
import { ChatInterface } from "@/components/chat/ChatInterface";
import { ContentPanel } from "@/components/output/ContentPanel";
import { OnboardingWizardWithProvider } from "@/components/brand/OnboardingWizard";
import { useBrandStore } from "@/lib/brandStore";
import { PanelLeft, PanelRight, Loader2, Sparkles } from "lucide-react";

export function ThreePanelLayout() {
  const { brands, fetchBrands, isLoading } = useBrandStore();
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
          background: "#f8f9fa",
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

      {/* Full-screen wizard on onboarding */}
      {showOnboarding && (
        <OnboardingWizardWithProvider onClose={() => fetchBrands()} />
      )}
    </div>
  );
}
