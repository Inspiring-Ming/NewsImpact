// Tab 1 - which news sources we read and how much we trust each, with the sum behind every
// score written out: a starting estimate for its kind of source, moved by its own record.
import { api } from "../../api/client";
import { humanize } from "../../shared/labels";
import { State } from "../../shared/ui";
import { useApi } from "../../shared/useApi";
import { Meter, reliabilityTone } from "../../shared/viz";
import { Flow, setting, type MethodData } from "./MethodPage";

const pct = (x?: number | null) => (x == null ? "–" : `${Math.round(x * 100)}%`);

export function MonitorStep({ method }: MethodData) {
  const sources = useApi(api.sources);
  const coverage = useApi(api.coverage);
  const weight = setting(method, "validation", "unconfirmed_weight") ?? 0.5;
  const days = setting(method, "validation", "confirmation_days") ?? 7;
  const k = method.prior_strength;
  const cov = new Map((coverage.data ?? []).map((c) => [c.source_id, c]));
  const active = (sources.data ?? []).filter((s) => s.enabled).sort((a, b) => b.reliability.score - a.reliability.score);
  const kinds = [...new Set(active.map((s) => s.source.source_type))];
  return (
    <section className="step-block">
      <h2>Which news sources we read, and how much we trust each</h2>
      <Flow steps={[
        { title: "Start from the kind of source", text: <>Each kind starts with an estimate of how often its reports hold up, from how it checks before publishing:
          <ul className="prior-list">{kinds.map((t) => method.source_priors[t] && (
            <li key={t}><b>{humanize(t)} {pct(method.source_priors[t].start)}</b> — {method.source_priors[t].why}</li>))}</ul></> },
        { title: `Check each report after ${days} days`, text: <>Did another, independent outlet report the same thing? Copies of one article count once. Yes = confirmed. No = not confirmed, which counts as <b>half</b> a miss: a true scoop can stay exclusive.</> },
        { title: "Move the score with the record", text: <>Score = (start × {k} + confirmed) ÷ ({k} + confirmed + ½ × not confirmed). The starting estimate weighs as much as {k} reports; after that, the source's own record counts more and more.</> },
      ]} />
      <State error={sources.error} loading={sources.loading}>
        <ul className="source-list">
          {active.map(({ source, reliability: r }) => {
            const c = cov.get(source.source_id);
            const confirmed = Math.round(r.supported), missed = Math.round(r.refuted / weight);
            return (
              <li key={source.source_id} className="source-row">
                <div className="source-name">
                  <b>{source.name.split(" - ")[0]}</b>
                  <span className="muted small">{humanize(source.source_type)} · {source.country} · {c?.articles ?? 0} articles</span>
                </div>
                <div className="source-score">
                  <span className={`big-num ${reliabilityTone(r.score)}`}>{pct(r.score)}</span>
                  <Meter value={r.score} tone={reliabilityTone(r.score)} />
                </div>
                <p className="source-why small">
                  Started at {pct(r.prior)}.{" "}
                  {confirmed + missed
                    ? <>Of its <b>{confirmed + missed}</b> reports old enough to check, <b>{confirmed}</b> were also reported by another outlet and <b>{missed}</b> were not (each counted as half a miss), so the score is now <b>{pct(r.score)}</b>.</>
                    : <>None of its reports is old enough to check yet, so the score is still the starting estimate.</>}
                  {c && <span className="muted"> {pct(c.with_company)} of its articles name a company we follow; {pct(c.in_stories)} became an update of an event.</span>}
                </p>
              </li>
            );
          })}
        </ul>
        <p className="small muted">A low score means few of its reports were repeated by others, not that they were shown wrong. Aggregators like Yahoo Finance carry many small stories that no one else covers.</p>
      </State>
    </section>
  );
}
