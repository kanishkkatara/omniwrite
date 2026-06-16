import { create } from "zustand";
import {
  Platform,
  ContentLength,
  ModelMode,
  ReadingLevel,
  CtaType,
  JobStatus,
  AgentStepStatus,
} from "@/types/generation";
import type {
  AgentStep,
  ContentOutput,
  GenerationCost,
  OutlineData,
  GenerateRequest,
  GenerationTab,
  Message,
  JobEvent,
} from "@/types/generation";
import * as api from "@/lib/api";
import { streamJobEvents } from "@/lib/api";

interface GenerationState {
  tabs: GenerationTab[];
  activeTabId: string;
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
  addTab: (title?: string) => string;
  removeTab: (tabId: string) => void;
  setActiveTab: (tabId: string) => void;
  updateTab: (tabId: string, updates: Partial<GenerationTab>) => void;
  addMessage: (tabId: string, message: Message) => void;
  updateTabStep: (tabId: string, step: AgentStep) => void;
  setTabOutput: (tabId: string, output: ContentOutput) => void;

  startJob: () => Promise<string>;
  connectTabStream: (tabId: string, jobId: string) => void;
  disconnectTabStream: (tabId: string) => void;

  // Active Tab wrappers (for compatibility and convenience)
  updateStep: (step: AgentStep) => void;
  setOutline: (outline: OutlineData) => void;
  setOutput: (output: ContentOutput) => void;
  setStatus: (status: JobStatus) => void;
  setCost: (cost: GenerationCost) => void;
  setIsStreaming: (streaming: boolean) => void;
  setError: (error: string | null) => void;
  setTopic: (topic: string) => void;
  reset: () => void;

  setConfigValue: <K extends keyof GenerationState>(key: K, value: GenerationState[K]) => void;
  setIsConfigModalOpen: (open: boolean) => void;
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

const createNewTab = (id?: string, title: string = "New Generation"): GenerationTab => {
  const newId = id || `tab-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
  return {
    id: newId,
    title,
    currentJobId: null,
    jobStatus: null,
    steps: [],
    outputs: [],
    outline: null,
    costSummary: null,
    isStreaming: false,
    error: null,
    topic: "",
    messages: [],
  };
};

const initialTab = createNewTab(undefined, "New Generation");

const initialState: GenerationState = {
  tabs: [initialTab],
  activeTabId: initialTab.id,
  isConfigModalOpen: false,
  ...initialConfig,
};

// Private background connection maps keyed by tabId
const streamCleanups = new Map<string, () => void>();
const pollIntervals = new Map<string, NodeJS.Timeout>();

export const useGenerationStore = create<GenerationStore>()((set, get) => ({
  ...initialState,

  addTab: (title) => {
    const newTab = createNewTab(undefined, title);
    set((state) => ({
      tabs: [...state.tabs, newTab],
      activeTabId: newTab.id,
    }));
    return newTab.id;
  },

  removeTab: (tabId) => {
    const { tabs, activeTabId, disconnectTabStream } = get();
    // Clean up background tasks for this tab
    disconnectTabStream(tabId);

    const updatedTabs = tabs.filter((t) => t.id !== tabId);

    if (updatedTabs.length === 0) {
      const defaultTab = createNewTab(undefined, "New Generation");
      set({
        tabs: [defaultTab],
        activeTabId: defaultTab.id,
      });
      return;
    }

    let nextActiveId = activeTabId;
    if (activeTabId === tabId) {
      const index = tabs.findIndex((t) => t.id === tabId);
      const nextIndex = Math.max(0, index - 1);
      nextActiveId = updatedTabs[nextIndex].id;
    }

    set({
      tabs: updatedTabs,
      activeTabId: nextActiveId,
    });
  },

  setActiveTab: (activeTabId) => set({ activeTabId }),

  updateTab: (tabId, updates) => {
    set((state) => ({
      tabs: state.tabs.map((t) => (t.id === tabId ? { ...t, ...updates } : t)),
    }));
  },

  addMessage: (tabId, message) => {
    set((state) => ({
      tabs: state.tabs.map((t) =>
        t.id === tabId ? { ...t, messages: [...t.messages, message] } : t
      ),
    }));
  },

  updateTabStep: (tabId, step) => {
    set((state) => ({
      tabs: state.tabs.map((t) => {
        if (t.id !== tabId) return t;
        const exists = t.steps.findIndex((s) => s.id === step.id);
        const updatedSteps = [...t.steps];
        if (exists >= 0) {
          updatedSteps[exists] = step;
        } else {
          updatedSteps.push(step);
        }
        return { ...t, steps: updatedSteps };
      }),
    }));
  },

  setTabOutput: (tabId, output) => {
    set((state) => ({
      tabs: state.tabs.map((t) => {
        if (t.id !== tabId) return t;
        const exists = t.outputs.findIndex(
          (o) => o.platform === output.platform && o.variant_index === output.variant_index
        );
        const updatedOutputs = [...t.outputs];
        if (exists >= 0) {
          updatedOutputs[exists] = output;
        } else {
          updatedOutputs.push(output);
        }
        return { ...t, outputs: updatedOutputs };
      }),
    }));
  },

  // Active Tab wrappers
  updateStep: (step) => get().updateTabStep(get().activeTabId, step),
  setOutline: (outline) => get().updateTab(get().activeTabId, { outline }),
  setOutput: (output) => get().setTabOutput(get().activeTabId, output),
  setStatus: (status) => get().updateTab(get().activeTabId, { jobStatus: status }),
  setCost: (cost) => get().updateTab(get().activeTabId, { costSummary: cost }),
  setIsStreaming: (isStreaming) => get().updateTab(get().activeTabId, { isStreaming }),
  setError: (error) => get().updateTab(get().activeTabId, { error, isStreaming: false }),
  setTopic: (topic) => {
    const activeTabId = get().activeTabId;
    const title = topic.length > 25 ? `${topic.substring(0, 22)}...` : topic;
    get().updateTab(activeTabId, { topic, title });
  },

  reset: () => {
    const activeTabId = get().activeTabId;
    get().updateTab(activeTabId, {
      currentJobId: null,
      jobStatus: null,
      steps: [],
      outputs: [],
      outline: null,
      costSummary: null,
      isStreaming: false,
      error: null,
      topic: "",
      messages: [],
      title: "New Generation",
    });
  },

  // Global Config actions
  setConfigValue: (key, value) => {
    set({ [key]: value } as any);
  },

  setIsConfigModalOpen: (isConfigModalOpen) => set({ isConfigModalOpen }),

  disconnectTabStream: (tabId) => {
    const cleanup = streamCleanups.get(tabId);
    if (cleanup) {
      try {
        cleanup();
      } catch (e) {
        console.error("Failed to call stream cleanup for tab:", tabId, e);
      }
      streamCleanups.delete(tabId);
    }

    const interval = pollIntervals.get(tabId);
    if (interval) {
      clearInterval(interval);
      pollIntervals.delete(tabId);
    }
  },

  connectTabStream: (tabId, jobId) => {
    const state = get();
    // 1. Disconnect any existing stream/polling for this tab
    state.disconnectTabStream(tabId);

    const handleEvent = (event: JobEvent) => {
      const currentStore = get();
      switch (event.event) {
        case "step_update": {
          const step = event.data as unknown as AgentStep;
          if (step && step.id) {
            currentStore.updateTabStep(tabId, step);
          }
          break;
        }
        case "outline_ready": {
          const outlineData = event.data as unknown as OutlineData;
          if (outlineData) {
            currentStore.updateTab(tabId, {
              outline: outlineData,
              jobStatus: JobStatus.AwaitingOutlineApproval,
            });
          }
          break;
        }
        case "content_ready": {
          const output = event.data as unknown as ContentOutput;
          if (output && output.platform) {
            currentStore.setTabOutput(tabId, output);
          }
          break;
        }
        case "job_complete": {
          const cost = event.data?.cost as GenerationCost | undefined;
          currentStore.updateTab(tabId, {
            costSummary: cost || null,
            jobStatus: JobStatus.Completed,
            isStreaming: false,
          });
          currentStore.disconnectTabStream(tabId);
          break;
        }
        case "error": {
          const errMsg =
            typeof event.data?.message === "string"
              ? event.data.message
              : "An error occurred during generation";
          currentStore.updateTab(tabId, {
            error: errMsg,
            jobStatus: JobStatus.Failed,
            isStreaming: false,
          });
          currentStore.disconnectTabStream(tabId);
          break;
        }
        case "progress": {
          const stepData = event.data as unknown as Partial<AgentStep>;
          if (stepData?.id) {
            currentStore.updateTabStep(tabId, {
              id: stepData.id,
              name: stepData.name ?? stepData.id,
              status: stepData.status ?? AgentStepStatus.Running,
              message: stepData.message,
            });
          }
          break;
        }
        default:
          break;
      }
    };

    const startPolling = () => {
      if (pollIntervals.has(tabId)) return;

      const interval = setInterval(async () => {
        try {
          const job = await api.getJob(jobId);
          const currentStore = get();

          currentStore.updateTab(tabId, { jobStatus: job.status });

          if (job.steps) {
            job.steps.forEach((step: any) => {
              currentStore.updateTabStep(tabId, {
                id: step.id || step.agent,
                name: step.name || step.agent,
                status: step.status,
                message: step.message,
                cost: step.cost,
                started_at: step.started_at,
                completed_at: step.completed_at,
              });
            });
          }
          if (job.outputs) {
            Object.values(job.outputs).forEach((out: any) =>
              currentStore.setTabOutput(tabId, out as ContentOutput)
            );
          }
          if (job.outline) {
            currentStore.updateTab(tabId, { outline: job.outline });
          }
          if (job.cost) {
            currentStore.updateTab(tabId, { costSummary: job.cost });
          }

          if (job.status === JobStatus.Completed || job.status === JobStatus.Failed) {
            currentStore.updateTab(tabId, { isStreaming: false });
            currentStore.disconnectTabStream(tabId);
            if (job.status === JobStatus.Failed && job.error) {
              currentStore.updateTab(tabId, { error: job.error });
            }
          }
        } catch (err) {
          console.error("Polling error for tab:", tabId, err);
        }
      }, 2000);

      pollIntervals.set(tabId, interval);
    };

    // Try SSE first
    try {
      const cleanup = streamJobEvents(
        jobId,
        (event) => {
          handleEvent(event);
        },
        () => {
          // SSE error/close — always fall back to polling if not already active
          startPolling();
        }
      );
      streamCleanups.set(tabId, cleanup);
    } catch (err) {
      console.warn("SSE connection failed for tab, falling back to polling", tabId, err);
      startPolling();
    }
  },

  startJob: async () => {
    const state = get();
    const tabId = state.activeTabId;
    const activeTab = state.tabs.find((t) => t.id === tabId);
    if (!activeTab) {
      throw new Error("No active tab found");
    }

    // Reset output & tracking state for the active tab, but keep configurations global
    get().updateTab(tabId, {
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
      topic: activeTab.topic,
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
      get().updateTab(tabId, {
        currentJobId: response.job_id,
        jobStatus: response.status,
      });
      // Start background streaming
      get().connectTabStream(tabId, response.job_id);
      return response.job_id;
    } catch (err) {
      get().updateTab(tabId, {
        isStreaming: false,
        error: err instanceof Error ? err.message : "Failed to start generation job",
      });
      throw err;
    }
  },
}));
