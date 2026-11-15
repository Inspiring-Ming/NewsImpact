// Expected vs actual in one grid: a row per update, a column per market measure.
// Each cell shows the expected direction, what was measured, and whether it matched.
import type { S } from "../../api/client";
import { ARROW, describe, humanize, label, RESULT } from "../../shared/labels";
import { useNames } from "../../shared/names";
import type { EventData } from "./context";

const CHANNELS = ["price", "volume", "volatility"] as const;

function Cell({ d, index }: { d?: S["DecisionCheck"]; index: string }) {
  if (!d) return <td className="cell-none">not expected</td>;
  const r = RESULT[d.verdict] ?? { text: humanize(d.verdict), icon: "?", tone: "muted" as const };
  return (
    <td className={`cell ${r.tone}`}>
      <div className="cell-top"><span className="arrow" title="expected">{ARROW[d.expected] ?? "?"}</span><span className="verdict">{r.icon}</span></div>
      <div className="small">{d.evidence ? describe(d.evidence, index) : r.text}</div>
    </td>
  );
}

export function Scorecard({ assessment, company }: EventData) {
  const { title } = useNames();
  const other = assessment.stages.flatMap((s) => s.decisions.filter((d) => !d.channel).map((d) => ({ s, d })));
  return (
    <>
      <div className="table-wrap card flush">
        <table className="scorecard">
          <thead><tr><th>Update</th>{CHANNELS.map((c) => <th key={c}>{humanize(label(c))}</th>)}</tr></thead>
          <tbody>
            {assessment.stages.map((st, i) => (
              <tr key={`${st.stage}-${st.published_at}`}>
                <td><b>{i + 1}. {title(st.stage_name)}</b></td>
                {CHANNELS.map((c) => <Cell key={c} d={st.decisions.find((d) => d.channel === c)} index={company.index_name} />)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="small muted legend">↑ ↓ ↕ expected direction · ✓ as expected · ✗ opposite · – no clear move · … too early</p>
      {other.length > 0 && (
        <details className="details">
          <summary>Other expected reactions not visible in prices ({other.length})</summary>
          <ul className="rules">
            {other.map(({ s, d }) => <li key={s.stage + d.actor + d.decision}><b>{label(d.actor)}</b> {d.decision} <span className="muted">· after {title(s.stage_name)}</span></li>)}
          </ul>
        </details>
      )}
    </>
  );
}
