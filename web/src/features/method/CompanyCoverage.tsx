// Does the news reach every company we follow? Articles naming each company in the coverage
// window (from the snapshot the hourly round publishes), the companies with none, and when
// and by which reading these figures were computed - so every number can be traced.
import { api } from "../../api/client";
import { State } from "../../shared/ui";
import { Term } from "../../shared/Term";
import { useApi } from "../../shared/useApi";

const THINNEST = 8; // how many of the least-covered companies to list

export function CompanyCoverage() {
  const report = useApi(api.companyCoverage);
  const d = report.data;
  const gaps = d?.companies.filter((c) => c.status === "gap") ?? [];
  const thin = d?.companies.filter((c) => c.status === "ok").slice(0, THINNEST) ?? [];
  return (
    <div className="coverage-block">
      <h3><Term id="companyCoverage" /></h3>
      <State error={report.error} loading={report.loading}>
        {d && (
          <>
            <p>
              <b>{d.companies.length - gaps.length} of {d.companies.length}</b> companies were named in the news in the last {d.window_days} days.
            </p>
            {gaps.length > 0 && (
              <p className="small"><span className="verdict-badge bad">No news found</span> {gaps.map((c) => `${c.name} (${c.ticker})`).join(", ")}</p>
            )}
            <p className="small muted">
              Fewest articles: {thin.map((c) => `${c.name} (${c.articles})`).join(" · ")}
            </p>
            <details className="small muted trace">
              <summary>Computed {new Date(d.computed_at).toLocaleString()} after the latest update round</summary>
              Reading method, every step in order: <code>{d.analysis}</code>
            </details>
          </>
        )}
      </State>
    </div>
  );
}
