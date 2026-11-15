// "Confirmed" or "Single source", with the source names on hover: the two facts a reader
// needs to judge news (how many independent sources, and which), no derived percentages.
import { Term } from "./Term";

export function SourceBadge({ confirmed, names }: { confirmed: boolean; names: string[] }) {
  return (
    <span className="source-badge">
      <Term id={confirmed ? "confirmed" : "single"}>
        <span className={`badge-verified ${confirmed ? "yes" : "no"}`}>{confirmed ? "✓ Confirmed" : "Single source"}</span>
      </Term>{" "}
      <Term tip={names.length ? `Reported by: ${names.join(", ")}` : "No source listed"}>
        <span className="small">{names.length} {names.length === 1 ? "source" : "sources"}</span>
      </Term>
    </span>
  );
}
