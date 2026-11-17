// Tab 2 - how news becomes an event and when it counts as confirmed, then each event type:
// its possible steps (from research) and how many of our events really reached each one.
import { Flow, setting, type MethodData } from "./MethodPage";

export function ConnectStep({ method, types }: MethodData) {
  const origins = setting(method, "validation", "corroborating_origins") ?? 2;
  const events = types.reduce((n, t) => n + t.events, 0);
  const confirmed = types.reduce((n, t) => n + t.confirmed, 0);
  return (
    <section className="step-block">
      <h2>Which events we detect, and when we call them confirmed</h2>
      <Flow steps={[
        { title: "Read", text: "Every sentence that names one of our companies, in every article from our sources." },
        { title: "Recognise", text: "Its wording is matched to an event type (word lists checked by AI). Opinion pieces, previews and share price comparisons are skipped: they talk about news, they are not news." },
        { title: "Join", text: "News about the same company and event type within the event's time window joins the same event, as its next step." },
        { title: "Confirm", text: <>An event is <b>Confirmed</b> when {origins} or more independent outlets report it (copies of one article count once), or when the company itself or a regulator filing publishes it. Until then it is a lead to check.</> },
      ]} />
      <p className="live-line"><span className="live-dot" /><span>Now: <b>{events}</b> events, <b>{confirmed}</b> confirmed ({events ? Math.round((confirmed / events) * 100) : 0}%). Most of the rest come from one source so far.</span></p>
      <div className="type-grid">
        {types.map((t) => (
          <article key={t.theme} className="type-card">
            <header>
              <h3>{t.title}</h3>
              <span className="muted small"><b>{t.events}</b> events · <b>{t.confirmed}</b> confirmed</span>
            </header>
            <ol className="steps-chain">
              {t.steps.map((s) => (
                <li key={s.title} className={s.reached ? "reached" : ""}>
                  <span>{s.title}</span><b>{s.reached}</b>
                </li>
              ))}
            </ol>
            <p className="small muted">
              {t.steps.length > 1
                ? "Possible steps, from research on how these stories unfold; not every event goes through all of them. The number is how many of our events reached each step."
                : "A single step: each report is its own event."}
              {t.gaps_seen > 0 && t.gap_days != null && <> Steps came a median <b>{t.gap_days.toFixed(1)} days</b> apart ({t.gaps_seen} seen).</>}
            </p>
            <details className="small">
              <summary>News within <b>{t.window_days} days</b> joins the same event — why?</summary>
              <p className="muted">{t.window_why}</p>
            </details>
          </article>
        ))}
      </div>
    </section>
  );
}
