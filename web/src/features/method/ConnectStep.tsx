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
    { label: "Articles read", n: overview.data?.articles ?? 0, tip: "Every article our sources published since we started reading." },
    { label: "Name one of our companies", n: naming, tip: "Articles with a sentence naming one of our 73 companies (names matched exactly)." },
    { label: "Became an event update", n: used, tip: "Articles with a sentence recognised as a kind of event that moves share prices: not opinion, previews or old news." },
    { label: "Events", n: events, tip: "Updates about the same company and story joined into one event." },
    { label: "Confirmed", n: confirmed, tip: `${origins} or more independent outlets, or the company or a regulator filing itself. The rest are leads with one source so far.` },
  ];
  const top = Math.max(1, funnel[0].n);
  return (
    <section className="hiw">
      <Head kicker="Step 2 · Events" title="From a sentence to a confirmed event"
            dek="Most news is not an event. Live counts of what passes each step." />
      <div className="funnel">
        {funnel.map((f, i) => (
          <Term key={f.label} tip={f.tip}>
            <div className={`funnel-row${i === funnel.length - 1 ? " last" : ""}`}>
              <span className="funnel-n">{fmt(f.n)}</span>
              <span className="funnel-bar"><i style={{ width: `${Math.max(1.5, Math.sqrt(f.n / top) * 100)}%` }} /></span>
              <span className="funnel-label">{f.label}</span>
            </div>
          </Term>
        ))}
      </div>
      <Flow steps={[
        { title: "Read", line: "sentence by sentence", tip: "Every sentence that names one of our companies, in every article from our sources." },
        { title: "Recognise", line: "an event type", tip: "Its wording is matched to an event type (word lists, checked by AI). Opinion pieces, previews and share price comparisons are skipped." },
        { title: "Join", line: "same company, same story", tip: "News about the same company and event type within the event's time window joins the same event, as its next step." },
        { title: "Confirm", line: `${origins}+ outlets or official`, tip: `Confirmed when ${origins} or more independent outlets report it (copies count once), or the company itself or a regulator filing publishes it.` },
      ]} />
      <h3 className="hiw-sub">{types.length} kinds of event, and how far our events went</h3>
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
                <span className="line-big">{t.events}</span>
                <small><span className="good">{t.confirmed} confirmed</span></small>
                <Term tip={t.window_why}><small>joins within {t.window_days} d</small></Term>
              </div>
            </div>
          );
        })}
      </div>
      <p className="hiw-legend"><span className="station mini on" /> a possible step from research, with how many of our events reached it
        <span className="sep" /> hover a source year for the finding</p>
    </section>
  );
}
