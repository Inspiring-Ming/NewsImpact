// Home: what is being monitored, the latest round, and how the pipeline works.
import { useState } from "react";
import { api } from "../api/client";
import { Card, Loading, Page, Stat } from "../components/ui";
import { useApi } from "../components/useApi";

const STEPS = [
  ["Sources", "Read the curated outlets automatically; mark copies of other outlets' articles."],
  ["Semantics", "Find claims about watched companies: event type, attribution, background vs. news."],
  ["Reliability", "How much to trust each outlet and claim, from its track record."],
  ["Storylines", "Link related news into one story (e.g. misconduct → departure → successor)."],
  ["Impact", "Which companies are affected, directly and through suppliers or rivals."],
  ["Market", "What prices, volume and volatility actually did, on each company's home exchange."],
  ["Validation", "Check every stage against independent evidence, then conclude and suggest."],
];

export function Overview() {
  const overview = useApi(api.overview);
  const monitor = useApi(api.monitor);
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const act = (label: string, run: () => Promise<unknown>) => async () => {
    setBusy(label);
    setMessage(null);
    try {
      await run();
      setMessage(`${label}: done.`);
    } catch (e) {
      setMessage(`${label}: ${(e as Error).message}`);
    } finally {
      setBusy(null);
      overview.reload();
      monitor.reload();
    }
  };

  const o = overview.data;
  const m = monitor.data;
  return (
    <Page
      title="Overview"
      intro="NewsImpact watches a curated set of news outlets, links related news into storylines, and checks what each stage did to the company and its stock."
      actions={
        <>
          {o?.profile === "demo" && (
            <button disabled={!!busy} onClick={act("Load demo data", api.loadDemo)}>Load demo data</button>
          )}
          <button className="primary" disabled={!!busy} onClick={act("Monitoring round", api.runRound)}>
            {busy === "Monitoring round" ? "Running…" : "Run a monitoring round now"}
          </button>
        </>
      }
    >
      {message && <p className="notice">{message}</p>}
      <Loading error={overview.error} loading={overview.loading && !o} />
      {o && (
        <div className="stats">
          <Stat label="outlets monitored" value={o.outlets_enabled} />
          <Stat label="articles stored" value={o.articles} />
          <Stat label="open storylines" value={o.storylines_open} />
          <Stat label="resolved storylines" value={o.storylines_resolved} />
          <Stat label="market data" value={o.market_data} />
          <Stat label="language model" value={o.llm}
                hint={o.llm_spent_this_month != null ? `$${o.llm_spent_this_month.toFixed(2)} this month` : undefined} />
        </div>
      )}
      <div className="grid2">
        <Card title="Monitoring">
          <p>
            {o && o.monitor_every_minutes > 0
              ? `Automatic: every ${o.monitor_every_minutes} minutes.`
              : "On demand (set NI_MONITOR_EVERY_MINUTES to run automatically)."}
          </p>
          <p className="muted">
            Last round: {m?.last_round_at ? new Date(m.last_round_at).toLocaleString() : "not yet"}
            {m?.last_new_articles != null && ` · ${m.last_new_articles} new articles · ${m.last_assessments_updated} assessments updated`}
          </p>
          <p className="muted">Profile: <b>{o?.profile}</b> {o?.profile === "demo" && "(fictional companies and prices)"}</p>
        </Card>
        <Card title="How it works">
          <ol className="steps">
            {STEPS.map(([name, text]) => (<li key={name}><b>{name}</b> — {text}</li>))}
          </ol>
        </Card>
      </div>
    </Page>
  );
}
