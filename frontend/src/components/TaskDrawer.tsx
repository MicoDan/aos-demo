import { ReactNode } from "react";
import { Task } from "../api";
import { useEscape } from "../useEscape";
import { IconClip, IconClose, IconEdit, IconTrash } from "./Icons";
import { Avatars, PriorityBadge, StatusBadge, fmtDay, isOverdue } from "./ui";

function Row({ label, children }: { label: string; children: ReactNode }) {
  return <div className="d-row"><dt>{label}</dt><dd>{children}</dd></div>;
}
const list = (a: string[]) => (a.length ? a.join(", ") : <span className="muted">—</span>);

export function TaskDrawer({ task, parentTitle, onClose, onEdit, onDelete }: {
  task: Task; parentTitle: string | null; onClose: () => void; onEdit: () => void; onDelete: () => void;
}) {
  useEscape(onClose);
  return (
    <div className="overlay drawer-overlay" onClick={onClose}>
      <aside className="drawer" onClick={(e) => e.stopPropagation()} aria-label="Task details">
        <header className="drawer-head">
          <div>
            {task.project && <span className="project">{task.project}</span>}
            <h2>{task.title}</h2>
          </div>
          <button className="icon-btn" onClick={onClose} aria-label="Close"><IconClose /></button>
        </header>
        <div className="drawer-body">
          <div className="d-badges"><StatusBadge status={task.status} /><PriorityBadge priority={task.priority} /></div>
          {task.description && <p className="d-desc">{task.description}</p>}
          <dl>
            <Row label="Project">{task.project ?? <span className="muted">—</span>}</Row>
            <Row label="Parent task">{task.parent_task ? parentTitle ?? "Parent task" : <span className="muted">—</span>}</Row>
            <Row label="Assignees">{task.assignees.length ? <span className="d-people"><Avatars names={task.assignees} /> {task.assignees.join(", ")}</span> : <span className="muted">—</span>}</Row>
            <Row label="Date issued">{fmtDay(task.date_issued)}</Row>
            <Row label="Due date"><span className={isOverdue(task.due_date, task.status) ? "overdue" : ""}>{fmtDay(task.due_date)}</span></Row>
            <Row label="Lead institution">{task.lead_institution ?? <span className="muted">—</span>}</Row>
            <Row label="Supporting (within GSAS)">{list(task.supporting_institutions_within_gsas)}</Row>
            <Row label="Supporting (outside GSAS)">{list(task.supporting_institutions_outside_gsas)}</Row>
            <Row label="Labels">{task.labels.length ? <span className="chips">{task.labels.map((l) => <span key={l} className="chip">{l}</span>)}</span> : <span className="muted">—</span>}</Row>
            <Row label="Attachments">
              {task.attachments.length ? (
                <ul className="att-list">
                  {task.attachments.map((a, i) => (
                    <li key={i}><IconClip />{a.url ? <a href={a.url} target="_blank" rel="noreferrer noopener">{a.name}</a> : a.name}</li>
                  ))}
                </ul>
              ) : <span className="muted">—</span>}
            </Row>
            <Row label="Version"><span className="muted">v{task.version} · updated {new Date(task.updated_at).toLocaleString()}</span></Row>
          </dl>
        </div>
        <footer className="drawer-foot">
          <button className="btn danger" onClick={onDelete}><IconTrash /> Delete</button>
          <button className="btn primary" onClick={onEdit}><IconEdit /> Edit task</button>
        </footer>
      </aside>
    </div>
  );
}
