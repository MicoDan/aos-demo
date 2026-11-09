import { replicaApi } from "../api";
import { MY_ASSIST } from "../brand";
import { usePolling } from "../usePolling";

export function StatsPanel() {
  const { data, error, loading } = usePolling(() => replicaApi.stats(), 3000);
  const cards = [
    { label: "Total tasks", value: data?.total },
    { label: "Pending", value: data?.pending },
    { label: "In progress", value: data?.in_progress },
    { label: "Completed", value: data?.completed },
    { label: "Completed · last 7 days", value: data?.completed_last_7_days },
  ];
  return (
    <section>
      {error && <p className="alert error">{data ? "Showing stale data — " : ""}{MY_ASSIST} error: {error}</p>}
      <div className="stat-grid">
        {cards.map((c) => (
          <div key={c.label} className="stat">
            <span className="stat-label">{c.label}</span>
            <span className="stat-value">{loading && !data ? <span className="skeleton w40" /> : c.value}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
