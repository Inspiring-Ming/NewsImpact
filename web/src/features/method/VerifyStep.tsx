// Tab 3 - does each kind of news really move the stock? The expectation from research
// next to what happened in the events we measured.
import { api, type S } from "../../api/client";
import { label, pct } from "../../shared/labels";
import { State } from "../../shared/ui";
import { Term } from "../../shared/Term";
import { useApi } from "../../shared/useApi";
import { StepBlock } from "./StepBlock";

const EXPECT: Record<string, string> = { down: "↓ falls", up: "↑ rises", uncertain: "↕ big move either way" };

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
                <th className="num"><Term id="avgMove" /></th><th className="num"><Term id="unusual">Unusual moves</Term></th>
                <th className="num"><Term id="asExpected" /></th>
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
                    <td>{expected ? EXPECT[expected] : <span className="muted">not set</span>}</td>
                    <td className="num">{done.length}</td>
                    <td className="num">{avg == null ? "–" : pct(avg)}</td>
                    <td className="num">{done.length ? `${done.filter((e) => e.stock_move_unusual).length} of ${done.length}` : "–"}</td>
                    <td className="num">{done.length && expected ? <b>{hit} of {done.length}</b> : "–"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </State>
    </StepBlock>
  );
}
