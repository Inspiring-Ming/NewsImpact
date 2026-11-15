// Expected vs actual. One section per market measure, each defined on the page. For every
// update: what investors usually do (expected direction), what we measured as a bar against
// this stock's normal range, and whether it matched, in words. The method and the exact
// versions sit at the bottom, so the result can be checked and repeated.
import type { S } from "../../api/client";
import { ARROW, humanize, moveVs, RESULT } from "../../shared/labels";
import { useNames } from "../../shared/names";
import { Meter } from "../../shared/viz";
import type { EventData } from "./context";

const EXPECT: Record<string, string> = { up: "rise", down: "fall", uncertain: "move sharply" };
const MEASURES = [
  { channel: "price", title: (i: string) => `Share price vs ${i}`,
    what: (i: string) => `Stock return minus the ${i}'s return, from the update day to the next trading day. Removing the market's move leaves the company's own reaction. Shaded band = this stock's normal range; a bar past it is an unusual move.` },
  { channel: "volume", title: () => "Trading volume",
    what: () => "Shares traded over the update day and the 2 days after, compared with this stock's normal day (1×, the line). Investors trade more when news changes their view." },
  { channel: "volatility", title: () => "Price swings",
    what: () => "How large daily price moves were over the update day and the 4 days after, compared with normal (1×, the line). Bigger swings mean investors disagree about what the news is worth." },
] as const;

function Bar({ o, scale }: { o: S["ChannelObservation"]; scale: number }) {
  if (o.channel === "price") {
    const band = o.statistic ? (1.96 * Math.abs(o.value)) / Math.abs(o.statistic) : 0;
    const x = (v: number) => 50 + (v / scale) * 50;
    return (
      <div className="xbar">
        {band > 0 && <span className="xbar-band" style={{ left: `${x(-band)}%`, width: `${x(band) - x(-band)}%` }} />}
        <span className="xbar-zero" style={{ left: "50%" }} />
        <span className={`xbar-fill ${o.significant ? (o.value < 0 ? "bad" : "good") : "neutral"}`}
              style={o.value < 0 ? { left: `${x(o.value)}%`, width: `${50 - x(o.value)}%` } : { left: "50%", width: `${x(o.value) - 50}%` }} />
      </div>
    );
  }
  return (
    <div className="xbar">
      <span className="xbar-zero" style={{ left: `${(1 / scale) * 100}%` }} />
      <span className={`xbar-fill ${o.significant ? "warn" : "neutral"}`} style={{ left: 0, width: `${Math.min(o.value / scale, 1) * 100}%` }} />
    </div>
  );
}

export function Scorecard({ assessment: a, company, card }: EventData) {
  const { title } = useNames();
  const index = company.index_name;
  const checks = a.stages.flatMap((st) => st.decisions).filter((d) => ["consistent", "inconsistent", "not_significant"].includes(d.verdict));
  const hits = checks.filter((d) => d.verdict === "consistent").length;
  return (
    <>
      <div className="card score-summary">
        <div>
          <div className="big">{checks.length ? `${hits} of ${checks.length}` : "–"}</div>
          <Meter value={checks.length ? hits / checks.length : 0} tone={hits / Math.max(checks.length, 1) >= 0.6 ? "good" : "warn"} />
        </div>
        <p>
          measured market reactions matched what investors usually do after this kind of news.
          {a.combined_reaction && <> Updates close together are also measured as one: the stock did <b>{moveVs(a.combined_reaction.value, index)}</b>.</>}
        </p>
      </div>

      {MEASURES.map((m) => {
        const rows = a.stages.map((st, i) => ({ st, i, d: st.decisions.find((d) => d.channel === m.channel) })).filter((r) => r.d);
        if (!rows.length) return null;
        const values = rows.flatMap(({ d }) => (d!.evidence ? [d!.evidence] : []));
        const scale = m.channel === "price"
          ? Math.max(0.03, ...values.map((o) => Math.max(Math.abs(o.value), o.statistic ? (1.96 * Math.abs(o.value)) / Math.abs(o.statistic) : 0))) * 1.15
          : Math.max(3, ...values.map((o) => o.value)) * 1.1;
        return (
          <section key={m.channel} className="card measure">
            <h3>{m.title(index)}</h3>
            <p className="small muted">{m.what(index)}</p>
            <div className="measure-rows">
              {rows.map(({ st, i, d }) => {
                const r = RESULT[d!.verdict] ?? { text: humanize(d!.verdict), icon: "?", tone: "muted" as const };
                const o = d!.evidence;
                return (
                  <div key={st.stage + st.published_at} className="measure-row">
                    <div className="m-update"><b>{i + 1}. {title(st.stage_name)}</b>
                      <div className="muted small">Expected to {ARROW[d!.expected]} {EXPECT[d!.expected] ?? d!.expected}</div></div>
                    <div className="m-bar">
                      {o ? <><Bar o={o} scale={scale} /><span className="small">{o.channel === "price" ? moveVs(o.value, index) : `${o.value.toFixed(1)}× normal`}</span></>
                        : <span className="muted small">{d!.verdict === "pending" ? "Measured once the next trading days close" : "No price data"}</span>}
                    </div>
                    <span className={`verdict-badge ${r.tone}`}>{r.icon} {r.text}</span>
                  </div>
                );
              })}
            </div>
          </section>
        );
      })}

      <section className="card measure">
        <h3>How this is measured</h3>
        <ul className="know-list small">
          <li>Daily closing prices ({a.provenance.components.market ?? "price provider"}) for {company.ticker} and the {index}.</li>
          <li>"Normal" for this stock is learned from the 120 trading days ending 10 days before the first update.</li>
          <li>A move counts as unusual when it happens on fewer than 1 normal day in 20.</li>
          <li>News published after the 4 pm close counts from the next trading day.</li>
          {card.notes.map((n) => <li key={n}>{n}</li>)}
        </ul>
        <details className="details">
          <summary>Exact versions, to repeat this result</summary>
          <p className="small">Assessed {new Date(a.as_of).toLocaleString()} with rules {a.model_version}. Each data file is identified by a fingerprint of its content: the same fingerprints give the same result.</p>
          <table>
            <tbody>
              {Object.entries({ ...a.provenance.components, ...a.provenance.reference_data }).map(([k, v]) => (
                <tr key={k}><td>{k}</td><td className="mono small">{v}</td></tr>
              ))}
            </tbody>
          </table>
        </details>
      </section>
    </>
  );
}
