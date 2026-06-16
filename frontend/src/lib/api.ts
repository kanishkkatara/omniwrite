import type { BrandProfile, BrandProfileCreate, BrandProfileUpdate } from "@/types/brand";
import type { GenerateRequest, GenerateResponse, JobState, JobEvent } from "@/types/generation";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`API error ${res.status} ${res.statusText}: ${errorText}`);
  }

  return res.json() as Promise<T>;
}

// ─── Brand APIs ───────────────────────────────────────────────────────────────

export async function createBrand(data: BrandProfileCreate): Promise<BrandProfile> {
  return apiFetch<BrandProfile>("/api/v1/brands", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getBrands(): Promise<BrandProfile[]> {
  return apiFetch<BrandProfile[]>("/api/v1/brands");
}

export async function getBrand(id: string): Promise<BrandProfile> {
  return apiFetch<BrandProfile>(`/api/v1/brands/${id}`);
}

export async function updateBrand(id: string, data: BrandProfileUpdate): Promise<BrandProfile> {
  return apiFetch<BrandProfile>(`/api/v1/brands/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function deleteBrand(id: string): Promise<void> {
  await apiFetch<void>(`/api/v1/brands/${id}`, { method: "DELETE" });
}

// ─── Generation APIs ──────────────────────────────────────────────────────────

export async function startGeneration(request: GenerateRequest): Promise<GenerateResponse> {
  return apiFetch<GenerateResponse>("/api/v1/generate", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function getJob(jobId: string): Promise<JobState> {
  return apiFetch<JobState>(`/api/v1/jobs/${jobId}`);
}

export async function approveOutline(
  jobId: string,
  approved: boolean,
  editedOutline?: string
): Promise<void> {
  await apiFetch<void>(`/api/v1/jobs/${jobId}/approve-outline`, {
    method: "POST",
    body: JSON.stringify({ approved, edited_outline: editedOutline }),
  });
}

export async function regeneratePlatform(
  jobId: string,
  platform: string,
  feedback?: string
): Promise<void> {
  await apiFetch<void>(`/api/v1/jobs/${jobId}/regenerate/${platform}`, {
    method: "POST",
    body: JSON.stringify({ feedback }),
  });
}

// ─── SSE Streaming ────────────────────────────────────────────────────────────

export function streamJobEvents(
  jobId: string,
  onEvent: (event: JobEvent) => void,
  onError?: (error: Event) => void
): () => void {
  const eventSource = new EventSource(`${BASE_URL}/api/v1/jobs/${jobId}/stream`);

  eventSource.onmessage = (e: MessageEvent) => {
    try {
      const parsed = JSON.parse(e.data as string) as JobEvent;
      onEvent(parsed);
    } catch {
      // non-JSON message, ignore
    }
  };

  // Handle named events
  const eventTypes = [
    "step_update",
    "outline_ready",
    "content_ready",
    "job_complete",
    "error",
    "progress",
  ];
  eventTypes.forEach((type) => {
    eventSource.addEventListener(type, (e: Event) => {
      // Ignore native EventSource connection error events
      if (type === "error" && !("data" in e)) {
        return;
      }
      const msgEvent = e as MessageEvent;
      try {
        const parsed = JSON.parse(msgEvent.data as string) as Record<string, unknown>;
        onEvent({ event: type, data: parsed });
      } catch {
        onEvent({ event: type, data: { raw: msgEvent.data } });
      }
    });
  });

  if (onError) {
    eventSource.onerror = onError;
  }

  return () => {
    eventSource.close();
  };
}
