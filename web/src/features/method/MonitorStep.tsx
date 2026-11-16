// Tab 1 - which news sources we read, how reliable each is and why: a starting estimate
// for its type, moved by its track record (how often other sources confirmed its reports).
import { api, type S } from "../../api/client";
import { humanize } from "../../shared/labels";
import { State } from "../../shared/ui";
import { Term } from "../../shared/Term";
import { useApi } from "../../shared/useApi";
import { Meter, reliabilityTone } from "../../shared/viz";
import { CompanyCoverage } from "./CompanyCoverage";
import { StepBlock } from "./StepBlock";

const pct = (x?: number) => (x == null ? "–" : `${Math.round(x * 100)}%`);

export function MonitorStep({ method }: { method: S["Method"] }) {
  const sources = useApi(api.sources);
  const coverage = useApi(api.coverage);
  const v = ((method.methodology as Record<string, unknown>).validation ?? {}) as Record<string, number>;
  const weight = v.unconfirmed_weight || 0.5;
  const cov = new Map((coverage.data ?? []).map((c) => [c.source_id, c]));
  const active = (sources.data ?? []).filter((s) => s.enabled).sort((a, b) => b.reliability.score - a.reliability.score);
  return (
    <StepBlock term="sourcesTab">
      <CompanyCoverage />
      <State error={sources.error} loading={sources.loading}>
        <div className="table-wrap">
          <table className="sources-table">
            <thead>
              <tr>
                <th>Source</th><th><Term id="reliability">Reliability now</Term></th><th className="num"><Term id="prior" /></th>
                <th className="num"><Term id="trackRecord" /></th><th className="num"><Term id="relevance" /></th>
                <th className="num"><Term id="usedInEvent" /></th>
              </tr>
            </thead>
            <tbody>
              {active.map(({ source, reliability: r }) => {
                const c = cov.get(source.source_id);
                const confirmed = Math.round(r.supported), unconfirmed = Math.round(r.refuted / weight);
                return (
                  <tr key={source.source_id}>
                    <td><b>{source.name.split(" - ")[0]}</b><div className="muted small">{humanize(source.source_type)} · {source.country} · {c?.articles ?? 0} articles</div></td>
                    <td><div className="conf"><Meter value={r.score} tone={reliabilityTone(r.score)} /> <b>{pct(r.score)}</b></div></td>
                    <td className="num">{pct(r.prior)}</td>
                    <td className="num">{confirmed + unconfirmed ? <><b>{confirmed}</b> of {confirmed + unconfirmed} confirmed</> : <span className="muted">none judged yet</span>}</td>
                    <td className="num">{pct(c?.with_company)}</td><td className="num">{pct(c?.in_stories)}</td>
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
