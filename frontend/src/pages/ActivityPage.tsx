import { ActivityPanel } from "../components/ActivityPanel";

export function ActivityPage() {
  return (
    <>
      <div className="page-head"><div><h1>Activity</h1></div></div>
      <ActivityPanel limit={50} title="Event log" />
    </>
  );
}
