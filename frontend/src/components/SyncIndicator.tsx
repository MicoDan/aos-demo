import { replicaApi, taskApi } from "../api";
import { usePolling } from "../usePolling";

const fmt = (iso: string | null) => (iso ? new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }) : "—");

export function SyncIndicator() {
  // Compare System A's view with System B's view of the same user's tasks.
  const a = usePolling(() => taskApi.summary(), 3000);
  const b = usePolling(() => replicaApi.syncStatus(), 3000);

  if (a.error || b.error) {
    return (
      <div className="sync warn" title={a.error ?? b.error ?? ""}>
        <span className="dot" />
        <span className="sync-main">{a.error ? "System A unreachable" : "System B unreachable (stale)"}</span>
        {b.data?.last_synced_at && <small>last sync {fmt(b.data.last_synced_at)}</small>}
      </div>
    );
  }
  if (!a.data || !b.data) return <div className="sync"><span className="dot" /><span className="sync-main">Checking sync…</span></div>;

  const aLatest = a.data.latest_updated_at ? Date.parse(a.data.latest_updated_at) : 0;
  const bLatest = b.data.latest_task_updated_at ? Date.parse(b.data.latest_task_updated_at) : 0;
  const inSync = a.data.total === b.data.live_tasks && bLatest >= aLatest;

  return (
    <div className={`sync ${inSync ? "ok" : "warn"}`}>
      <span className="dot" />
      <span className="sync-main">{inSync ? "In sync" : "Catching up…"}</span>
      <small>A {a.data.total} · B {b.data.live_tasks} · last event {fmt(b.data.last_synced_at)}</small>
    </div>
  );
}
