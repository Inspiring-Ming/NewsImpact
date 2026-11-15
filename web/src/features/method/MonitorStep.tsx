// Tab 1 - which news sources we read and how reliable each is, with live numbers.
import { api } from "../../api/client";
import { humanize } from "../../shared/labels";
import { State } from "../../shared/ui";
import { useApi } from "../../shared/useApi";
import { Term } from "../../shared/Term";
import { StepBlock } from "./StepBlock";

const pct = (x?: number) => (x == null ? "–" : `${Math.round(x * 100)}%`);

export function MonitorStep() {
  const sources = useApi(api.sources);
  const coverage = useApi(api.coverage);
  const cov = new Map((coverage.data ?? []).map((c) => [c.source_id, c]));
  const active = (sources.data ?? []).filter((s) => s.enabled);
  return (
    <StepBlock term="sourcesTab">
      <State error={sources.error} loading={sources.loading}>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Source</th><th><Term id="reliability" /></th><th className="num"><Term id="articles" /></th><th className="num"><Term id="relevance" /></th><th className="num"><Term id="usedInEvent" /></th></tr></thead>
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
      </State>
    </StepBlock>
  );
}
