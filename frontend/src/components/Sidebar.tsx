import { ReactNode } from "react";
import { logout, username } from "../auth";
import { Brand } from "./Brand";
import { IconActivity, IconDashboard, IconLogout, IconTasks } from "./Icons";

export type View = "dashboard" | "tasks" | "activity";
const NAV: { id: View; label: string; icon: ReactNode }[] = [
  { id: "dashboard", label: "Dashboard", icon: <IconDashboard /> },
  { id: "tasks", label: "Tasks", icon: <IconTasks /> },
  { id: "activity", label: "Activity", icon: <IconActivity /> },
];

export function Sidebar({ view, open, onNavigate }: { view: View; open: boolean; onNavigate: (v: View) => void }) {
  const name = username();
  return (
    <aside className={`sidebar ${open ? "open" : ""}`}>
      <Brand />
      <nav className="nav" aria-label="Main">
        <span className="nav-title">Workspace</span>
        {NAV.map((n) => (
          <a key={n.id} href={`#/${n.id}`} className={`nav-item ${view === n.id ? "active" : ""}`}
             onClick={(e) => { e.preventDefault(); onNavigate(n.id); }} aria-current={view === n.id ? "page" : undefined}>
            {n.icon}<span>{n.label}</span>
          </a>
        ))}
      </nav>
      <div className="side-foot">
        <div className="me">
          <span className="avatar lg">{name.charAt(0).toUpperCase()}</span>
          <div className="me-text"><strong>{name}</strong><small>Signed in</small></div>
        </div>
        <button className="icon-btn" onClick={() => logout()} title="Log out" aria-label="Log out"><IconLogout /></button>
      </div>
    </aside>
  );
}
