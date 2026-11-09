import { replicaApi, taskApi } from "../api";
import { MY_ASSIST, SMART_ADMIN } from "../brand";
import { usePolling } from "../usePolling";

const fmt = (iso: string | null) => (iso ? new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }) : "—");

export function SyncIndicator() {
  // Compare Smart Admin's view with My Assist's view of the same user's tasks.
  const a = usePolling(() => taskApi.summary(), 3000);
  const b = usePolling(() => replicaApi.syncStatus(), 3000);

  if (a.error || b.error) {
    return (
      <div className="sync warn" title={a.error ?? b.error ?? ""}>
        <span className="dot" />
        <span className="sync-main">{a.error ? `${SMART_ADMIN} unreachable` : `${MY_ASSIST} unreachable (stale)`}</span>
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
      <small>{SMART_ADMIN} {a.data.total} · {MY_ASSIST} {b.data.live_tasks} · last event {fmt(b.data.last_synced_at)}</small>
    </div>
  );
}
