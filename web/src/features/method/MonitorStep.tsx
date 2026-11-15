// Tab 1 - which news sources we read and how reliable each is, with live numbers.
import { api, type S } from "../../api/client";
import { humanize } from "../../shared/labels";
import { State } from "../../shared/ui";
import { useApi } from "../../shared/useApi";
import { StepBlock } from "./StepBlock";

const pct = (x?: number) => (x == null ? "–" : `${Math.round(x * 100)}%`);

export function MonitorStep({ method }: { method: S["Method"] }) {
  const v = ((method.methodology as Record<string, unknown>).validation ?? {}) as Record<string, unknown>;
  const sources = useApi(api.sources);
  const coverage = useApi(api.coverage);
  const cov = new Map((coverage.data ?? []).map((c) => [c.source_id, c]));
  const active = (sources.data ?? []).filter((s) => s.enabled);
  return (
    <StepBlock title="Which news sources we read, and how reliable each is"
      term="source credibility scoring"
      rules={[
        "A source is added only if it is original (news agency, regulator, the company) or widely read by investors.",
        "Reliability starts from the kind of source (official filing > news agency > newspaper > press release > blog), then moves with its track record.",
        "A source stays only if it covers the companies we follow and is sometimes first to report an event.",
        "Copies of another source's article are kept but never counted as an extra source.",
        <>An update is <b>confirmed</b> when {String(v.corroborating_origins ?? 2)} or more independent sources report it, or the company or an official filing does.</>,
      ]}>
      <State error={sources.error} loading={sources.loading}>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Source</th><th>Reliability</th><th className="num">Articles</th><th className="num">Name a tracked company</th><th className="num">Used in an event</th></tr></thead>
            <tbody>
              {active.map(({ source, reliability }) => {
                const c = cov.get(source.source_id);
                return (
                  <tr key={source.source_id}>
                    <td><b>{source.name}</b><div className="muted small">{humanize(source.source_type)} · {source.country}</div></td>
                    <td><div className="bar"><span style={{ width: `${reliability.score * 100}%` }} /></div><span className="small">{Math.round(reliability.score * 100)}%</span></td>
                    <td className="num">{c?.articles ?? 0}</td><td className="num">{pct(c?.with_company)}</td><td className="num">{pct(c?.in_stories)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="small muted">Reliability = the chance a claim from this source holds up.</p>
      </State>
    </StepBlock>
  );
}
