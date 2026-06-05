export type JobState = "queued" | "running" | "succeeded" | "failed" | string;

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
}
