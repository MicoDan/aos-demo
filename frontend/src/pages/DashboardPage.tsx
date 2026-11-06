import { taskApi } from "../api";
import { ActivityPanel } from "../components/ActivityPanel";
import { StatsPanel } from "../components/StatsPanel";
import { Avatars, PriorityBadge, SourceTag, StatusBadge, fmtDay } from "../components/ui";
import { username } from "../auth";
import { usePolling } from "../usePolling";

export function DashboardPage({ goTasks }: { goTasks: () => void }) {
  const { data, error, loading } = usePolling(() => taskApi.list("", 6, 0), 5000);
  return (
    <>
      <div className="page-head">
        <div><h1>Welcome back, {username()}</h1><SourceTag system="B" /></div>
      </div>
      <StatsPanel />
      <div className="two-col">
        <section className="card">
          <header className="card-head">
            <div><h2>Latest tasks</h2><SourceTag system="A" /></div>
            <button className="btn sm" onClick={goTasks}>View all</button>
          </header>
          {error && <p className="alert error">System A error: {error}</p>}
          {loading && !data && <div className="pad"><div className="skeleton row" /><div className="skeleton row" /><div className="skeleton row" /></div>}
          {data && data.items.length === 0 && <p className="empty-note">No tasks yet.</p>}
          <ul className="mini-list">
            {data?.items.map((t) => (
              <li key={t.id}>
                <div className="mini-main"><span className="t-title">{t.title}</span><small className="muted">{t.project ?? "No project"} · due {fmtDay(t.due_date)}</small></div>
                <Avatars names={t.assignees} /><PriorityBadge priority={t.priority} /><StatusBadge status={t.status} />
              </li>
            ))}
          </ul>
        </section>
        <ActivityPanel limit={8} />
      </div>
    </>
  );
}
