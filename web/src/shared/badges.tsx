// Small labels that explain themselves on hover: how urgent an event is, how it reads
// (good or bad news, rumour), and how well it is sourced (count, names, confirmed).
import type { S } from "../api/client";
import { tone } from "./labels";
import { Term } from "./Term";
import { Dots } from "./viz";

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

export function Signals({ e }: { e: S["EventCard"] }) {
  const t = tone(e.tone);
  return (
    <span className="signals">
      <Term id="tone"><span className={`tone-chip ${t.tone}`}>{t.icon} {t.text}</span></Term>
      {e.is_rumour && <Term id="rumour"><span className="tone-chip warn">? Rumour</span></Term>}
    </span>
  );
}

export function SourceBadge({ confirmed, names }: { confirmed: boolean; names: string[] }) {
  const shown = names.slice(0, 2).join(", ") + (names.length > 2 ? ` +${names.length - 2} more` : "");
  return (
    <div className="source-badge">
      <div className="src-top">
        <Dots n={names.length} />
        <Term tip={names.length ? `Reported by: ${names.join(", ")}` : "No source listed"}>
          <b>{names.length} {names.length === 1 ? "source" : "sources"}</b>
        </Term>
      </div>
      <div className="small muted src-names">{shown}</div>
      <Confirmation confirmed={confirmed} />
    </div>
  );
}

/** "✓ Confirmed" or "○ Not yet confirmed", explained on hover. */
export function Confirmation({ confirmed }: { confirmed: boolean }) {
  return (
    <Term id={confirmed ? "confirmed" : "single"}>
      <span className={`status-word ${confirmed ? "good" : "warn"}`}>{confirmed ? "✓ Confirmed" : "○ Not yet confirmed"}</span>
    </Term>
  );
}
