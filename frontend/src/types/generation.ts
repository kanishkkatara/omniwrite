export enum Platform {
  Blog = "blog",
  Reddit = "reddit",
  LinkedIn = "linkedin",
  LinkedInComment = "linkedin_comment",
}

export enum ContentLength {
  Short = "short",
  Medium = "medium",
  Long = "long",
}

export enum ModelMode {
  Test = "test",
  Production = "production",
}

export enum ReadingLevel {
  Beginner = "beginner",
  Intermediate = "intermediate",
  Expert = "expert",
}

export enum CtaType {
  Subscribe = "subscribe",
  LearnMore = "learn_more",
  ContactUs = "contact_us",
  BuyNow = "buy_now",
  GetStarted = "get_started",
  None = "none",
}

export enum AgentStepStatus {
  Pending = "pending",
  Running = "running",
  Done = "done",
  Error = "error",
  Skipped = "skipped",
}

export interface GenerateRequest {
  topic: string;
  brand_id?: string;
  platforms: Platform[];
  content_length?: ContentLength;
  model_mode?: ModelMode;
  seo_keywords?: string[];
  reading_level?: ReadingLevel;
  cta_type?: CtaType;
  subreddit?: string;
  include_research?: boolean;
  creativity?: number;
  variants?: number;
}

export interface ContentOutput {
  platform: Platform;
  content: string;
  word_count?: number;
  variant_index?: number;
}

export interface AgentStep {
  id: string;
  name: string;
  status: AgentStepStatus;
  message?: string;
  started_at?: string;
  completed_at?: string;
  cost?: number;
}

export interface GenerationCost {
  total_cost: number;
  total_duration_seconds: number;
  model_used: string;
  per_agent?: Record<string, number>;
}

export interface GenerateResponse {
  job_id: string;
  status: JobStatus;
}

export enum JobStatus {
  Pending = "pending",
  Running = "running",
  AwaitingOutlineApproval = "awaiting_outline_approval",
  WritingContent = "writing_content",
  Completed = "completed",
  Failed = "failed",
}

export interface OutlineData {
  sections: OutlineSection[];
  raw?: string;
}

export interface OutlineSection {
  title: string;
  description?: string;
  subsections?: string[];
}

export interface JobEvent {
  event: string;
  data: Record<string, unknown>;
}

export interface JobState {
  job_id: string;
  status: JobStatus;
  steps: AgentStep[];
  outputs: ContentOutput[];
  outline?: OutlineData | null;
  cost?: GenerationCost | null;
  error?: string;
}
