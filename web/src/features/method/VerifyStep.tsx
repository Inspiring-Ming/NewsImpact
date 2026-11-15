// Tab 3 - does each kind of news really move the stock? The expectation from research
// next to what happened in the events we measured.
import { api, type S } from "../../api/client";
import { label, pct } from "../../shared/labels";
import { State } from "../../shared/ui";
import { Term } from "../../shared/Term";
import { useApi } from "../../shared/useApi";
import { Meter, MoveBar } from "../../shared/viz";
import { StepBlock } from "./StepBlock";

const EXPECT: Record<string, { text: string; tone: string }> = {
  down: { text: "↓ falls", tone: "bad" }, up: { text: "↑ rises", tone: "good" }, uncertain: { text: "↕ big move either way", tone: "warn" },
};

export function VerifyStep({ method }: { method: S["Method"] }) {
  const companies = useApi(api.companies);
  const events = (companies.data ?? []).flatMap((c) => c.events);
  return (
    <StepBlock term="marketTab">
      <State error={companies.error} loading={companies.loading}>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Event type</th><th><Term id="expectShare" /></th><th className="num"><Term id="measured" /></th>
                <th><Term id="avgMove" /></th><th className="num"><Term id="unusual">Unusual moves</Term></th>
                <th><Term id="asExpected" /></th>
              </tr>
            </thead>
            <tbody>
              {method.playbooks.map((p) => {
                const name = p.title || label(p.theme);
                const expected = p.stages.flatMap((s) => s.decisions).find((d) => d.market_channel === "price")?.expected_direction;
                const done = events.filter((e) => e.event_type === name && e.stock_move != null);
                const avg = done.length ? done.reduce((n, e) => n + e.stock_move!, 0) / done.length : null;
                const hit = done.filter((e) => expected === "uncertain" ? e.stock_move_unusual
                  : expected === "down" ? e.stock_move! < 0 : expected === "up" ? e.stock_move! > 0 : false).length;
                return (
                  <tr key={p.theme}>
                    <td><b>{name}</b></td>
                    <td>{expected ? <span className={`expect ${EXPECT[expected].tone}`}>{EXPECT[expected].text}</span> : <span className="muted">not set</span>}</td>
                    <td className="num">{done.length}</td>
                    <td>{avg == null ? <span className="muted">–</span> : <div className="move-top"><MoveBar value={avg} unusual={Math.abs(avg) >= 0.02} span={0.1} /><b>{pct(avg)}</b></div>}</td>
                    <td className="num">{done.length ? `${done.filter((e) => e.stock_move_unusual).length} of ${done.length}` : "–"}</td>
                    <td>{done.length && expected ? (
                      <div className="conf"><Meter value={hit / done.length} tone={hit / done.length >= 0.6 ? "good" : hit / done.length >= 0.4 ? "warn" : "bad"} /> <b>{hit} of {done.length}</b></div>
                    ) : <span className="muted">–</span>}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="small muted">Colour on the bars: green = matches the expectation in most events (60% or more), amber = mixed, red = rarely. Few events means the result can still change a lot.</p>
      </State>
    </StepBlock>
  );
}
