// Tab 3 - does each kind of news really move the stock? For each case (e.g. the company is the
// buyer or the target), what research expects, what our events did, and what chance alone gives.
import { CHANCE_WORDS, EXPECT, pct, verdictText } from "../../shared/labels";
import { Flow, setting, type MethodData } from "./MethodPage";

const measured = (t: MethodData["types"][number]) => t.cases.reduce((n, c) => n + c.n, 0);

export function VerifyStep({ method, types }: MethodData) {
  const min = setting(method, "validation", "min_events_for_calibration") ?? 20;
  return (
    <section className="step-block">
      <h2>Does this news move the stock?</h2>
      <Flow steps={[
        { title: "Expect", text: "Published research says how each kind of news usually moves a share price. It depends on the case: a takeover target's shares jump, the buyer's barely move." },
        { title: "Measure", text: "For each event: the stock's move minus its market's move (S&P 500 or ASX 200) over the event days. 'Unusual' = larger than on 19 of 20 normal days for that stock." },
        { title: "Compare with chance", text: <>A rise or fall happens half the time by chance, an unusual move 1 time in 20. We say research is matched or contradicted only after {min} events, and only when the result beats chance in a statistical test.</> },
      ]} />
      <div className="type-grid wide">
        {types.map((t) => (
          <article key={t.theme} className="type-card">
            <header>
              <h3>{t.title}</h3>
              <span className="muted small">{measured(t)} event{measured(t) === 1 ? "" : "s"} measured</span>
            </header>
            <ul className="case-list">
              {t.cases.map((c) => {
                const e = EXPECT[c.expected], v = verdictText(c, min);
                return (
                  <li key={c.label} className="case">
                    <div className="case-head">
                      <b>{c.label[0].toUpperCase() + c.label.slice(1)}</b>
                      <span className={`expect ${e.tone}`}>{e.text}</span>
                    </div>
                    <p className="small muted">{c.finding} <i>{c.source}</i></p>
                    {c.n > 0 ? (
                      <div className="case-result">
                        {c.average != null && <p className="small">Average move <b>{pct(c.average)}</b></p>}
                        <p className="small"><b>{c.met} of {c.n}</b> {e.did} · by chance alone: {CHANCE_WORDS[c.expected]}</p>
                        <span className={`verdict ${v.tone}`}>{v.text}</span>
                      </div>
                    ) : <p className="small muted">No measured event in this case yet.</p>}
                  </li>
                );
              })}
            </ul>
            {t.no_expectation > 0 && <p className="small muted">{t.no_expectation} event{t.no_expectation > 1 ? "s" : ""} without an expectation.</p>}
          </article>
        ))}
      </div>
    </section>
  );
}
