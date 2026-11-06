import { useEffect } from "react";

/** Calls `fn` when Escape is pressed while the component is mounted. */
export function useEscape(fn: () => void) {
  useEffect(() => {
    const on = (e: KeyboardEvent) => e.key === "Escape" && fn();
    window.addEventListener("keydown", on);
    return () => window.removeEventListener("keydown", on);
  }, [fn]);
}
