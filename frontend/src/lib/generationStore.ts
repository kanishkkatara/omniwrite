import { create } from "zustand";
import {
  Platform,
  ContentLength,
  ModelMode,
  ReadingLevel,
  CtaType,
  JobStatus,
} from "@/types/generation";
import type {
  AgentStep,
  ContentOutput,
  GenerationCost,
  OutlineData,
  GenerateRequest,
} from "@/types/generation";
import * as api from "@/lib/api";

interface GenerationState {
  currentJobId: string | null;
  jobStatus: JobStatus | null;
  steps: AgentStep[];
  outputs: ContentOutput[];
  outline: OutlineData | null;
  costSummary: GenerationCost | null;
  isStreaming: boolean;
  error: string | null;
  topic: string;
  isConfigModalOpen: boolean;

  // Generation Settings (Config)
  platforms: Platform[];
  contentLength: ContentLength;
  modelMode: ModelMode;
  testModel: string;
  productionModel: string;
  seoKeywords: string[];
  readingLevel: ReadingLevel;
  ctaType: CtaType;
  subreddit: string;
  includeResearch: boolean;
  creativity: number; // 0 - 100
  variants: number;
}

interface GenerationActions {
  startJob: () => Promise<string>;
  updateStep: (step: AgentStep) => void;
  setOutline: (outline: OutlineData) => void;
  setOutput: (output: ContentOutput) => void;
  setStatus: (status: JobStatus) => void;
  setCost: (cost: GenerationCost) => void;
  setIsStreaming: (streaming: boolean) => void;
  setError: (error: string | null) => void;
  setTopic: (topic: string) => void;
  setConfigValue: <K extends keyof GenerationState>(key: K, value: GenerationState[K]) => void;
  setIsConfigModalOpen: (open: boolean) => void;
  reset: () => void;
}

type GenerationStore = GenerationState & GenerationActions;

const initialConfig = {
  platforms: [Platform.Blog, Platform.LinkedIn],
  contentLength: ContentLength.Medium,
  modelMode: ModelMode.Test,
  testModel: "gpt-4.1-nano",
  productionModel: "claude-sonnet-4-5",
  seoKeywords: [],
  readingLevel: ReadingLevel.Intermediate,
  ctaType: CtaType.None,
  subreddit: "",
  includeResearch: true,
  creativity: 50,
  variants: 1,
};

const initialState: GenerationState = {
  currentJobId: null,
  jobStatus: null,
  steps: [],
  outputs: [],
  outline: null,
  costSummary: null,
  isStreaming: false,
  error: null,
  topic: "",
  isConfigModalOpen: false,
  ...initialConfig,
};

export const useGenerationStore = create<GenerationStore>()((set, get) => ({
  ...initialState,

  startJob: async () => {
    const state = get();
    // Reset output & tracking state but keep configurations
    set({
      currentJobId: null,
      jobStatus: JobStatus.Pending,
      steps: [],
      outputs: [],
      outline: null,
      costSummary: null,
      isStreaming: true,
      error: null,
    });

    // Map settings from the store to the GenerateRequest schema
    const request: GenerateRequest = {
      topic: state.topic,
      platforms: state.platforms,
      content_length: state.contentLength,
      model_mode: state.modelMode,
      test_model: state.testModel || undefined,
      production_model: state.productionModel || undefined,
      seo_keywords: state.seoKeywords,
      reading_level: state.readingLevel,
      cta_type: state.ctaType,
      subreddit: state.subreddit || undefined,
      include_research: state.includeResearch,
      creativity: state.creativity / 100, // map 0-100% slider to 0.0-1.0 float
      variants: state.variants,
    };

    try {
      const response = await api.startGeneration(request);
      set({ currentJobId: response.job_id, jobStatus: response.status });
      return response.job_id;
    } catch (err) {
      set({
        isStreaming: false,
        error: err instanceof Error ? err.message : "Failed to start generation job",
      });
      throw err;
    }
  },

  updateStep: (step) => {
    set((state) => {
      const exists = state.steps.findIndex((s) => s.id === step.id);
      if (exists >= 0) {
        const updated = [...state.steps];
        updated[exists] = step;
        return { steps: updated };
      }
      return { steps: [...state.steps, step] };
    });
  },

  setOutline: (outline) => set({ outline }),

  setOutput: (output) => {
    set((state) => {
      const exists = state.outputs.findIndex(
        (o) => o.platform === output.platform && o.variant_index === output.variant_index
      );
      if (exists >= 0) {
        const updated = [...state.outputs];
        updated[exists] = output;
        return { outputs: updated };
      }
      return { outputs: [...state.outputs, output] };
    });
  },

  setStatus: (status) => set({ jobStatus: status }),

  setCost: (cost) => set({ costSummary: cost }),

  setIsStreaming: (isStreaming) => set({ isStreaming }),

  setError: (error) => set({ error, isStreaming: false }),

  setTopic: (topic) => set({ topic }),

  setConfigValue: (key, value) => {
    set({ [key]: value } as any);
  },

  setIsConfigModalOpen: (isConfigModalOpen) => set({ isConfigModalOpen }),

  reset: () =>
    set((state) => ({
      currentJobId: null,
      jobStatus: null,
      steps: [],
      outputs: [],
      outline: null,
      costSummary: null,
      isStreaming: false,
      error: null,
      topic: "",
    })),
}));
