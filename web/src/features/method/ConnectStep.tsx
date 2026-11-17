// Tab 2 - from a sentence to a confirmed event. A funnel from articles read to confirmed
// events (live counts), then each event type as a line with its possible steps as stations:
// filled when our events reached them, with the count.
import { api } from "../../api/client";
import { Term } from "../../shared/Term";
import { useApi } from "../../shared/useApi";
import { Flow, Head, setting, type MethodData } from "./MethodPage";

const fmt = (n: number) => n.toLocaleString("en-US");

export function ConnectStep({ method, types }: MethodData) {
  const overview = useApi(api.overview);
  const coverage = useApi(api.coverage);
  const origins = setting(method, "validation", "corroborating_origins") ?? 2;
  const research = new Map(method.playbooks.map((p) => [p.theme, p.research[0]]));
  const events = types.reduce((n, t) => n + t.events, 0);
  const confirmed = types.reduce((n, t) => n + t.confirmed, 0);
  const outlets = coverage.data ?? [];
  const naming = outlets.reduce((n, c) => n + Math.round(c.articles * c.with_company), 0);
  const used = outlets.reduce((n, c) => n + Math.round(c.articles * c.in_stories), 0);
  const funnel = [
    { label: "articles read", what: "everything our sources published", n: overview.data?.articles ?? 0 },
    { label: "name one of our companies", what: "a sentence names one of our companies (names matched exactly)", n: naming },
    { label: "report an event", what: "that sentence reports something that moves share prices: not opinion, a preview or old news", n: used },
    { label: "events", what: `articles about the same company and story are joined: ${fmt(used)} articles make ${fmt(events)} events`, n: events },
    { label: "confirmed events", what: `${origins}+ independent outlets, or the company or a regulator filing itself, reported it`, n: confirmed },
  ];
  const top = Math.max(1, funnel[0].n);
  return (
    <section className="hiw">
      <Head kicker="Step 2 · Events" title="From a sentence to a confirmed event"
            dek="Most news is not an event. Live counts of what passes each step." />
      <ol className="funnel">
        {funnel.map((f, i) => (
          <li key={f.label} className={i === funnel.length - 1 ? "last" : ""}>
            <i style={{ width: `${Math.max(2, Math.sqrt(f.n / top) * 100)}%` }} aria-hidden="true" />
            <span className="funnel-n">{fmt(f.n)}</span>
            <span className="funnel-text"><b>{f.label}</b><small>{f.what}</small></span>
          </li>
        ))}
      </ol>
      <Flow steps={[
        { title: "Read", line: "sentence by sentence", tip: "Every sentence that names one of our companies, in every article from our sources." },
        { title: "Recognise", line: "an event type", tip: "Its wording is matched to an event type (word lists, checked by AI). Opinion pieces, previews and share price comparisons are skipped." },
        { title: "Join", line: "same company, same story", tip: "News about the same company and event type within the event's time window joins the same event, as its next step." },
        { title: "Confirm", line: `${origins}+ outlets or official`, tip: `Confirmed when ${origins} or more independent outlets report it (copies count once), or the company itself or a regulator filing publishes it.` },
      ]} />
      <h3 className="hiw-sub">{types.length} kinds of event, and how far our events went</h3>
      <div className="line-row line-head" aria-hidden="true">
        <span>Kind of event · research</span><span>Possible steps · how many of our events reached each</span><span>Our events</span>
      </div>
      <div className="lines">
        {types.map((t) => {
          const why = research.get(t.theme);
          return (
            <div key={t.theme} className="line-row">
              <div className="line-name">
                <b>{t.title}</b>
                {why && <Term tip={`${why.finding} — ${why.source}`}><small className="cite">{why.source.match(/^.*?\(\d{4}\)/)?.[0] ?? why.source}</small></Term>}
              </div>
              <ol className="line-track">
                {t.steps.map((s) => (
                  <li key={s.title} className={s.reached ? "on" : ""}>
                    <Term tip={`${s.reached} of our events reached "${s.title}"`}><span className="station">{s.reached}</span></Term>
                    <small>{s.title}</small>
                  </li>
                ))}
              </ol>
              <div className="line-meta">
                <span className="line-big">{t.events}<small> events</small></span>
                <small><span className="good">{t.confirmed} confirmed</span></small>
                <Term tip={t.window_why}><small>joins within {t.window_days} d</small></Term>
              </div>
            </div>
          );
        })}
      </div>
      <p className="hiw-legend"><span className="station mini on" /> reached by at least one event <span className="station mini" /> not yet
        <span className="sep" /> point at a research name for its finding</p>
    </section>
  );
}
