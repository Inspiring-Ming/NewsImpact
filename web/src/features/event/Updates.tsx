// Updates as a timeline: a date axis with every update placed in time, then one card per
// update with its tone, sources, confidence and the stock's reaction that day.
import { date, moveVs, tone } from "../../shared/labels";
import { useNames } from "../../shared/names";
import { confidenceTone, Dots, Meter, MoveBar } from "../../shared/viz";
import type { EventData } from "./context";

const DAY = 86_400_000;

export function Updates({ story, assessment, company }: EventData) {
  const { title, source } = useNames();
  const byStage = new Map(story.events.map((e) => [`${e.stage}|${e.published_at}`, e]));
  const stages = assessment.stages;
  const t0 = Date.parse(stages[0].published_at), t1 = Date.parse(stages[stages.length - 1].published_at);
  const span = Math.max(t1 - t0, DAY);
  return (
    <>
      <div className="card axis-card">
        <div className="time-axis">
          {stages.map((st, i) => (
            <span key={i} className="axis-node" style={{ left: `${((Date.parse(st.published_at) - t0) / span) * 100}%` }}
                  title={title(st.stage_name)}>{i + 1}</span>
          ))}
        </div>
        <div className="axis-ends muted small"><span>{date(stages[0].published_at, true)}</span><span>{date(stages[stages.length - 1].published_at, true)}</span></div>
      </div>
      <ol className="timeline">
        {stages.map((st, i) => {
          const ev = byStage.get(`${st.stage}|${st.published_at}`) ?? story.events.find((e) => e.stage === st.stage);
          const t = tone(ev?.tone ?? 0);
          const price = st.decisions.find((d) => d.channel === "price")?.evidence;
          const gap = i > 0 ? Math.round((Date.parse(st.published_at) - Date.parse(stages[i - 1].published_at)) / DAY) : null;
          return (
            <li key={`${st.stage}-${st.published_at}`} className="stage">
              {gap != null && <div className="gap muted small">{gap === 0 ? "same day" : `${gap} day${gap > 1 ? "s" : ""} later`}</div>}
              <div className={`stage-num ${t.tone}`}>{i + 1}</div>
              <div className="stage-body">
                <div className="stage-head">
                  <b>{title(st.stage_name)}</b>
                  <span className="muted">{date(st.published_at, true)}</span>
                  <span className={`tone-chip ${t.tone}`}>{t.text}</span>
                  {ev?.is_rumour && <span className="tone-chip warn">Rumour</span>}
                  {st.claim.authoritative && <span className="tone-chip good">Company or official filing</span>}
                </div>
                {ev && <blockquote>{ev.summary.replace("?.", "?").replace("!.", "!")}</blockquote>}
                <div className="stage-facts">
                  <span><Dots n={st.claim.outlets.length} /> {st.claim.outlets.map(source).join(", ")}</span>
                  <span className="conf"><Meter value={st.claim.confidence} tone={confidenceTone(st.claim.confidence)} /> {Math.round(st.claim.confidence * 100)}% confidence</span>
                  {price && <span className="conf"><MoveBar value={price.value} unusual={price.significant} /> stock {moveVs(price.value, company.index_name)}</span>}
                </div>
                {st.overlaps_previous && <p className="small muted">Within a few trading days of the update before, so their stock reactions are also measured together.</p>}
              </div>
            </li>
          );
        })}
      </ol>
    </>
  );
}
