import { useEffect, useState } from "react";
import { IconMenu } from "./components/Icons";
import { Sidebar, View } from "./components/Sidebar";
import { SyncIndicator } from "./components/SyncIndicator";
import { ActivityPage } from "./pages/ActivityPage";
import { DashboardPage } from "./pages/DashboardPage";
import { TasksPage } from "./pages/TasksPage";

const TITLES: Record<View, string> = { dashboard: "Dashboard", tasks: "Tasks", activity: "Activity" };
const fromHash = (): View => {
  const h = window.location.hash.replace("#/", "");
  return h === "tasks" || h === "activity" ? h : "dashboard";
};

export default function App() {
  const [view, setView] = useState<View>(fromHash);
  const [menu, setMenu] = useState(false);

  useEffect(() => {
    const on = () => setView(fromHash());
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  useEffect(() => { document.title = `${TITLES[view]} · Task Platform`; }, [view]);

  const go = (v: View) => { window.location.hash = `#/${v}`; setView(v); setMenu(false); };

  return (
    <div className="shell">
      <Sidebar view={view} open={menu} onNavigate={go} />
      {menu && <div className="scrim" onClick={() => setMenu(false)} />}
      <div className="main">
        <header className="topbar">
          <button className="icon-btn menu-btn" onClick={() => setMenu(true)} aria-label="Open menu"><IconMenu /></button>
          <span className="crumb">{TITLES[view]}</span>
          <SyncIndicator />
        </header>
        <main className="content">
          {view === "dashboard" && <DashboardPage goTasks={() => go("tasks")} />}
          {view === "tasks" && <TasksPage />}
          {view === "activity" && <ActivityPage />}
        </main>
      </div>
    </div>
  );
}
