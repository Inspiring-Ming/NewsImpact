// Tab 3 - the expected reaction for each update and how the market reaction is measured,
// in one place: every expectation sits beside its track record.
import { useState } from "react";
import type { S } from "../../api/client";
import { ARROW, humanize, label } from "../../shared/labels";
import { StepBlock } from "./StepBlock";

type Rec = Record<string, unknown>;
const CHANNELS = ["price", "volume", "volatility"] as const;

export function VerifyStep({ method, calibration }: { method: S["Method"]; calibration: S["Calibration"] | null }) {
  const market = ((method.methodology as Rec).market ?? {}) as Rec;
  const validation = ((method.methodology as Rec).validation ?? {}) as Rec;
  const windows = (market.windows ?? {}) as Record<string, [number, number]>;
  const est = Number(market.estimation_days ?? 120);
  const [theme, setTheme] = useState(method.playbooks[0]?.theme ?? "");
  const shown = method.playbooks.filter((p) => p.theme === theme);
  const record = new Map((calibration?.reactions ?? []).map((r) => [`${r.theme}|${r.stage_name}|${r.channel}`, r]));
  return (
    <StepBlock title="What reaction we expect, and how we check it"
      term="event study: abnormal return against a market index (MacKinlay 1997)"
      rules={[
        "Each update type has expected reactions from research on investor behaviour, e.g. a leader stepping down: share price ↓, trading volume ↑.",
        <>Each stock is compared with its own index: <b>S&amp;P 500</b> for US, <b>ASX 200</b> for Australia.</>,
        <>Normal behaviour is learned from the previous <b>{est} trading days</b> (about six months).</>,
        <>Measured from the update day to <b>{(windows.price ?? [0, 1])[1]} trading day(s) after</b> for share price, up to {(windows.volatility ?? [0, 4])[1]} for price swings. News after the 4 pm close counts from the next day.</>,
        "A move is unusual only if it happens on fewer than 1 normal trading day in 20.",
        <>Evidence is <b>strong</b> when the update is confirmed and at least {Math.round(Number(validation.high_support ?? 0.6) * 100)}% of expected reactions happened.</>,
      ]}>
      <select value={theme} onChange={(e) => setTheme(e.target.value)} aria-label="Event type">
        {method.playbooks.map((p) => <option key={p.theme} value={p.theme}>{p.title || label(p.theme)}</option>)}
      </select>
      <div className="table-wrap">
        <table className="scorecard">
          <thead><tr><th>Update</th>{CHANNELS.map((c) => <th key={c}>{humanize(label(c))}</th>)}</tr></thead>
          <tbody>
            {shown.flatMap((p) => p.stages.map((s) => (
              <tr key={p.theme + s.name}>
                <td><b>{s.title || label(s.name)}</b></td>
                {CHANNELS.map((c) => {
                  const d = s.decisions.find((x) => x.market_channel === c);
                  const r = record.get(`${p.theme}|${s.name}|${c}`);
                  return (
                    <td key={c} className="cell">
                      {d ? <><span className="arrow">{ARROW[d.expected_direction] ?? "?"}</span>
                        <div className="muted small">{r && r.n_events ? `${Math.round((r.share_consistent ?? 0) * r.n_events)} of ${r.n_events} as expected` : "not tested yet"}</div></>
                        : <span className="muted small">–</span>}
                    </td>
                  );
                })}
              </tr>
            )))}
          </tbody>
        </table>
      </div>
      <p className="small muted">↑ rise · ↓ fall · ↕ large move either way. With 20+ events per update type, expectations become measured facts.</p>
    </StepBlock>
  );
}
