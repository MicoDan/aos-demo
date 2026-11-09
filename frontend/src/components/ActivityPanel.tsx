import { Activity, replicaApi } from "../api";
import { MY_ASSIST } from "../brand";
import { usePolling } from "../usePolling";
import { SourceTag, timeAgo } from "./ui";

const LABEL: Record<string, string> = { "task.created": "Created", "task.updated": "Updated", "task.completed": "Completed", "task.deleted": "Deleted" };

function describe(a: Activity): string {
  const ch = a.details.changes ?? {};
  const keys = Object.keys(ch);
  if (a.event_type === "task.updated" && keys.length)
    return keys.map((k) => (k === "status" ? `status ${ch[k].old} → ${ch[k].new}` : k.replace(/_/g, " "))).join(", ");
  return a.details.status ? `status: ${a.details.status.replace("_", " ")}` : "";
}

export function ActivityPanel({ limit = 8, title = "Recent activity" }: { limit?: number; title?: string }) {
  const { data, error, loading } = usePolling(() => replicaApi.activity(limit), 3000, [limit]);
  return (
    <section className="card">
      <header className="card-head">
        <div><h2>{title}</h2><SourceTag system="B" /></div>
      </header>
      {loading && !data && <div className="pad"><div className="skeleton row" /><div className="skeleton row" /><div className="skeleton row" /></div>}
      {error && <p className="alert error">{data ? "Stale — " : ""}{MY_ASSIST} error: {error}</p>}
      {data && data.length === 0 && <p className="empty-note">No activity yet.</p>}
      <ul className="feed">
        {data?.map((a) => (
          <li key={a.event_id}>
            <span className={`feed-dot ${a.event_type.replace("task.", "")}`} />
            <div className="feed-body">
              <div className="feed-line"><span className={`tag ${a.event_type.replace("task.", "")}`}>{LABEL[a.event_type] ?? a.event_type}</span><span className="feed-title">{a.details.title}</span></div>
              <small className="muted">{describe(a)}</small>
            </div>
            <time className="muted" title={new Date(a.occurred_at).toLocaleString()}>{timeAgo(a.occurred_at)}</time>
          </li>
        ))}
      </ul>
    </section>
  );
}
