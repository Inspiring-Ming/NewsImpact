// Two things read from the wording of the latest update: good or bad news for the company,
// and whether it is only a rumour. Each explains itself on hover.
import type { S } from "../api/client";
import { tone } from "./labels";
import { Term } from "./Term";

export function Signals({ e }: { e: S["EventCard"] }) {
  const t = tone(e.tone);
  return (
    <span className="signals">
      <Term id="tone"><span className={`tone-chip ${t.tone}`}>{t.icon} {t.text}</span></Term>
      {e.is_rumour && <Term id="rumour"><span className="tone-chip warn">? Rumour</span></Term>}
    </span>
  );
}
