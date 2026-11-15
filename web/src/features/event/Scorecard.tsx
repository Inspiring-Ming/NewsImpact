// Expected vs actual: one row per update, one column per market measure. Each cell shows
// what investors usually do (expected direction), what we measured (with a bar), and
// whether it matched, in words.
import type { S } from "../../api/client";
import { ARROW, humanize, moveVs, RESULT } from "../../shared/labels";
import { useNames } from "../../shared/names";
import { Term } from "../../shared/Term";
import { MoveBar, RatioBar } from "../../shared/viz";
import type { EventData } from "./context";

const CHANNELS = ["price", "volume", "volatility"] as const;
const EXPECT: Record<string, string> = { up: "rise", down: "fall", uncertain: "move sharply" };

function Cell({ d, index }: { d?: S["DecisionCheck"]; index: string }) {
  if (!d) return <td className="cell-none">not expected for this update</td>;
  const r = RESULT[d.verdict] ?? { text: humanize(d.verdict), icon: "?", tone: "muted" as const };
  const o = d.evidence;
  return (
    <td className={`cell ${r.tone}`}>
      <div className="small muted">Expected: {ARROW[d.expected] ?? ""} {EXPECT[d.expected] ?? d.expected}</div>
      {o ? (
        <div className="cell-measure">
          {o.channel === "price"
            ? <><MoveBar value={o.value} unusual={o.significant} /><span className="small">{moveVs(o.value, index)}</span></>
            : <><RatioBar value={o.value} /><span className="small">{o.value.toFixed(1)}× normal</span></>}
        </div>
      ) : null}
      <div className={`verdict-badge ${r.tone}`}>{r.icon} {r.text}</div>
    </td>
  );
}

export function Scorecard({ assessment, company, card }: EventData) {
  const { title } = useNames();
  return (
    <>
      <div className="table-wrap card flush">
        <table className="scorecard">
          <thead><tr><th>Update</th>{CHANNELS.map((c) => <th key={c}><Term id={c} /></th>)}</tr></thead>
          <tbody>
            {assessment.stages.map((st, i) => (
              <tr key={`${st.stage}-${st.published_at}`}>
                <td><b>{i + 1}. {title(st.stage_name)}</b><div className="muted small">{new Date(st.published_at).toLocaleDateString(undefined, { day: "numeric", month: "short" })}</div></td>
                {CHANNELS.map((c) => <Cell key={c} d={st.decisions.find((d) => d.channel === c)} index={company.index_name} />)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {card.notes.length > 0 && (
        <div className="card notes">
          <h3>Status of these checks</h3>
          <ul className="know-list">{card.notes.map((n) => <li key={n}>{n}</li>)}</ul>
        </div>
      )}
    </>
  );
}
