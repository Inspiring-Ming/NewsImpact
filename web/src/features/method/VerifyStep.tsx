// Tab 3 - does each kind of news really move the stock? One row per case: what research expects,
// one dot per measured event (filled = moved as expected), and the verdict against chance.
import { CHANCE_WORDS, EXPECT, pct, verdictText } from "../../shared/labels";
import { Term } from "../../shared/Term";
import { Flow, setting, type MethodData } from "./MethodPage";

const MAX_DOTS = 24;

export function VerifyStep({ method, types }: MethodData) {
  const min = setting(method, "validation", "min_events_for_calibration") ?? 20;
  return (
    <section className="step-block">
      <h2>Does this news move the stock?</h2>
      <Flow steps={[
        { icon: "📚", title: "Expect", line: "what research predicts", tip: "Published research says how each kind of news usually moves a share price. It depends on the case: a takeover target's shares jump, the buyer's barely move." },
        { icon: "📏", title: "Measure", line: "stock minus its market", tip: "For each event: the stock's move minus its market's move (S&P 500 or ASX 200) over the event days. 'Unusual' = larger than on 19 of 20 normal days for that stock." },
        { icon: "🎲", title: "Beat chance", line: `judged after ${min} events`, tip: `A rise or fall happens half the time by chance, an unusual move 1 time in 20. We say research is matched or contradicted only after ${min} events, and only when the result beats chance in a statistical test.` },
      ]} />
      <p className="dot-legend small"><span className="dot on" /> moved as research expects <span className="dot" /> did not</p>
      <div className="type-grid wide">
        {types.map((t) => (
          <article key={t.theme} className="type-card">
            <header><h3>{t.title}</h3></header>
            <ul className="case-list">
              {t.cases.map((c) => {
                const e = EXPECT[c.expected], v = verdictText(c, min);
                return (
                  <li key={c.label} className="case">
                    <Term tip={`${c.finding} (${c.source})`}><span className="case-label">{c.label[0].toUpperCase() + c.label.slice(1)}</span></Term>
                    <span className={`expect ${e.tone}`}>{e.text}</span>
                    {c.n > 0 ? (
                      <>
                        <Term tip={`${c.met} of ${c.n} events ${e.did}; by chance alone ${CHANCE_WORDS[c.expected]} would.${c.average != null ? ` Average move ${pct(c.average)}.` : ""}`}>
                          <span className="dots-row" role="img" aria-label={`${c.met} of ${c.n} as expected`}>
                            {Array.from({ length: Math.min(c.n, MAX_DOTS) }, (_, i) => <span key={i} className={`dot${i < c.met ? " on" : ""}`} />)}
                            <b>{c.met}/{c.n}</b>
                          </span>
                        </Term>
                        <span className={`verdict ${v.tone}`}>{c.verdict === "too_few" ? `${c.n} of ${min} needed` : v.text}</span>
                      </>
                    ) : <span className="small muted">no event yet</span>}
                  </li>
                );
              })}
            </ul>
          </article>
        ))}
      </div>
    </section>
  );
}
