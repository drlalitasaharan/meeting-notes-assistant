export type JobState = "queued" | "running" | "succeeded" | "failed" | string;

export type EditableNotesSection =
  | "summary"
  | "key_points"
  | "action_items";

export interface Meeting {
  id: number;
  title?: string;
  created_at?: string;
  status?: string;
  processing_stage?: string | null;
  processing_progress_label?: string | null;
  processing_error_message?: string | null;
  confidential_mode?: boolean;
  recording_retention_policy?: string | null;
  recording_deleted_at?: string | null;
  recording_delete_status?: string;
}

export interface MeetingListResponse {
  items: Meeting[];
  total: number;
}

export interface CreateMeetingResponse {
  id: number;
  title?: string;
  created_at?: string;
  status?: string;
}

export interface UploadMeetingResponse {
  id?: string;
  job_id?: string;
  status?: string;
  artifact_url?: string | null;
  confidential_mode?: boolean;
  recording_retention_policy?: string | null;
  recording_deleted_at?: string | null;
  recording_delete_status?: string;
}

export interface JobStatus {
  id: string;
  status: JobState;
  artifact_url?: string | null;
}

export interface MeetingNotes {
  meeting_id: number;
  status: string;
  processing_stage?: string | null;
  processing_progress_label?: string | null;
  processing_error_message?: string | null;
  model_version?: string;
  summary: string;
  key_points: string[];
  action_items: string[];
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface UserRead {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  organization_name?: string | null;
}

export interface SignupRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  organization_name?: string | null;
}


export interface BillingStatus {
  plan_code: string;
  billing_status: string;
  provider?: string | null;
  current_period_end?: string | null;
  source?: string;
}

export interface UsageSummary {
  plan: string;
  is_pilot_override: boolean;
  meetings_used: number;
  meeting_upload_limit: number;
  remaining_uploads: number;
  max_duration_seconds: number;
  max_duration_minutes: number;
}

export type FeedbackUsefulness = "yes" | "somewhat" | "no";
export type FeedbackMostUseful =
  | "summary"
  | "decisions"
  | "action_items"
  | "risks"
  | "nothing_yet";
export type FeedbackWouldUseAgain = "yes" | "maybe" | "no";
export type FeedbackMeetingType =
  | "internal"
  | "client"
  | "sales"
  | "research"
  | "project"
  | "other";

export interface MeetingFeedbackRequest {
  meeting_id: number;
  usefulness: FeedbackUsefulness;
  most_useful: FeedbackMostUseful;
  improvement_text?: string | null;
  would_use_again: FeedbackWouldUseAgain;
  meeting_type: FeedbackMeetingType;
}

export interface MeetingFeedbackResponse extends MeetingFeedbackRequest {
  id: number;
  user_id: number;
  created_at: string;
  updated_at: string;
}
