import { create } from "zustand";
import type {
  AgentStep,
  ContentOutput,
  GenerationCost,
  JobStatus,
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
}

interface GenerationActions {
  startJob: (request: GenerateRequest) => Promise<string>;
  updateStep: (step: AgentStep) => void;
  setOutline: (outline: OutlineData) => void;
  setOutput: (output: ContentOutput) => void;
  setStatus: (status: JobStatus) => void;
  setCost: (cost: GenerationCost) => void;
  setIsStreaming: (streaming: boolean) => void;
  setError: (error: string | null) => void;
  setTopic: (topic: string) => void;
  reset: () => void;
}

type GenerationStore = GenerationState & GenerationActions;

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
};

export const useGenerationStore = create<GenerationStore>()((set) => ({
  ...initialState,

  startJob: async (request) => {
    set({ ...initialState, isStreaming: true, topic: request.topic });
    const response = await api.startGeneration(request);
    set({ currentJobId: response.job_id, jobStatus: response.status });
    return response.job_id;
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

  reset: () => set({ ...initialState }),
}));
