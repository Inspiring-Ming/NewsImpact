// For analysts: the exact statistics and how this result can be reproduced.
import { describe, label } from "../../shared/labels";
import { useNames } from "../../shared/names";
import type { EventData } from "./context";

export function AnalystData({ assessment: a, company }: EventData) {
  const { title } = useNames();
  const rows = a.stages.flatMap((s) => s.decisions.filter((d) => d.evidence).map((d) => ({ s, d })));
  return (
    <div className="card">
      <p>{a.conclusion}</p>
      {a.combined_reaction && (
        <p className="small">Updates in the same week are measured together: {describe(a.combined_reaction, company.index_name)} (z = {a.combined_reaction.statistic}).</p>
      )}
      <div className="table-wrap">
        <table>
          <thead><tr><th>Update</th><th>Measure</th><th>Metric</th><th className="num">Value</th><th className="num">z</th></tr></thead>
          <tbody>
            {rows.map(({ s, d }) => (
              <tr key={s.stage + d.actor + d.decision}>
                <td>{title(s.stage_name)}</td><td>{label(d.channel ?? "")}</td>
                <td className="mono small">{d.evidence!.metric}</td>
                <td className="num">{d.evidence!.value.toFixed(3)}</td><td className="num">{d.evidence!.statistic ?? "–"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <h3>Reproduce this result</h3>
      <table>
        <tbody>
          <tr><td>Assessed</td><td className="small">{new Date(a.as_of).toLocaleString()}</td></tr>
          <tr><td>Rules version</td><td className="mono small">{a.model_version}</td></tr>
          {Object.entries({ ...a.provenance.components, ...a.provenance.reference_data }).map(([k, v]) => (
            <tr key={k}><td>{k}</td><td className="mono small">{v}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
