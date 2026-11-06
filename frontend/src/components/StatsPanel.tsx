import { replicaApi } from "../api";
import { usePolling } from "../usePolling";

export function StatsPanel() {
  const { data, error, loading } = usePolling(() => replicaApi.stats(), 3000);
  const cards = [
    { label: "Total tasks", value: data?.total, tone: "slate" },
    { label: "Pending", value: data?.pending, tone: "amber" },
    { label: "In progress", value: data?.in_progress, tone: "blue" },
    { label: "Completed", value: data?.completed, tone: "green" },
    { label: "Completed · last 7 days", value: data?.completed_last_7_days, tone: "green" },
  ];
  const total = data?.total ?? 0;
  const pct = (n: number) => (total ? (n / total) * 100 : 0);
  return (
    <section>
      {error && <p className="alert error">{data ? "Showing stale data — " : ""}System B error: {error}</p>}
      <div className="stat-grid">
        {cards.map((c) => (
          <div key={c.label} className={`stat ${c.tone}`}>
            <span className="stat-label">{c.label}</span>
            <span className="stat-value">{loading && !data ? <span className="skeleton w40" /> : c.value}</span>
          </div>
        ))}
      </div>
      {data && total > 0 && (
        <div className="distribution" aria-label="Status distribution">
          <div className="bar">
            <span className="seg amber" style={{ width: `${pct(data.pending)}%` }} />
            <span className="seg blue" style={{ width: `${pct(data.in_progress)}%` }} />
            <span className="seg green" style={{ width: `${pct(data.completed)}%` }} />
          </div>
          <div className="legend">
            <span><i className="amber" />Pending</span><span><i className="blue" />In progress</span><span><i className="green" />Completed</span>
          </div>
        </div>
      )}
    </section>
  );
}
