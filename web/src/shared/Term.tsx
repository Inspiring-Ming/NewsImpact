// A label with its definition on hover, focus or tap: column headers, key numbers, titles.
// Definitions live in labels.ts (TERMS) so every page explains a word the same way.
import { useRef, useState, type ReactNode } from "react";
import { TERMS } from "./labels";

export function Term({ id, tip, children }: { id?: keyof typeof TERMS; tip?: string; children?: ReactNode }) {
  const ref = useRef<HTMLSpanElement>(null);
  const [at, setAt] = useState<{ x: number; y: number } | null>(null);
  const show = () => {
    const r = ref.current?.getBoundingClientRect();
    // Fixed position, so a scrolling table cannot clip it; kept inside the screen.
    if (r) setAt({ x: Math.min(Math.max(r.left, 8), window.innerWidth - 288), y: r.bottom + 6 });
  };
  const hide = () => setAt(null);
  return (
    <span ref={ref} className="term" tabIndex={0} onMouseEnter={show} onMouseLeave={hide}
          onFocus={show} onBlur={hide} onClick={(e) => { e.stopPropagation(); at ? hide() : show(); }}>
      {children ?? (id && TERMS[id].label)}
      {at && <span role="tooltip" className="tip" style={{ left: at.x, top: at.y }}>{tip ?? (id && TERMS[id].tip)}</span>}
    </span>
  );
}
