"use client";

import { useEffect, useCallback } from "react";
import { useGenerationStore } from "@/lib/generationStore";
import { streamJobEvents, getJob } from "@/lib/api";
import type { JobEvent, AgentStep, ContentOutput, GenerationCost, OutlineData } from "@/types/generation";
import { JobStatus, AgentStepStatus } from "@/types/generation";

export function useJobStream(jobId: string | null) {
  const {
    updateStep,
    setOutline,
    setOutput,
    setStatus,
    setCost,
    setIsStreaming,
    setError,
  } = useGenerationStore();

  const handleEvent = useCallback(
    (event: JobEvent) => {
      switch (event.event) {
        case "step_update": {
          const step = event.data as unknown as AgentStep;
          if (step && step.id) {
            updateStep(step);
          }
          break;
        }
        case "outline_ready": {
          const outlineData = event.data as unknown as OutlineData;
          if (outlineData) {
            setOutline(outlineData);
            setStatus(JobStatus.AwaitingOutlineApproval);
          }
          break;
        }
        case "content_ready": {
          const output = event.data as unknown as ContentOutput;
          if (output && output.platform) {
            setOutput(output);
          }
          break;
        }
        case "job_complete": {
          const cost = event.data?.cost as GenerationCost | undefined;
          if (cost) setCost(cost);
          setStatus(JobStatus.Completed);
          setIsStreaming(false);
          break;
        }
        case "error": {
          const errMsg =
            typeof event.data?.message === "string"
              ? event.data.message
              : "An error occurred during generation";
          setError(errMsg);
          setStatus(JobStatus.Failed);
          break;
        }
        case "progress": {
          const stepData = event.data as unknown as Partial<AgentStep>;
          if (stepData?.id) {
            updateStep({
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
    },
    [updateStep, setOutline, setOutput, setStatus, setCost, setIsStreaming, setError]
  );

  useEffect(() => {
    if (!jobId) return;

    let cleanup: (() => void) | null = null;
    let pollInterval: ReturnType<typeof setInterval> | null = null;

    // Try SSE first
    try {
      cleanup = streamJobEvents(
        jobId,
        (event) => {
          handleEvent(event);
        },
        () => {
          // SSE error/close — always fall back to polling if not already active
          if (!pollInterval) {
            startPolling();
          }
        }
      );
    } catch {
      startPolling();
    }

    function startPolling() {
      pollInterval = setInterval(async () => {
        try {
          const job = await getJob(jobId!);
          setStatus(job.status);
          if (job.steps) job.steps.forEach(updateStep);
          if (job.outputs) {
            Object.values(job.outputs).forEach((out: any) => setOutput(out));
          }
          if (job.outline) setOutline(job.outline);
          if (job.cost) setCost(job.cost);
          if (
            job.status === JobStatus.Completed ||
            job.status === JobStatus.Failed
          ) {
            if (pollInterval) clearInterval(pollInterval);
            setIsStreaming(false);
            if (job.status === JobStatus.Failed && job.error) {
              setError(job.error);
            }
          }
        } catch (err) {
          console.error("Polling error:", err);
        }
      }, 2000);
    }

    return () => {
      if (cleanup) cleanup();
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [jobId, handleEvent, updateStep, setOutline, setOutput, setStatus, setCost, setIsStreaming, setError]);
}
