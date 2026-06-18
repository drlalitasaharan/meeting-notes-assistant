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
}

export interface JobStatus {
  id: string;
  status: JobState;
  artifact_url?: string | null;
}

export interface MeetingNotes {
  meeting_id: number;
  status: string;
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
