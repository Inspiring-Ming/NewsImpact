// One event: key numbers on top, then tabs, so nothing needs long scrolling.
// To show something new, add one entry to TABS.
import { useState, type ComponentType } from "react";
import { api } from "../../api/client";
import { COUNTRY, date, NO_MOVE, pct, vsWords } from "../../shared/labels";
import { confidenceTone, Dots, Meter, MoveBar, RatioBar } from "../../shared/viz";
import { Term } from "../../shared/Term";
import { Fact, State, Tabs } from "../../shared/ui";
import { useApi } from "../../shared/useApi";
import type { EventData } from "./context";
import { Overview } from "./Overview";
import { Scorecard } from "./Scorecard";
import { Updates } from "./Updates";

const TABS: { id: string; label: string; component: ComponentType<EventData> }[] = [
  { id: "overview", label: "Overview", component: Overview },
  { id: "updates", label: "Updates", component: Updates },
  { id: "reaction", label: "Expected vs actual", component: Scorecard },
];

export function EventPage({ id }: { id: string }) {
  const summary = useApi(() => api.eventSummary(id), [id]);
  const story = useApi(() => api.storyline(id), [id]);
  const assessment = useApi(() => api.assessment(id), [id]);
  const prices = useApi(() => api.prices(id), [id]);
  const [tab, setTab] = useState(TABS[0].id);
  const company = summary.data, card = company?.events[0], s = story.data, a = assessment.data;
  const country = company ? COUNTRY[company.country] : undefined;
  const checks = a ? a.stages.flatMap((st) => st.decisions).filter((d) => ["consistent", "inconsistent", "not_significant"].includes(d.verdict)) : [];
  const measured = checks, hits = checks.filter((d) => d.verdict === "consistent").length;
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
              <p className="lead-small">
                <a href={card.latest_url} target="_blank" rel="noreferrer">{card.latest_headline} ↗</a>
              </p>
              <p className="small muted">
                <span className={`badge-verified ${card.verified ? "yes" : "no"}`}>{card.verified ? "✓ Verified" : "Unverified signal"}</span>{" "}
                Prices: daily closes{prices.data?.points.length ? ` to ${date(prices.data.points[prices.data.points.length - 1].day)}` : ""} · news checked every hour
              </p>
            </header>
            <div className="kpis">
              <Fact label={<Term id="move">Stock vs {company.index_name}</Term>}
                    value={card.stock_move != null ? pct(card.stock_move) : card.move_so_far != null ? pct(card.move_so_far) : "–"}
                    tone={card.stock_move_unusual ? (card.stock_move! < 0 ? "bad" : "good") : undefined}
                    sub={card.stock_move == null ? (card.move_so_far != null
                      ? <><MoveBar value={card.move_so_far} unusual={false} /><div>so far, to {date(card.so_far_through!)} close · <Term id="provisional">provisional</Term></div></>
                      : NO_MOVE[card.stock_move_status])
                      : <><MoveBar value={card.stock_move} unusual={card.stock_move_unusual} />
                          <div>{vsWords(card.stock_move, company.index_name)} · {card.stock_move_period}</div>
                          <Term id="unusual">{card.stock_move_unusual ? "⚠ unusual move" : "normal range"}</Term></>} />
              <Fact label={<Term id="volume" />} value={card.volume_ratio == null ? "–" : `${card.volume_ratio.toFixed(1)}×`}
                    sub={card.volume_ratio == null ? "not measured yet"
                      : <><RatioBar value={card.volume_ratio} /><div>{card.volume_ratio >= 2 ? "far above" : "close to"} a normal day (1×)</div></>} />
              <Fact label={<Term id="confidence">News confidence</Term>} value={`${Math.round(card.confidence * 100)}%`}
                    tone={confidenceTone(card.confidence)}
                    sub={<><Meter value={card.confidence} tone={confidenceTone(card.confidence)} />
                          <div><Dots n={card.sources} /> {card.sources} {card.sources === 1 ? "source" : "independent sources"}</div></>} />
              <Fact label={<Term id="expected">Reactions as expected</Term>}
                    value={measured.length ? `${hits} of ${measured.length}` : "–"}
                    sub={measured.length ? <><Meter value={hits / measured.length} tone={hits / measured.length >= 0.6 ? "good" : "warn"} />
                          <div>measured market reactions that matched</div></> : "none measured yet"} />
            </div>
            <Tabs tabs={TABS} active={tab} onChange={setTab} />
            <Body company={company} card={card} story={s} assessment={a} prices={prices.data ?? null} />
          </>
        )}
      </State>
    </>
  );
}
