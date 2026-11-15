// How we measured: every number on this page, how it was computed, in plain words,
// and what was used, so anyone can check or repeat the result.
import type { S } from "../../api/client";
import { moveVs } from "../../shared/labels";
import { useNames } from "../../shared/names";
import type { EventData } from "./context";

const MEASURE: Record<string, string> = {
  price: "Stock return minus its market's return",
  volume: "Shares traded vs a normal day",
  volatility: "Size of daily price moves vs normal",
};

function result(o: S["ChannelObservation"], index: string): string {
  return o.channel === "price" ? moveVs(o.value, index) : `${o.value.toFixed(1)}× normal`;
}

export function AnalystData({ assessment: a, company }: EventData) {
  const { title } = useNames();
  const rows = a.stages.flatMap((s) => s.decisions.filter((d) => d.evidence).map((d) => ({ s, o: d.evidence! })));
  return (
    <div className="card measured">
      <h3>Measurements</h3>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Update</th><th>What we measured</th><th>Result</th><th>How unusual</th></tr></thead>
          <tbody>
            {rows.map(({ s, o }) => (
              <tr key={s.stage + o.channel}>
                <td>{title(s.stage_name)}</td>
                <td>{MEASURE[o.channel] ?? o.channel}</td>
                <td>{result(o, company.index_name)}</td>
                <td>
                  {o.statistic == null ? "–" : <>{Math.abs(o.statistic).toFixed(1)}× a typical move · <b className={o.significant ? "warn" : "muted"}>{o.significant ? "unusual" : "normal"}</b></>}
                </td>
              </tr>
            ))}
            {a.combined_reaction && (
              <tr>
                <td>Updates in the same week, together</td><td>{MEASURE.price}</td>
                <td>{result(a.combined_reaction, company.index_name)}</td>
                <td>{a.combined_reaction.statistic == null ? "–" : `${Math.abs(a.combined_reaction.statistic).toFixed(1)}× a typical move`}</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <p className="small muted">"How unusual" compares the move with this stock's typical move. Above 2× (exactly 1.96) it happens on fewer than 1 normal day in 20, so we call it unusual.</p>
      <h3>How it was computed</h3>
      <ul className="know-list">
        <li>Daily closing prices from {a.provenance.components.market ?? "our price provider"}, for {company.ticker} and the {company.index_name}.</li>
        <li>"Normal" for this stock is learned from the 120 trading days ending 10 days before the first update.</li>
        <li>Share price is measured from the update day to the next trading day; news after the 4 pm close counts from the next day.</li>
        <li>Updates within 4 trading days of each other are measured together, because their effects overlap.</li>
      </ul>
      <details className="details">
        <summary>Exact versions, for repeating this result</summary>
        <p className="small">Assessed {new Date(a.as_of).toLocaleString()} with rules {a.model_version}. Each file below is identified by a fingerprint of its content; the same fingerprints give the same result.</p>
        <table>
          <tbody>
            {Object.entries({ ...a.provenance.components, ...a.provenance.reference_data }).map(([k, v]) => (
              <tr key={k}><td>{k}</td><td className="mono small">{v}</td></tr>
            ))}
          </tbody>
        </table>
      </details>
    </div>
  );
}
