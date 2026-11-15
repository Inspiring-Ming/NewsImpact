// For analysts: the statistics and exactly how this result was produced.
import { describe, humanize } from "../../shared/labels";
import { useNames } from "../../shared/names";
import type { StoryData } from "./context";

export function EvidenceDetails({ assessment: a, company }: StoryData) {
  const { title } = useNames();
  const rows = a.stages.flatMap((s) => s.decisions.filter((d) => d.evidence).map((d) => ({ s, d })));
  return (
    <details className="details">
      <summary>Show statistics and sources</summary>
      <p className="small">{a.conclusion}</p>
      {a.combined_reaction && (
        <p className="small">Combined reaction for events in the same week: {a.combined_reaction.metric} = {describe(a.combined_reaction, company.benchmark_name)}, z = {a.combined_reaction.statistic}</p>
      )}
      <table>
        <thead><tr><th>Stage</th><th>Who</th><th>Measure</th><th>Value</th><th>z</th></tr></thead>
        <tbody>
          {rows.map(({ s, d }) => (
            <tr key={s.stage_name + d.actor + d.decision}>
              <td>{title(s.stage_name)}</td><td>{humanize(d.actor)}</td>
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
