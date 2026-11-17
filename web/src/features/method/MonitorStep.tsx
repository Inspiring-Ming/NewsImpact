// Tab 1 - how much we trust each news source, as a dumbbell chart: where its kind of source
// starts (hollow) and where its own record has moved it (filled). The sum is one hover away.
import { api } from "../../api/client";
import { humanize } from "../../shared/labels";
import { Term } from "../../shared/Term";
import { State } from "../../shared/ui";
import { useApi } from "../../shared/useApi";
import { Flow, Head, setting, type MethodData } from "./MethodPage";

const pct = (x?: number | null) => (x == null ? "–" : `${Math.round(x * 100)}%`);
const AXIS = [0.25, 0.5, 0.75, 1];
const at = (x: number) => `${Math.max(0, Math.min(1, x)) * 100}%`;

export function MonitorStep({ method }: MethodData) {
  const sources = useApi(api.sources);
  const weight = setting(method, "validation", "unconfirmed_weight") ?? 0.5;
  const days = setting(method, "validation", "confirmation_days") ?? 7;
  const k = method.prior_strength;
  const active = (sources.data ?? []).filter((s) => s.enabled).sort((a, b) => b.reliability.score - a.reliability.score);
  return (
    <section className="hiw">
      <Head kicker="Step 1 · Sources" title="How much we trust each news source"
            dek={<>Every source starts from what its kind usually gets right, then moves with its own record:
              did another outlet report the same thing within {days} days?</>} />
      <Flow steps={[
        { title: "Start", line: "by kind of source", tip: `Official filing 95%, news agency 80%, newspaper 75%, press release and aggregator 67%: ordered by how content is checked before it is published. The start weighs as much as ${k} reports.` },
        { title: "Confirmed", line: "+1 each", tip: `Another, independent outlet reported the same thing within ${days} days. Copies of one article count once.` },
        { title: "Not confirmed", line: `−${weight} each`, tip: `Nobody else reported it within ${days} days. It counts as half a miss, because a true scoop can stay exclusive.` },
        { title: "Score", line: "where it stands now", tip: `(start × ${k} + confirmed) ÷ (${k} + confirmed + ${weight} × not confirmed)` },
      ]} />
      <State error={sources.error} loading={sources.loading}>
        <div className="dumbbell" role="table" aria-label="Trust score of each source">
          <div className="db-axis" aria-hidden="true">
            <span />
            <div className="db-track">{AXIS.map((x) => <i key={x} style={{ left: at(x) }}>{pct(x)}</i>)}</div>
            <span />
          </div>
          {active.map(({ source, reliability: r }) => {
            const ok = Math.round(r.supported), missed = Math.round(r.refuted / weight), judged = ok + missed;
            const up = r.score >= r.prior;
            const working = judged
              ? `Started at ${pct(r.prior)}. Of ${judged} reports old enough to check, ${ok} were also reported by another outlet and ${missed} were not (each half a miss): now ${pct(r.score)}.`
              : "No report old enough to check yet: still the starting estimate.";
            return (
              <div key={source.source_id} className="db-row" role="row">
                <div className="db-name" role="cell">
                  <b>{source.name.split(" - ")[0]}</b>
                  <small>{humanize(source.source_type)} · {source.country}</small>
                </div>
                <Term tip={working}>
                  <div className="db-track" role="cell" aria-label={working}>
                    {AXIS.map((x) => <span key={x} className="db-grid" style={{ left: at(x) }} />)}
                    <span className={`db-bar ${up ? "up" : "down"}`}
                          style={{ left: at(Math.min(r.prior, r.score)), width: at(Math.abs(r.score - r.prior)) }} />
                    <span className="db-start" style={{ left: at(r.prior) }} />
                    <span className={`db-now ${up ? "up" : "down"}`} style={{ left: at(r.score) }} />
                  </div>
                </Term>
                <div className="db-value" role="cell">
                  <b>{pct(r.score)}</b>
                  <small>{judged ? <><span className="good">{ok} ✓</span> · {missed} ✗</> : "not judged yet"}</small>
                </div>
              </div>
            );
          })}
        </div>
        <p className="hiw-legend"><span className="db-start static" /> start for its kind <span className="db-now up static" /> now, after its record
          <span className="sep" /> A low score means rarely repeated by others, not shown wrong.</p>
      </State>
    </section>
  );
}
