// Which outlets we read, how far we trust each, and whether each earns its place.
import { api } from "../../api/client";
import { humanize } from "../../shared/labels";
import { State } from "../../shared/ui";
import { useApi } from "../../shared/useApi";

const pct = (x?: number) => (x == null ? "–" : `${Math.round(x * 100)}%`);

export function SourcesTab() {
  const sources = useApi(api.sources);
  const coverage = useApi(api.coverage);
  const cov = new Map((coverage.data ?? []).map((c) => [c.source_id, c]));
  return (
    <>
      <p className="muted">
        Trust starts from the kind of outlet (a filing &gt; a wire &gt; a newspaper &gt; a blog) and moves with its track record.
        An outlet earns its place if it writes about the companies we watch and is often first to report a stage.
      </p>
      <State error={sources.error} loading={sources.loading}>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Outlet</th><th>Kind</th><th>Trust</th><th>Articles</th><th>About our companies</th><th>Reported first</th></tr></thead>
            <tbody>
              {(sources.data ?? []).map(({ source, reliability, enabled }) => {
                const c = cov.get(source.source_id);
                return (
                  <tr key={source.source_id} className={enabled ? "" : "disabled"}>
                    <td><b>{source.name}</b> <span className="muted small">{source.country ?? ""}{!enabled && " · paused"}</span></td>
                    <td>{humanize(source.source_type)}</td>
                    <td>
                      <div className="bar"><span style={{ width: `${reliability.score * 100}%` }} /></div>
                      <span className="small muted">{reliability.score.toFixed(2)}</span>
                    </td>
                    <td>{c?.articles ?? 0}</td>
                    <td>{pct(c?.with_company)}</td>
                    <td>{c?.stages_first ?? 0} stage(s)</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </State>
    </>
  );
}
