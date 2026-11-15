// All storylines, filterable by market and status.
import { useState } from "react";
import { api } from "../api/client";
import { Badge, day, Loading, Page } from "../components/ui";
import { useApi } from "../components/useApi";

const marketOf = (ticker: string) => (ticker.endsWith(".AX") ? "ASX" : "US");

export function Storylines() {
  const { data, error, loading } = useApi(api.storylines);
  const [market, setMarket] = useState("all");
  const [status, setStatus] = useState("all");
  const rows = (data ?? []).filter(
    (s) => (market === "all" || marketOf(s.ticker) === market) && (status === "all" || s.status === status),
  );
  return (
    <Page title="Storylines" intro="Chains of related news about one company. Open one to see each stage, the evidence and the conclusion.">
      <div className="filters">
        <label>Market <select value={market} onChange={(e) => setMarket(e.target.value)}>
          <option value="all">All</option><option value="US">US</option><option value="ASX">Australia (ASX)</option>
        </select></label>
        <label>Status <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="all">All</option><option value="developing">Developing</option>
          <option value="escalating">Escalating</option><option value="resolved">Resolved</option>
        </select></label>
      </div>
      <Loading error={error} loading={loading} />
      {data && rows.length === 0 && <p className="muted">No storylines yet. Run a monitoring round (or load the demo) on the Overview page.</p>}
      <div className="list">
        {rows.map((s) => (
          <a key={s.storyline_id} className="row-card" href={`#/storylines/${s.storyline_id}`}>
            <div className="row-main">
              <span className="ticker">{s.ticker}</span>
              <span>{s.entity_name}</span>
              <span className="muted">{s.theme.replace(/_/g, " ")}</span>
            </div>
            <div className="row-meta">
              <span className="muted">{s.events.length} stage(s) · {day(s.opened_at)} → {day(s.updated_at)}</span>
              <Badge value={s.status} />
            </div>
          </a>
        ))}
      </div>
    </Page>
  );
}
