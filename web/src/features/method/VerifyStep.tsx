// Market reaction check: how we measure it, and what has been measured so far.
import type { S } from "../../api/client";
import { DIRECTION, label } from "../../shared/labels";
import { StepBlock } from "./StepBlock";

type Rec = Record<string, unknown>;

export function VerifyStep({ method, calibration }: { method: S["Method"]; calibration: S["Calibration"] | null }) {
  const market = ((method.methodology as Rec).market ?? {}) as Rec;
  const validation = ((method.methodology as Rec).validation ?? {}) as Rec;
  const windows = (market.windows ?? {}) as Record<string, [number, number]>;
  const est = Number(market.estimation_days ?? 120);
  const titles = new Map(method.playbooks.flatMap((p) => p.stages.map((s) => [s.name, s.title || s.name] as const)));
  const measured = (calibration?.reactions ?? []).filter((r) => r.n_events > 0);
  return (
    <StepBlock title="How we check whether the market really reacted"
      term="event study: abnormal (excess) return against a market index, the standard research method (MacKinlay 1997)"
      what="We compare the company's share price with its whole market around each event. If the stock moves much more than the market, the news - not the market as a whole - is the likely cause."
      rules={[
        <>Each stock is compared with its own market index: the <b>S&amp;P 500</b> for US companies, the <b>ASX 200</b> for Australian ones.</>,
        <>We first learn how the stock normally moves with its index, from the previous <b>{est} trading days</b> (about six months).</>,
        <>The reaction is measured from the event day to <b>{(windows.price ?? [0, 1])[1]} trading day(s) after</b> (share price), and up to {(windows.volatility ?? [0, 4])[1]} days for price swings. News published after the 4 pm close counts from the next trading day.</>,
        <>A move counts as a <b>clear reaction</b> only if it is so large that it happens on fewer than 1 normal trading day in 20.</>,
        <>Evidence is <b>strong</b> only when the news is confirmed and the market confirmed at least {Math.round(Number(validation.high_support ?? 0.6) * 100)}% of the expected reactions.</>,
      ]}>
      {measured.length ? (
        <div className="table-wrap">
          <table>
            <thead><tr><th>After this event</th><th>We expected</th><th>Stories measured</th><th>It happened in</th></tr></thead>
            <tbody>
              {measured.map((r) => (
                <tr key={r.theme + r.stage_name + r.channel}>
                  <td>{titles.get(r.stage_name) ?? r.stage_name}</td>
                  <td>{label(r.channel)} to {DIRECTION[r.expected] ?? r.expected}</td>
                  <td>{r.n_events}</td>
                  <td>{r.share_consistent != null ? `${Math.round(r.share_consistent * r.n_events)} of ${r.n_events}` : "–"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : <p className="muted">No reactions measured yet.</p>}
      <p className="small muted">With 20 or more stories per event, these results turn our starting expectations into measured facts.</p>
    </StepBlock>
  );
}
