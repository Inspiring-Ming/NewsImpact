// How urgent an event is (rules in app/guidance.py), with the reason on hover.
import type { S } from "../api/client";
import { Term } from "./Term";

const LEVEL = {
  act: { text: "Act now", cls: "act" },
  check: { text: "Check", cls: "check" },
  background: { text: "Background", cls: "background" },
} as const;

export function PriorityBadge({ e }: { e: S["EventCard"] }) {
  const p = LEVEL[e.priority as keyof typeof LEVEL] ?? LEVEL.background;
  return (
    <Term tip={`${p.text}: ${e.priority_reason}. Act now = confirmed news with an unusual move or a new update in 24 hours; Check = confirmed news, or an unusual move not yet confirmed; Background = the rest.`}>
      <span className={`priority ${p.cls}`}><span className="pdot" />{p.text}</span>
    </Term>
  );
}
