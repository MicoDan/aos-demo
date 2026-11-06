import { freshToken, keycloak } from "./auth";
import { config } from "./config";

export type Status = "pending" | "in_progress" | "completed";
export type Priority = "low" | "medium" | "high" | "critical";
export interface Attachment {
  name: string;
  url: string | null;
  content_type?: string | null;
  size?: number | null;
}
/** Fields the user edits. Every one is stored directly on the task. */
export interface TaskInput {
  title: string;
  project: string | null;
  status: Status;
  description: string | null;
  attachments: Attachment[];
  parent_task: string | null;
  priority: Priority;
  assignees: string[];
  lead_institution: string | null;
  supporting_institutions_within_gsas: string[];
  supporting_institutions_outside_gsas: string[];
  date_issued: string | null;
  due_date: string | null;
  labels: string[];
}
export interface Task extends Omit<TaskInput, "date_issued"> {
  id: string;
  date_issued: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  version: number;
}
export interface TaskPage {
  items: Task[];
  total: number;
  limit: number;
  offset: number;
  latest_updated_at: string | null;
}
export interface Stats {
  total: number;
  pending: number;
  in_progress: number;
  completed: number;
  completed_last_7_days: number;
}
export interface Activity {
  event_id: string;
  task_id: string;
  event_type: string;
  details: { title?: string; status?: string; version?: number; changes?: Record<string, { old: unknown; new: unknown }> };
  occurred_at: string;
  processed_at: string;
}
export interface SyncStatus {
  live_tasks: number;
  last_event_id: string | null;
  last_synced_at: string | null;
  seconds_since_sync: number | null;
  latest_task_updated_at: string | null;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(base: string, path: string, init: RequestInit = {}, retried = false): Promise<T> {
  const token = await freshToken();
  const res = await fetch(base + path, {
    ...init,
    headers: {
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      Authorization: `Bearer ${token}`,
    },
  });
  if (res.status === 401) {
    if (!retried) {
      try {
        await keycloak.updateToken(-1); // force refresh once
        return request<T>(base, path, init, true);
      } catch {
        /* fall through to re-login */
      }
    }
    await keycloak.login();
    throw new ApiError(401, "Session expired");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail);
  }
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
}

// System A (source of truth)
const A = config.taskApi;
export const taskApi = {
  list: (status: Status | "", limit = 50, offset = 0) =>
    request<TaskPage>(A, `/tasks?limit=${limit}&offset=${offset}${status ? `&status=${status}` : ""}`),
  get: (id: string) => request<Task>(A, `/tasks/${id}`),
  summary: () => request<TaskPage>(A, "/tasks?limit=1"),
  create: (t: TaskInput) => request<Task>(A, "/tasks", { method: "POST", body: JSON.stringify(t) }),
  update: (id: string, t: TaskInput) => request<Task>(A, `/tasks/${id}`, { method: "PUT", body: JSON.stringify(t) }),
  remove: (id: string) => request<void>(A, `/tasks/${id}`, { method: "DELETE" }),
};

// System B (replica, fed by Kafka)
const B = config.replicaApi;
export const replicaApi = {
  stats: () => request<Stats>(B, "/stats"),
  activity: (limit = 20) => request<Activity[]>(B, `/activity?limit=${limit}`),
  syncStatus: () => request<SyncStatus>(B, "/sync-status"),
};
