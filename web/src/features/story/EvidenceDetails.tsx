// For analysts: the statistics and exactly how this result was produced.
import { describe, humanize, label } from "../../shared/labels";
import type { StoryData } from "./context";

export function EvidenceDetails({ assessment: a }: StoryData) {
  const rows = a.stages.flatMap((s) => s.decisions.filter((d) => d.evidence).map((d) => ({ s, d })));
  return (
    <details className="details">
      <summary>Statistics and provenance (for analysts)</summary>
      <p className="small">{a.conclusion}</p>
      {a.combined_reaction && (
        <p className="small">Combined reaction for stages in the same week: {a.combined_reaction.metric} = {describe(a.combined_reaction)}, z = {a.combined_reaction.statistic}</p>
      )}
      <table>
        <thead><tr><th>Stage</th><th>Who</th><th>Measure</th><th>Value</th><th>z</th></tr></thead>
        <tbody>
          {rows.map(({ s, d }) => (
            <tr key={s.stage_name + d.actor + d.decision}>
              <td>{label(s.stage_name)}</td><td>{humanize(d.actor)}</td>
              <td className="mono">{d.evidence!.metric}</td><td>{d.evidence!.value.toFixed(3)}</td><td>{d.evidence!.statistic ?? "–"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="small muted">Assessed {new Date(a.as_of).toLocaleString()} · {a.model_version}</p>
      <table>
        <tbody>
          {Object.entries({ ...a.provenance.components, ...a.provenance.reference_data }).map(([k, v]) => (
            <tr key={k}><td>{k}</td><td className="mono small">{v}</td></tr>
          ))}
        </tbody>
      </table>
    </details>
  );
}
