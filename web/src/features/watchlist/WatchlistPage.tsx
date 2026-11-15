// Home: the companies we follow. Developing stories first, then other news, then the rest.
import { useState } from "react";
import { api } from "../../api/client";
import { State } from "../../shared/ui";
import { useApi } from "../../shared/useApi";
import { CompanyRow } from "./CompanyRow";
import { StoryCard } from "./StoryCard";

const COUNTRIES = [["all", "All"], ["US", "🇺🇸 United States"], ["AU", "🇦🇺 Australia"]] as const;

export function WatchlistPage({ refreshKey }: { refreshKey: number }) {
  const { data, error, loading } = useApi(api.companies, [refreshKey]);
  const [country, setCountry] = useState<string>("all");
  const all = data ?? [];
  const shown = all.filter((c) => country === "all" || c.country === country);
  const withStories = shown.filter((c) => c.stories.some((s) => s.confirmed !== "no"));
  // A story reported by a single outlet may be a misreading; keep it apart until confirmed.
  const unconfirmed = shown.flatMap((c) => c.stories.filter((s) => s.confirmed === "no").map((s) => ({ c, s })));
  const inNews = shown.filter((c) => !c.stories.length && c.latest_news);
  const quiet = shown.filter((c) => !c.stories.length && !c.latest_news);
  const storyCount = withStories.reduce((n, c) => n + c.stories.filter((s) => s.confirmed !== "no").length, 0);

  return (
    <>
      <section className="hero">
        <h1>Company news and stock reactions</h1>
        <p className="lead">
          We follow {all.length || "…"} large companies in the United States and Australia. When news about one of them
          turns into a developing story, such as a CEO resignation, a product recall or a takeover, we track each step,
          check that it is confirmed by several news outlets, and measure how the stock reacted compared with its market.
        </p>
      </section>

      <div className="filters">
        <div className="segmented" role="group" aria-label="Country">
          {COUNTRIES.map(([id, name]) => (
            <button key={id} className={id === country ? "active" : ""} onClick={() => setCountry(id)}>{name}</button>
          ))}
        </div>
      </div>

      <State error={error} loading={loading && !data}>
        <section className="section">
          <div className="section-head">
            <h2>Developing stories <span className="count">{storyCount}</span></h2>
            <p className="muted">News that is unfolding over several events, with its effect on the stock.</p>
          </div>
          {withStories.length ? (
            <div className="cards">
              {withStories.flatMap((c) => c.stories.filter((s) => s.confirmed !== "no")
                .map((s) => <StoryCard key={s.storyline_id} company={c} story={s} />))}
            </div>
          ) : (
            <p className="state empty">No developing stories right now. Press <b>Check for news</b> at the top to read the latest news.</p>
          )}
        </section>

        {unconfirmed.length > 0 && (
          <section className="section">
            <div className="section-head">
              <h2>Waiting for confirmation <span className="count">{unconfirmed.length}</span></h2>
              <p className="muted">Possible stories reported by only one outlet so far. They may be a misreading, so we wait for a second, independent source.</p>
            </div>
            <ul className="company-list">
              {unconfirmed.map(({ c, s }) => (
                <li key={s.storyline_id} className="company-row">
                  <div className="company-row-name"><b>{c.name}</b><span className="muted small">{s.story_type}</span></div>
                  <a className="company-row-news" href={`#/story/${s.storyline_id}`}>{s.latest_headline}</a>
                  <span className="muted small company-row-meta">{s.confirmed_text}</span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {inNews.length > 0 && (
          <section className="section">
            <div className="section-head">
              <h2>Also in the news <span className="count">{inNews.length}</span></h2>
              <p className="muted">Latest headline for companies mentioned in the news, with no developing story yet.</p>
            </div>
            <ul className="company-list">{inNews.map((c) => <CompanyRow key={c.ticker} company={c} />)}</ul>
          </section>
        )}

        {quiet.length > 0 && (
          <section className="section">
            <div className="section-head">
              <h2>No recent news <span className="count">{quiet.length}</span></h2>
            </div>
            <p className="muted small quiet">{quiet.map((c) => c.name).join(" · ")}</p>
          </section>
        )}
      </State>
    </>
  );
}
