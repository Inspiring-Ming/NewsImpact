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
  // The server computes each event type's track record (views/guidance.py); every event
  // of a type carries the same one.
  const records = new Map((companies.data ?? []).flatMap((c) => c.events).map((e) => [e.event_type, e.record]));
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
                const r = records.get(name);
                const expected = r?.expected ?? p.stages.flatMap((s) => s.decisions).find((d) => d.market_channel === "price")?.expected_direction;
                const n = r?.n ?? 0, avg = r?.average ?? null, unusual = r?.unusual ?? 0, hit = r?.as_expected ?? 0;
                return (
                  <tr key={p.theme}>
                    <td><b>{name}</b></td>
                    <td>{expected ? <span className={`expect ${EXPECT[expected].tone}`}>{EXPECT[expected].text}</span> : <span className="muted">not set</span>}</td>
                    <td className="num">{n}</td>
                    <td>{avg == null ? <span className="muted">–</span> : <div className="move-top"><MoveBar value={avg} unusual={Math.abs(avg) >= 0.02} span={0.1} /><b>{pct(avg)}</b></div>}</td>
                    <td className="num">{n ? `${unusual} of ${n}` : "–"}</td>
                    <td>{n && expected ? (
                      <div className="conf"><Meter value={hit / n} tone={hit / n >= 0.6 ? "good" : hit / n >= 0.4 ? "warn" : "bad"} /> <b>{hit} of {n}</b></div>
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
