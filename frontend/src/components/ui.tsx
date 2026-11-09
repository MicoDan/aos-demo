import { Priority, Status } from "../api";
import { MY_ASSIST, SMART_ADMIN } from "../brand";

export const STATUS_LABEL: Record<Status, string> = { pending: "Pending", in_progress: "In progress", completed: "Completed" };
export const PRIORITY_LABEL: Record<Priority, string> = { low: "Low", medium: "Medium", high: "High", critical: "Critical" };

export function StatusBadge({ status }: { status: Status }) {
  return <span className={`badge status-${status}`}><i />{STATUS_LABEL[status]}</span>;
}
export function PriorityBadge({ priority }: { priority: Priority }) {
  return <span className={`prio prio-${priority}`}><i />{PRIORITY_LABEL[priority]}</span>;
}
export function SourceTag({ system }: { system: "A" | "B" }) {
  return system === "A"
    ? <span className="source a">Live from {SMART_ADMIN} (source of truth)</span>
    : <span className="source b">From {MY_ASSIST} (replica, updated via Kafka)</span>;
}

const COLORS = ["#d6effa", "#dcf2e4", "#fdf3c4", "#e3edf4", "#cfe9dd", "#e9f5fc", "#f3ecc6"];
export function Avatar({ name }: { name: string }) {
  const c = COLORS[[...name].reduce((a, ch) => a + ch.charCodeAt(0), 0) % COLORS.length];
  return <span className="avatar" style={{ background: c }} title={name}>{name.trim().charAt(0).toUpperCase()}</span>;
}
export function Avatars({ names }: { names: string[] }) {
  if (!names.length) return <span className="muted">—</span>;
  return (
    <span className="avatars">
      {names.slice(0, 3).map((n) => <Avatar key={n} name={n} />)}
      {names.length > 3 && <span className="avatar more">+{names.length - 3}</span>}
    </span>
  );
}

/** Parse a YYYY-MM-DD string as a local date (avoids timezone off-by-one). */
export function parseDay(d: string) { const [y, m, day] = d.split("-").map(Number); return new Date(y, m - 1, day); }
export function fmtDay(d: string | null) {
  return d ? parseDay(d).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" }) : "—";
}
export function isOverdue(due: string | null, status: Status) {
  if (!due || status === "completed") return false;
  const t = new Date(); t.setHours(0, 0, 0, 0);
  return parseDay(due) < t;
}
export function timeAgo(iso: string) {
  const s = Math.max(0, (Date.now() - Date.parse(iso)) / 1000);
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}
