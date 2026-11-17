// Tab 1 - which news sources we read and how much we trust each. The score is shown as a sum
// (start + confirmed − half of not confirmed) and each source's record as a bar; the full
// working is one hover away.
import { api } from "../../api/client";
import { humanize } from "../../shared/labels";
import { Term } from "../../shared/Term";
import { State } from "../../shared/ui";
import { useApi } from "../../shared/useApi";
import { Meter, reliabilityTone } from "../../shared/viz";
import { setting, type MethodData } from "./MethodPage";

const pct = (x?: number | null) => (x == null ? "–" : `${Math.round(x * 100)}%`);

export function MonitorStep({ method }: MethodData) {
  const sources = useApi(api.sources);
  const coverage = useApi(api.coverage);
  const weight = setting(method, "validation", "unconfirmed_weight") ?? 0.5;
  const days = setting(method, "validation", "confirmation_days") ?? 7;
  const k = method.prior_strength;
  const cov = new Map((coverage.data ?? []).map((c) => [c.source_id, c]));
  const active = (sources.data ?? []).filter((s) => s.enabled).sort((a, b) => b.reliability.score - a.reliability.score);
  const kinds = [...new Set(active.map((s) => s.source.source_type))].filter((t) => method.source_priors[t]);
  return (
    <section className="step-block">
      <h2>How much we trust each news source</h2>
      <div className="formula" aria-label="How a trust score is worked out">
        <Term tip={`Each kind of source starts with an estimate of how often its reports hold up, from how it checks before publishing. It weighs as much as ${k} reports.`}>
          <span className="f-chip">Start<small>kind of source</small></span></Term>
        <span className="f-op">+</span>
        <Term tip={`After ${days} days: did another, independent outlet report the same thing? Copies of one article count once.`}>
          <span className="f-chip good">✓ +1<small>confirmed by another outlet</small></span></Term>
        <span className="f-op">−</span>
        <Term tip={`Not repeated by anyone within ${days} days counts as half a miss: a true scoop can stay exclusive.`}>
          <span className="f-chip muted">✗ −½<small>not confirmed</small></span></Term>
        <span className="f-op">=</span>
        <Term tip={`Score = (start × ${k} + confirmed) ÷ (${k} + confirmed + ${weight} × not confirmed).`}>
          <span className="f-chip accent">Trust score</span></Term>
      </div>
      <div className="prior-bars">
        {kinds.map((t) => (
          <Term key={t} tip={method.source_priors[t].why}>
            <span className="prior-bar"><span>{humanize(t)}</span><Meter value={method.source_priors[t].start} tone="neutral" /><b>{pct(method.source_priors[t].start)}</b></span>
          </Term>
        ))}
        <span className="small muted">starting estimates</span>
      </div>
      <State error={sources.error} loading={sources.loading}>
        <ul className="source-list">
          {active.map(({ source, reliability: r }) => {
            const c = cov.get(source.source_id);
            const ok = Math.round(r.supported), missed = Math.round(r.refuted / weight), judged = ok + missed;
            const working = judged
              ? `Started at ${pct(r.prior)}. Of its ${judged} reports old enough to check, ${ok} were also reported by another outlet and ${missed} were not (each counted as half a miss), so the score is now ${pct(r.score)}.`
              : "None of its reports is old enough to check yet, so the score is still the starting estimate.";
            return (
              <li key={source.source_id} className="source-row">
                <div className="source-name">
                  <b>{source.name.split(" - ")[0]}</b>
                  <span className="muted small">{humanize(source.source_type)} · {source.country} · {c?.articles ?? 0} articles</span>
                </div>
                <Term tip={working}>
                  <span className={`big-num ${reliabilityTone(r.score)}`}>{pct(r.score)}</span>
                </Term>
                <div className="record">
                  {judged ? (
                    <>
                      <div className="record-bar" role="img" aria-label={`${ok} confirmed, ${missed} not confirmed`}>
                        <span className="ok" style={{ flexGrow: ok }} /><span className="miss" style={{ flexGrow: missed }} />
                      </div>
                      <span className="small"><b className="good">✓ {ok}</b> confirmed · <span className="muted">✗ {missed} not</span></span>
                    </>
                  ) : <span className="small muted">no report old enough to check yet</span>}
                </div>
                {c && <Term tip={`${pct(c.with_company)} of its articles name a company we follow; ${pct(c.in_stories)} became an update of an event.`}>
                  <span className="small muted">{pct(c.in_stories)} → events</span></Term>}
              </li>
            );
          })}
        </ul>
        <p className="small muted">Low score = rarely repeated by others, not shown wrong.</p>
      </State>
    </section>
  );
}
