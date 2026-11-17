// Tab 3 - does each kind of news move the stock as research says? A forest plot: for each case,
// the share of our events that moved as expected (dot), its 95% range (whisker), and what chance
// alone would give (tick). A verdict only from enough events.
import { CHANCE_WORDS, EXPECT, pct, verdictText } from "../../shared/labels";
import { Term } from "../../shared/Term";
import { Flow, Head, setting, type MethodData } from "./MethodPage";

/** 95% Wilson interval for k of n: the range the true share plausibly lies in. */
function wilson(k: number, n: number, z = 1.96): [number, number] {
  const p = k / n, d = 1 + (z * z) / n;
  const mid = (p + (z * z) / (2 * n)) / d, half = (z * Math.sqrt((p * (1 - p)) / n + (z * z) / (4 * n * n))) / d;
  return [Math.max(0, mid - half), Math.min(1, mid + half)];
}
const at = (x: number) => `${x * 100}%`;
const GLYPH: Record<string, string> = { up: "↑", down: "↓", flat: "→", uncertain: "↕" };

export function VerifyStep({ method, types }: MethodData) {
  const min = setting(method, "validation", "min_events_for_calibration") ?? 20;
  return (
    <section className="hiw">
      <Head kicker="Step 3 · Market" title="Does this news move the stock as research says?"
            dek={<>Each row is one case. The dot is the share of our events that moved as expected; the tick is what chance alone gives. We judge only after {min} events.</>} />
      <Flow steps={[
        { title: "Expect", line: "from published research", tip: "Research says how each kind of news usually moves a share price, case by case: a takeover target's shares jump, the buyer's barely move." },
        { title: "Measure", line: "stock minus its market", tip: "The stock's move minus its market's (S&P 500 or ASX 200) over the event days. 'Unusual' = larger than on 19 of 20 normal days for that stock." },
        { title: "Beat chance", line: "binomial test", tip: `A rise or fall happens 1 time in 2 by chance, an unusual move 1 in 20, no unusual move 19 in 20. A verdict needs ${min} events and a result that beats chance (z ≥ 1.96).` },
      ]} />
      <div className="forest" role="table" aria-label="Share of events that moved as research expects, by case">
        <div className="fp-axis" aria-hidden="true">
          <span />
          <div className="fp-track">{[0, 0.25, 0.5, 0.75, 1].map((x) => <i key={x} style={{ left: at(x) }}>{Math.round(x * 100)}%</i>)}</div>
          <span />
        </div>
        {types.map((t) => (
          <div key={t.theme} className="fp-group" role="rowgroup">
            <div className="fp-group-name">{t.title}</div>
            {t.cases.map((c) => {
              const e = EXPECT[c.expected], v = verdictText(c, min);
              const share = c.n ? c.met / c.n : null, [lo, hi] = c.n ? wilson(c.met, c.n) : [0, 0];
              return (
                <div key={c.label} className="fp-row" role="row">
                  <div className="fp-case" role="cell">
                    <span className={`fp-glyph ${e.tone}`} aria-label={e.text}>{GLYPH[c.expected]}</span>
                    <Term tip={`${c.finding} — ${c.source}`}><span>{c.label[0].toUpperCase() + c.label.slice(1)}</span></Term>
                  </div>
                  <Term tip={c.n ? `${c.met} of ${c.n} ${e.did} (expected: ${e.text.slice(2)}). Chance alone: ${CHANCE_WORDS[c.expected]}. 95% range ${Math.round(lo * 100)}–${Math.round(hi * 100)}%.${c.average != null ? ` Average move ${pct(c.average)}.` : ""}` : "No measured event in this case yet."}>
                    <div className="fp-track" role="cell">
                      {[0.25, 0.5, 0.75].map((x) => <span key={x} className="fp-grid" style={{ left: at(x) }} />)}
                      <span className="fp-chance" style={{ left: at(c.chance) }} />
                      {share != null && <>
                        <span className={`fp-whisker ${v.tone}`} style={{ left: at(lo), width: at(hi - lo) }} />
                        <span className={`fp-dot ${v.tone}`} style={{ left: at(share), width: 6 + Math.min(c.n, 20) * 0.5, height: 6 + Math.min(c.n, 20) * 0.5 }} />
                      </>}
                    </div>
                  </Term>
                  <div className="fp-value" role="cell">
                    {c.n ? <><b>{c.met}/{c.n}</b><small className={v.tone}>{c.verdict === "too_few" ? `${c.n} of ${min}` : v.text}</small></> : <small>no event yet</small>}
                  </div>
                </div>
              );
            })}
          </div>
        ))}
      </div>
      <p className="hiw-legend"><span className="fp-dot static" /> our share (bigger = more events) <span className="fp-whisker static" /> 95% range
        <span className="fp-chance static" /> chance alone <span className="sep" /> ↑ rises ↓ falls → little change ↕ larger move than usual</p>
    </section>
  );
}
