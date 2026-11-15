// A company in the news without a developing story: its latest headline.
import type { S } from "../../api/client";
import { COUNTRY, date } from "../../shared/labels";

export function CompanyRow({ company }: { company: S["CompanyCard"] }) {
  const n = company.latest_news!;
  const country = COUNTRY[company.country];
  return (
    <li className="company-row">
      <div className="company-row-name">
        <b>{company.name}</b>
        <span className="muted small">{country?.flag} {company.ticker}</span>
      </div>
      <a className="company-row-news" href={n.url} target="_blank" rel="noreferrer">{n.title}</a>
      <span className="muted small company-row-meta">
        {n.outlet} · {date(n.published_at)}{company.articles > 1 && ` · ${company.articles} articles`}
      </span>
    </li>
  );
}
