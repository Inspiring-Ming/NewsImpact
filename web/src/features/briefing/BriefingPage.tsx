// Home: what NewsImpact does, and every story it is following right now.
import { useState } from "react";
import { api } from "../../api/client";
import { State } from "../../shared/ui";
import { useApi } from "../../shared/useApi";
import { HowItWorks } from "./HowItWorks";
import { StoryCard } from "./StoryCard";

const MARKETS = ["All", "US", "ASX"] as const;

export function BriefingPage({ refreshKey }: { refreshKey: number }) {
  const { data, error, loading } = useApi(api.briefing, [refreshKey]);
  const [market, setMarket] = useState<(typeof MARKETS)[number]>("All");
  const cards = (data ?? []).filter((c) => market === "All" || c.market === market);
  return (
    <>
      <section className="hero">
        <h1>From headlines to market evidence</h1>
        <p className="lead">
          NewsImpact follows how news about a company unfolds, which decisions it triggers,
          and whether the market actually reacted, with every conclusion backed by evidence.
        </p>
        <HowItWorks />
      </section>

      <div className="list-head">
        <h2>Stories we are following</h2>
        <div className="segmented" role="group" aria-label="Market">
          {MARKETS.map((m) => (
            <button key={m} className={m === market ? "active" : ""} onClick={() => setMarket(m)}>
              {m === "ASX" ? "Australia" : m}
            </button>
          ))}
        </div>
      </div>
      <State error={error} loading={loading && !data}
             empty={data && cards.length === 0 && (
               <p>No stories yet. Use <b>Update now</b> (or <b>Load demo</b>) at the top to collect the latest news.</p>
             )}>
        <div className="cards">{cards.map((c) => <StoryCard key={c.storyline_id} item={c} />)}</div>
      </State>
    </>
  );
}
