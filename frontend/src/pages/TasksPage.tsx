import { useState } from "react";
import { Status, Task, TaskInput, taskApi } from "../api";
import { MY_ASSIST, SMART_ADMIN } from "../brand";
import { IconInbox, IconPlus } from "../components/Icons";
import { TaskDrawer } from "../components/TaskDrawer";
import { TaskModal } from "../components/TaskModal";
import { Avatars, PriorityBadge, SourceTag, StatusBadge, fmtDay, isOverdue } from "../components/ui";
import { useEscape } from "../useEscape";
import { usePolling } from "../usePolling";

const PAGE = 10;
const TABS: { id: Status | ""; label: string }[] = [
  { id: "", label: "All" }, { id: "pending", label: "Pending" }, { id: "in_progress", label: "In progress" }, { id: "completed", label: "Completed" },
];

export function TasksPage() {
  const [filter, setFilter] = useState<Status | "">("");
  const [offset, setOffset] = useState(0);
  const [editing, setEditing] = useState<Task | "new" | null>(null);
  const [viewing, setViewing] = useState<Task | null>(null);
  const [deleting, setDeleting] = useState<Task | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const { data, error, loading, reload } = usePolling(() => taskApi.list(filter, PAGE, offset), 5000, [filter, offset]);
  // keep an open drawer fresh when the list refreshes
  const live = viewing ? data?.items.find((t) => t.id === viewing.id) ?? viewing : null;
  const parent = useParentTitle(live);

  const save = async (input: TaskInput) => {
    if (editing && editing !== "new") await taskApi.update(editing.id, input);
    else await taskApi.create(input);
    setEditing(null);
    setViewing(null);
    reload();
  };

  const confirmDelete = async () => {
    if (!deleting) return;
    try {
      await taskApi.remove(deleting.id);
      setDeleting(null);
      setViewing(null);
      if (data && data.items.length === 1 && offset > 0) setOffset(offset - PAGE);
      reload();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Delete failed");
      setDeleting(null);
    }
  };

  return (
    <>
      <div className="page-head">
        <div><h1>Tasks</h1><SourceTag system="A" /></div>
        <button className="btn primary" onClick={() => setEditing("new")}><IconPlus /> New task</button>
      </div>

      <section className="card">
        <div className="toolbar">
          <div className="tabs" role="tablist">
            {TABS.map((t) => (
              <button key={t.id} role="tab" aria-selected={filter === t.id} className={`tab ${filter === t.id ? "active" : ""}`}
                onClick={() => { setFilter(t.id); setOffset(0); }}>{t.label}</button>
            ))}
          </div>
          {data && <span className="muted count">{data.total} {data.total === 1 ? "task" : "tasks"}</span>}
        </div>

        {error && <p className="alert error">{SMART_ADMIN} error: {error}</p>}
        {actionError && <p className="alert error" onClick={() => setActionError(null)}>{actionError} (click to dismiss)</p>}

        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr><th>Task</th><th>Status</th><th className="hide-sm">Priority</th><th className="hide-sm">Assignees</th><th>Due</th><th className="hide-sm">Labels</th></tr>
            </thead>
            <tbody>
              {loading && !data && [0, 1, 2, 3].map((i) => <tr key={i}><td colSpan={6}><div className="skeleton row" /></td></tr>)}
              {data?.items.map((t) => (
                <tr key={t.id} className="clickable" tabIndex={0} onClick={() => setViewing(t)}
                    onKeyDown={(e) => e.key === "Enter" && setViewing(t)}>
                  <td className="cell-title">
                    <div className="t-title">{t.title}</div>
                    <div className="t-sub">
                      {t.project && <span className="project">{t.project}</span>}
                      {t.parent_task && <span className="muted">↳ subtask</span>}
                      {t.attachments.length > 0 && <span className="muted">📎 {t.attachments.length}</span>}
                    </div>
                  </td>
                  <td><StatusBadge status={t.status} /></td>
                  <td className="hide-sm"><PriorityBadge priority={t.priority} /></td>
                  <td className="hide-sm"><Avatars names={t.assignees} /></td>
                  <td className={isOverdue(t.due_date, t.status) ? "overdue" : ""}>{fmtDay(t.due_date)}</td>
                  <td className="hide-sm">
                    <span className="chips">
                      {t.labels.slice(0, 2).map((l) => <span key={l} className="chip">{l}</span>)}
                      {t.labels.length > 2 && <span className="chip">+{t.labels.length - 2}</span>}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {data && data.items.length === 0 && (
            <div className="empty">
              <IconInbox />
              <strong>{filter ? "No tasks with this status" : "No tasks yet"}</strong>
              <span className="muted">{filter ? "Try another filter." : "Create your first task, or run `make seed` to load demo data."}</span>
            </div>
          )}
        </div>

        {data && data.total > PAGE && (
          <footer className="pager">
            <span className="muted">{offset + 1}–{Math.min(offset + PAGE, data.total)} of {data.total}</span>
            <div>
              <button className="btn sm" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))}>Previous</button>
              <button className="btn sm" disabled={offset + PAGE >= data.total} onClick={() => setOffset(offset + PAGE)}>Next</button>
            </div>
          </footer>
        )}
      </section>

      {live && !editing && !deleting && (
        <TaskDrawer task={live} parentTitle={parent} onClose={() => setViewing(null)} onEdit={() => setEditing(live)} onDelete={() => setDeleting(live)} />
      )}
      {editing && <TaskModal task={editing === "new" ? null : editing} onClose={() => setEditing(null)} onSave={save} />}
      {deleting && <DeleteConfirm task={deleting} onCancel={() => setDeleting(null)} onConfirm={confirmDelete} />}
    </>
  );
}

function DeleteConfirm({ task, onCancel, onConfirm }: { task: Task; onCancel: () => void; onConfirm: () => void }) {
  useEscape(onCancel);
  return (
    <div className="overlay" onClick={onCancel}>
      <div className="modal confirm" onClick={(e) => e.stopPropagation()}>
        <h2>Delete task?</h2>
        <p>“{task.title}” will be permanently deleted from {SMART_ADMIN}, and removed from {MY_ASSIST} once the event syncs.</p>
        <div className="modal-foot plain">
          <button className="btn" onClick={onCancel}>Cancel</button>
          <button className="btn danger solid" onClick={onConfirm}>Delete</button>
        </div>
      </div>
    </div>
  );
}

/** Looks up the parent task's title (a task read from Smart Admin by id). */
function useParentTitle(task: Task | null): string | null {
  const id = task?.parent_task ?? null;
  const { data } = usePolling(async () => (id ? (await taskApi.get(id)).title : null), 60000, [id]);
  return id ? data : null;
}
