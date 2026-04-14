import type {
  CreateMeetingResponse,
  JobStatus,
  MeetingNotes,
  UploadMeetingResponse,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "");

if (!API_BASE_URL) {
  throw new Error("NEXT_PUBLIC_API_BASE_URL is not set");
}

async function handleJsonResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function createMeeting(title: string): Promise<CreateMeetingResponse> {
  const response = await fetch(`${API_BASE_URL}/v1/meetings`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      title,
      tags: [],
    }),
  });

  return handleJsonResponse<CreateMeetingResponse>(response);
}

export async function uploadMeetingFile(
  meetingId: number,
  file: File,
): Promise<UploadMeetingResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/v1/meetings/${meetingId}/upload`, {
    method: "POST",
    body: formData,
  });

  return handleJsonResponse<UploadMeetingResponse>(response);
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const response = await fetch(`${API_BASE_URL}/v1/jobs/${jobId}`, {
    method: "GET",
    cache: "no-store",
  });

  return handleJsonResponse<JobStatus>(response);
}

export async function getMeetingNotes(meetingId: number): Promise<MeetingNotes> {
  const response = await fetch(`${API_BASE_URL}/v1/meetings/${meetingId}/notes/ai`, {
    method: "GET",
    cache: "no-store",
  });

  return handleJsonResponse<MeetingNotes>(response);
}

export async function getMeetingMarkdown(meetingId: number): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/v1/meetings/${meetingId}/notes.md`, {
    method: "GET",
    cache: "no-store",
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }

  return response.text();
}
