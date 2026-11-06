import { FormEvent, useEffect, useState } from "react";
import { useEscape } from "../useEscape";
import { IconClose, IconPlus, IconTrash } from "./Icons";
import { Attachment, Priority, Status, Task, TaskInput, taskApi } from "../api";

interface Props {
  task: Task | null;
  onClose: () => void;
  onSave: (t: TaskInput) => Promise<void>;
}

const csv = (a: string[]) => a.join(", ");
const parseCsv = (s: string) => s.split(",").map((x) => x.trim()).filter(Boolean);
const today = () => new Date().toISOString().slice(0, 10);

export function TaskModal({ task, onClose, onSave }: Props) {
  const [title, setTitle] = useState(task?.title ?? "");
  const [project, setProject] = useState(task?.project ?? "");
  const [status, setStatus] = useState<Status>(task?.status ?? "pending");
  const [description, setDescription] = useState(task?.description ?? "");
  const [attachments, setAttachments] = useState<Attachment[]>(task?.attachments ?? []);
  const [parent, setParent] = useState(task?.parent_task ?? "");
  const [priority, setPriority] = useState<Priority>(task?.priority ?? "medium");
  const [assignees, setAssignees] = useState(csv(task?.assignees ?? []));
  const [lead, setLead] = useState(task?.lead_institution ?? "");
  const [within, setWithin] = useState(csv(task?.supporting_institutions_within_gsas ?? []));
  const [outside, setOutside] = useState(csv(task?.supporting_institutions_outside_gsas ?? []));
  const [issued, setIssued] = useState(task?.date_issued ?? today());
  const [due, setDue] = useState(task?.due_date ?? "");
  const [labels, setLabels] = useState(csv(task?.labels ?? []));
  const [candidates, setCandidates] = useState<Task[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    taskApi.list("", 100).then((p) => setCandidates(p.items.filter((t) => t.id !== task?.id))).catch(() => {});
  }, [task?.id]);

  const setAtt = (i: number, patch: Partial<Attachment>) =>
    setAttachments(attachments.map((a, j) => (j === i ? { ...a, ...patch } : a)));

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await onSave({
        title: title.trim(),
        project: project.trim() || null,
        status,
        description: description.trim() || null,
        attachments: attachments.filter((a) => a.name.trim()).map((a) => ({ ...a, name: a.name.trim(), url: a.url?.trim() || null })),
        parent_task: parent || null,
        priority,
        assignees: parseCsv(assignees),
        lead_institution: lead.trim() || null,
        supporting_institutions_within_gsas: parseCsv(within),
        supporting_institutions_outside_gsas: parseCsv(outside),
        date_issued: issued || null,
        due_date: due || null,
        labels: parseCsv(labels),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
      setSaving(false);
    }
  };

  useEscape(onClose);
  return (
    <div className="overlay" onClick={onClose}>
      <form className="modal wide" onClick={(e) => e.stopPropagation()} onSubmit={submit}>
        <header className="modal-head">
          <h2>{task ? "Edit task" : "New task"}</h2>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Close"><IconClose /></button>
        </header>
        <div className="modal-body">
          <fieldset>
            <legend>Basics</legend>
            <div className="form-grid">
              <label className="span2">Title
                <input name="title" value={title} onChange={(e) => setTitle(e.target.value)} required maxLength={200} autoFocus placeholder="What needs to be done?" />
              </label>
              <label>Project
                <input name="project" value={project} onChange={(e) => setProject(e.target.value)} maxLength={200} />
              </label>
              <label>Status
                <select name="status" value={status} onChange={(e) => setStatus(e.target.value as Status)}>
                  <option value="pending">Pending</option>
                  <option value="in_progress">In progress</option>
                  <option value="completed">Completed</option>
                </select>
              </label>
              <label className="span2">Description
                <textarea name="description" value={description} onChange={(e) => setDescription(e.target.value)} rows={3} />
              </label>
            </div>
          </fieldset>

          <fieldset>
            <legend>Planning</legend>
            <div className="form-grid">
              <label>Priority
                <select name="priority" value={priority} onChange={(e) => setPriority(e.target.value as Priority)}>
                  <option value="low">Low</option><option value="medium">Medium</option>
                  <option value="high">High</option><option value="critical">Critical</option>
                </select>
              </label>
              <label>Parent task
                <select name="parent_task" value={parent} onChange={(e) => setParent(e.target.value)}>
                  <option value="">— none —</option>
                  {parent && !candidates.some((t) => t.id === parent) && <option value={parent}>(current parent)</option>}
                  {candidates.map((t) => <option key={t.id} value={t.id}>{t.title}</option>)}
                </select>
              </label>
              <label>Date issued
                <input type="date" name="date_issued" value={issued} onChange={(e) => setIssued(e.target.value)} />
              </label>
              <label>Due date
                <input type="date" name="due_date" value={due} onChange={(e) => setDue(e.target.value)} />
              </label>
              <label className="span2">Assignees <small className="hint">comma-separated</small>
                <input name="assignees" value={assignees} onChange={(e) => setAssignees(e.target.value)} placeholder="amina, jean" />
              </label>
              <label className="span2">Labels <small className="hint">comma-separated</small>
                <input name="labels" value={labels} onChange={(e) => setLabels(e.target.value)} placeholder="urgent, finance" />
              </label>
            </div>
          </fieldset>

          <fieldset>
            <legend>Institutions</legend>
            <div className="form-grid">
              <label className="span2">Lead institution
                <input name="lead_institution" value={lead} onChange={(e) => setLead(e.target.value)} maxLength={200} />
              </label>
              <label>Supporting (within GSAS) <small className="hint">comma-separated</small>
                <input name="within" value={within} onChange={(e) => setWithin(e.target.value)} />
              </label>
              <label>Supporting (outside GSAS) <small className="hint">comma-separated</small>
                <input name="outside" value={outside} onChange={(e) => setOutside(e.target.value)} />
              </label>
            </div>
          </fieldset>

          <fieldset>
            <legend>Attachments</legend>
            <div className="attachments">
              {attachments.map((a, i) => (
                <div className="att-row" key={i}>
                  <input placeholder="Name" aria-label="Attachment name" value={a.name} onChange={(e) => setAtt(i, { name: e.target.value })} />
                  <input placeholder="Link (https://…)" aria-label="Attachment link" value={a.url ?? ""} onChange={(e) => setAtt(i, { url: e.target.value })} />
                  <button type="button" className="icon-btn danger" aria-label="Remove attachment" onClick={() => setAttachments(attachments.filter((_, j) => j !== i))}><IconTrash /></button>
                </div>
              ))}
              <button type="button" className="btn ghost sm" onClick={() => setAttachments([...attachments, { name: "", url: "" }])}><IconPlus /> Add attachment</button>
            </div>
          </fieldset>
        </div>
        <footer className="modal-foot">
          {error && <span className="error grow">{error}</span>}
          <button type="button" className="btn" onClick={onClose} disabled={saving}>Cancel</button>
          <button type="submit" className="btn primary" disabled={saving || !title.trim()}>{saving ? "Saving…" : task ? "Save changes" : "Create task"}</button>
        </footer>
      </form>
    </div>
  );
}
