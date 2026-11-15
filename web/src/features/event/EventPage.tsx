// One event: key numbers on top, then tabs, so nothing needs long scrolling.
// To show something new, add one entry to TABS.
import { useState, type ComponentType } from "react";
import { api } from "../../api/client";
import { COUNTRY, pct } from "../../shared/labels";
import { Fact, State, Tabs } from "../../shared/ui";
import { useApi } from "../../shared/useApi";
import { AnalystData } from "./AnalystData";
import type { EventData } from "./context";
import { Overview } from "./Overview";
import { Scorecard } from "./Scorecard";
import { Updates } from "./Updates";

const TABS: { id: string; label: string; component: ComponentType<EventData> }[] = [
  { id: "overview", label: "Overview", component: Overview },
  { id: "updates", label: "Updates", component: Updates },
  { id: "reaction", label: "Expected vs actual", component: Scorecard },
  { id: "data", label: "Analyst data", component: AnalystData },
];

export function EventPage({ id }: { id: string }) {
  const summary = useApi(() => api.eventSummary(id), [id]);
  const story = useApi(() => api.storyline(id), [id]);
  const assessment = useApi(() => api.assessment(id), [id]);
  const prices = useApi(() => api.prices(id), [id]);
  const [tab, setTab] = useState(TABS[0].id);
  const company = summary.data, card = company?.events[0], s = story.data, a = assessment.data;
  const country = company ? COUNTRY[company.country] : undefined;
  const Body = TABS.find((t) => t.id === tab)!.component;
  return (
    <>
      <a className="back" href="#/">← Watchlist</a>
      <State error={summary.error ?? story.error ?? assessment.error} loading={!company || !card || !s || !a}>
        {company && card && s && a && (
          <>
            <header className="event-head">
              <div>
                <span className="tag">{card.event_type}</span>{" "}
                <span className="muted small">{card.ongoing ? "Developing" : "Complete"}</span>
              </div>
              <h1>{company.name}</h1>
              <div className="muted">{country?.flag} {company.ticker} · {company.sector}</div>
              <p className="lead-small">{card.latest_headline}</p>
            </header>
            <div className="kpis">
              <Fact label={`Stock vs ${company.index_name}`}
                    value={card.stock_move == null ? "–" : pct(card.stock_move)}
                    tone={card.stock_move_unusual ? (card.stock_move! < 0 ? "bad" : "good") : undefined}
                    sub={card.stock_move == null ? "no price data yet" : `${card.stock_move_period} · ${card.stock_move_unusual ? "unusual move" : "normal range"}`} />
              <Fact label="Updates" value={card.updates.length} sub={card.ongoing ? "more may follow" : "event complete"} />
              <Fact label="Sources" value={card.sources} sub={`${Math.round(card.source_reliability * 100)}% avg. reliability`} />
              <Fact label="Reactions as expected" value={a.market_support == null ? "–" : `${Math.round(a.market_support * 100)}%`}
                    sub="of those measurable in prices" />
            </div>
            <Tabs tabs={TABS} active={tab} onChange={setTab} />
            <Body company={company} card={card} story={s} assessment={a} prices={prices.data ?? null} />
          </>
        )}
      </State>
    </>
  );
}
