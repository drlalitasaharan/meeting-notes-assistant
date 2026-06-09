import type {
  AuthResponse,
  CreateMeetingResponse,
  EditableNotesSection,
  JobStatus,
  MeetingListResponse,
  MeetingNotes,
  UploadMeetingResponse,
  UserRead,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "");
const AUTH_TOKEN_KEY = "meeting-notes-assistant-token";
const AUTH_CHANGE_EVENT = "meetiq-auth-change";

if (!API_BASE_URL) {
  throw new Error("NEXT_PUBLIC_API_BASE_URL is not set");
}

function getAuthToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(AUTH_TOKEN_KEY);
}

function dispatchAuthChange(): void {
  if (typeof window === "undefined") {
    return;
  }

  window.dispatchEvent(new Event(AUTH_CHANGE_EVENT));
}

function setAuthToken(token: string): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(AUTH_TOKEN_KEY, token);
  dispatchAuthChange();
}

export function clearAuthToken(): void {
  if (typeof window === "undefined") {
    return;
  }

  const existingToken = window.localStorage.getItem(AUTH_TOKEN_KEY);
  if (existingToken === null) {
    return;
  }

  window.localStorage.removeItem(AUTH_TOKEN_KEY);
  dispatchAuthChange();
}

export function subscribeToAuthChanges(callback: () => void): () => void {
  if (typeof window === "undefined") {
    return () => {};
  }

  const handleAuthChange = () => callback();
  const handleStorage = (event: StorageEvent) => {
    if (event.key === AUTH_TOKEN_KEY) {
      callback();
    }
  };

  window.addEventListener(AUTH_CHANGE_EVENT, handleAuthChange);
  window.addEventListener("storage", handleStorage);

  return () => {
    window.removeEventListener(AUTH_CHANGE_EVENT, handleAuthChange);
    window.removeEventListener("storage", handleStorage);
  };
}

function buildHeaders(additional?: HeadersInit): Record<string, string> {
  const token = getAuthToken();
  const headers: Record<string, string> = {};

  if (additional instanceof Headers) {
    additional.forEach((value, key) => {
      headers[key] = value;
    });
  } else if (additional) {
    Object.assign(headers, additional);
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  return headers;
}

async function parseErrorResponse(response: Response): Promise<string> {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    try {
      const payload = await response.json();
      if (payload && typeof payload === "object") {
        if (typeof payload.detail === "string") {
          return payload.detail;
        }
        if (typeof payload.error === "string") {
          return payload.error;
        }
      }
    } catch {
      // ignore parse failure
    }
  }

  const text = await response.text();
  return text || `Request failed with status ${response.status}`;
}

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function handleJsonResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const message = await parseErrorResponse(response);
    throw new ApiError(response.status, message);
  }

  return response.json() as Promise<T>;
}

async function handleTextResponse(response: Response): Promise<string> {
  if (!response.ok) {
    const message = await parseErrorResponse(response);
    throw new ApiError(response.status, message);
  }

  return response.text();
}

async function fetchWithAuth<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: buildHeaders(options?.headers),
  });

  if (response.status === 401 || response.status === 403) {
    clearAuthToken();
  }

  return handleJsonResponse<T>(response);
}

async function fetchTextWithAuth(path: string, options?: RequestInit): Promise<string> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: buildHeaders(options?.headers),
  });

  if (response.status === 401 || response.status === 403) {
    clearAuthToken();
  }

  return handleTextResponse(response);
}

export async function loginUser(email: string, password: string): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/v1/auth/login`, {
    method: "POST",
    headers: buildHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ email, password }),
  });

  const payload = await handleJsonResponse<AuthResponse>(response);
  setAuthToken(payload.access_token);
  return payload;
}

export async function signupUser(
  email: string,
  password: string,
  firstName: string,
  lastName: string,
  organizationName?: string | null,
): Promise<AuthResponse> {
  const body = {
    email,
    password,
    first_name: firstName,
    last_name: lastName,
    organization_name: organizationName ?? null,
  };

  const response = await fetch(`${API_BASE_URL}/v1/auth/signup`, {
    method: "POST",
    headers: buildHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  });

  const payload = await handleJsonResponse<AuthResponse>(response);
  setAuthToken(payload.access_token);
  return payload;
}

export async function getCurrentUser(): Promise<UserRead> {
  return fetchWithAuth<UserRead>("/v1/auth/me");
}

export async function getMeetings(): Promise<MeetingListResponse> {
  return fetchWithAuth<MeetingListResponse>("/v1/meetings?limit=50");
}

export async function createMeeting(title: string): Promise<CreateMeetingResponse> {
  return fetchWithAuth<CreateMeetingResponse>("/v1/meetings", {
    method: "POST",
    headers: buildHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ title, tags: [] }),
  });
}

export async function uploadMeetingFile(
  meetingId: number,
  file: File,
): Promise<UploadMeetingResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/v1/meetings/${meetingId}/upload`, {
    method: "POST",
    headers: buildHeaders(),
    body: formData,
  });

  if (response.status === 401 || response.status === 403) {
    clearAuthToken();
  }

  return handleJsonResponse<UploadMeetingResponse>(response);
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  return fetchWithAuth<JobStatus>(`/v1/jobs/${jobId}`, {
    method: "GET",
    cache: "no-store",
  });
}

export async function getMeetingNotes(meetingId: number): Promise<MeetingNotes> {
  return fetchWithAuth<MeetingNotes>(`/v1/meetings/${meetingId}/notes/ai`, {
    method: "GET",
    cache: "no-store",
  });
}

export async function updateMeetingNotesSection(
  meetingId: number,
  section: EditableNotesSection,
  value: string | string[],
): Promise<MeetingNotes> {
  return fetchWithAuth<MeetingNotes>(
    `/v1/meetings/${meetingId}/notes/ai`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        section,
        value,
      }),
    },
  );
}

export async function getMeetingMarkdown(meetingId: number): Promise<string> {
  return fetchTextWithAuth(`/v1/meetings/${meetingId}/notes.md`, {
    method: "GET",
    cache: "no-store",
  });
}
