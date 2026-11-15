// Step 1 - which outlets we read and how far we trust each, with live numbers.
import { api } from "../../api/client";
import { humanize } from "../../shared/labels";
import { State } from "../../shared/ui";
import { useApi } from "../../shared/useApi";
import { StepBlock } from "./StepBlock";

const pct = (x?: number) => (x == null ? "–" : `${Math.round(x * 100)}%`);

export function MonitorStep() {
  const sources = useApi(api.sources);
  const coverage = useApi(api.coverage);
  const cov = new Map((coverage.data ?? []).map((c) => [c.source_id, c]));
  const active = (sources.data ?? []).filter((s) => s.enabled);
  return (
    <StepBlock id="monitor"
      what="We read a short list of trusted US and Australian business outlets automatically, and remember how often each one turns out to be right."
      rules={[
        "Start small: an outlet is added only if it is an original source (news agency, regulator, the company) or widely read by investors.",
        "Trust starts from the kind of outlet (regulatory filing > news agency > newspaper > press release > blog) and then moves with its track record.",
        "An outlet keeps its place only if it writes about the companies we follow and is sometimes first to report an event.",
        "Copies of another outlet's article are kept but never counted as extra confirmation.",
      ]}>
      <State error={sources.error} loading={sources.loading}>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Outlet</th><th>Trust</th><th>Articles</th><th>About our companies</th><th>Part of a story</th></tr></thead>
            <tbody>
              {active.map(({ source, reliability }) => {
                const c = cov.get(source.source_id);
                return (
                  <tr key={source.source_id}>
                    <td><b>{source.name}</b><div className="muted small">{humanize(source.source_type)} · {source.country}</div></td>
                    <td><div className="bar"><span style={{ width: `${reliability.score * 100}%` }} /></div><span className="small">{Math.round(reliability.score * 100)}%</span></td>
                    <td>{c?.articles ?? 0}</td><td>{pct(c?.with_company)}</td><td>{pct(c?.in_stories)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="small muted">Trust = the chance a claim from this outlet holds up, from its kind and track record.</p>
      </State>
    </StepBlock>
  );
}
