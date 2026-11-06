import { ReactNode } from "react";

const base = { width: 18, height: 18, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round", strokeLinejoin: "round" } as const;
const mk = (d: ReactNode) => () => <svg {...base} aria-hidden="true">{d}</svg>;

export const IconDashboard = mk(<><rect x="3" y="3" width="7" height="9" rx="1.5" /><rect x="14" y="3" width="7" height="5" rx="1.5" /><rect x="14" y="12" width="7" height="9" rx="1.5" /><rect x="3" y="16" width="7" height="5" rx="1.5" /></>);
export const IconTasks = mk(<><path d="M9 11l3 3 8-8" /><path d="M20 12v6a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h9" /></>);
export const IconActivity = mk(<path d="M3 12h4l3-8 4 16 3-8h4" />);
export const IconPlus = mk(<><path d="M12 5v14" /><path d="M5 12h14" /></>);
export const IconLogout = mk(<><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><path d="M16 17l5-5-5-5" /><path d="M21 12H9" /></>);
export const IconMenu = mk(<><path d="M4 6h16" /><path d="M4 12h16" /><path d="M4 18h16" /></>);
export const IconClose = mk(<><path d="M18 6L6 18" /><path d="M6 6l12 12" /></>);
export const IconEdit = mk(<><path d="M12 20h9" /><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z" /></>);
export const IconTrash = mk(<><path d="M3 6h18" /><path d="M8 6V4h8v2" /><path d="M19 6l-1 14H6L5 6" /></>);
export const IconClip = mk(<path d="M21 11l-9 9a5 5 0 0 1-7-7l9-9a3.5 3.5 0 0 1 5 5l-9 9a2 2 0 0 1-3-3l8-8" />);
export const IconInbox = () => <svg {...base} width={32} height={32} aria-hidden="true"><path d="M22 12h-6l-2 3h-4l-2-3H2" /><path d="M5.5 5h13l3.5 7v6a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-6Z" /></svg>;
export const IconLayers = mk(<><path d="M12 2l10 5-10 5L2 7Z" /><path d="M2 17l10 5 10-5" /><path d="M2 12l10 5 10-5" /></>);
