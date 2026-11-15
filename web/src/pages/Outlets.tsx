// Which outlets we watch, how reliable they are, and whether they earn their place.
import { api } from "../api/client";
import { Card, Loading, num, Page, pct } from "../components/ui";
import { useApi } from "../components/useApi";

export function Outlets() {
  const sources = useApi(api.sources);
  const coverage = useApi(api.coverage);
  const cov = new Map((coverage.data ?? []).map((c) => [c.source_id, c]));
  return (
    <Page
      title="Outlets"
      intro={<>Reliability starts from the outlet type and moves with its track record. Coverage shows whether an outlet earns its place
        (rule in <a href="#/method">Method</a>): watched companies, storyline triggers, copies of others, and stages it reported first.</>}
    >
      <Loading error={sources.error} loading={sources.loading} />
      <Card wide>
        <table>
          <thead><tr>
            <th>Outlet</th><th>Type</th><th>Country</th><th>Reliability</th><th>95% interval</th>
            <th>Articles</th><th>Name a watched company</th><th>Contain a trigger</th><th>Copies</th><th>Stages first</th>
          </tr></thead>
          <tbody>
            {(sources.data ?? []).map(({ source, reliability, enabled }) => {
              const c = cov.get(source.source_id);
              return (
                <tr key={source.source_id} className={enabled ? "" : "disabled"}>
                  <td><b>{source.name}</b>{!enabled && <span className="muted"> (disabled)</span>}{!source.listed && <span className="muted"> (unlisted)</span>}</td>
                  <td>{source.source_type.replace(/_/g, " ")}</td>
                  <td>{source.country ?? "–"}</td>
                  <td><b>{num(reliability.score)}</b></td>
                  <td className="muted">{num(reliability.ci_low)}–{num(reliability.ci_high)}</td>
                  <td>{c?.articles ?? 0}</td>
                  <td>{pct(c?.with_company)}</td>
                  <td>{pct(c?.with_trigger)}</td>
                  <td>{pct(c?.copies)}</td>
                  <td>{c?.stages_first ?? 0}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </Card>
    </Page>
  );
}
