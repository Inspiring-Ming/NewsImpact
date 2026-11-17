// Tab 2 - how news becomes an event and when it counts as confirmed, then each event type:
// why we track it (research), its possible steps and how many of our events reached each.
import { Term } from "../../shared/Term";
import { Meter } from "../../shared/viz";
import { Flow, setting, type MethodData } from "./MethodPage";

export function ConnectStep({ method, types }: MethodData) {
  const origins = setting(method, "validation", "corroborating_origins") ?? 2;
  const research = new Map(method.playbooks.map((p) => [p.theme, p.research[0]]));
  const events = types.reduce((n, t) => n + t.events, 0);
  const confirmed = types.reduce((n, t) => n + t.confirmed, 0);
  return (
    <section className="step-block">
      <h2>From a sentence to a confirmed event</h2>
      <Flow steps={[
        { icon: "📰", title: "Read", line: "sentences naming our companies", tip: "Every sentence that names one of our 73 companies, in every article from our sources." },
        { icon: "🏷️", title: "Recognise", line: "match an event type", tip: "Its wording is matched to an event type (word lists, checked by AI). Opinion pieces, previews and share price comparisons are skipped: they talk about news, they are not news." },
        { icon: "🔗", title: "Join", line: "same company, same story", tip: "News about the same company and event type within the event's time window joins the same event, as its next step." },
        { icon: "✅", title: "Confirm", line: `${origins}+ outlets or official`, tip: `Confirmed when ${origins} or more independent outlets report it (copies of one article count once), or the company itself or a regulator filing publishes it. Until then it is a lead to check.` },
      ]} />
      <div className="confirm-meter">
        <span className="live-dot" />
        <b className="big-num">{confirmed}</b><span className="muted">of {events} events confirmed</span>
        <Meter value={events ? confirmed / events : 0} tone="good" />
        <span className="small muted">the rest: one source so far</span>
      </div>
      <p className="dot-legend small"><span className="chain-key">Step <b>3</b></span> = a possible step from research, and how many of our events reached it</p>
      <div className="type-grid">
        {types.map((t) => {
          const why = research.get(t.theme);
          return (
            <article key={t.theme} className="type-card">
              <header>
                <h3>{t.title}</h3>
                <span className="pill">{t.events} events · <b className="good">{t.confirmed} ✓</b></span>
              </header>
              {why && <Term tip={`${why.finding} (${why.source})`}><span className="why-chip">Why we track it · {why.source.match(/^.*?\(\d{4}\)/)?.[0] ?? why.source}</span></Term>}
              <ol className="steps-chain">
                {t.steps.map((s) => (
                  <li key={s.title} className={s.reached ? "reached" : ""}><span>{s.title}</span><b>{s.reached}</b></li>
                ))}
              </ol>
              <div className="chips small">
                <Term tip={t.window_why}><span>⏱ joins within {t.window_days} days</span></Term>
                {t.gaps_seen > 0 && t.gap_days != null && (
                  <Term tip={`Median time between one step and the next in our events (${t.gaps_seen} seen).`}><span>↔ {t.gap_days.toFixed(1)} days between steps</span></Term>
                )}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
