// How well a piece of news is sourced, as two plain facts: how many independent sources
// reported it (with their names), and whether that makes it confirmed. No derived percentages.
import { Term } from "./Term";
import { Dots } from "./viz";

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
