// Each update in the order it was reported, with how many sources reported it.
import { date } from "../../shared/labels";
import { useNames } from "../../shared/names";
import { Pill } from "../../shared/ui";
import type { EventData } from "./context";

export function Updates({ story, assessment }: EventData) {
  const { title, source } = useNames();
  // Titles are joined to the body with ". " for sentence splitting; drop that extra stop.
  const quote = new Map(story.events.map((e) => [e.stage, e.summary.replace("?.", "?").replace("!.", "!")]));
  return (
    <ol className="timeline">
      {assessment.stages.map((st, i) => (
        <li key={`${st.stage}-${st.published_at}`} className="stage">
          <div className="stage-num">{i + 1}</div>
          <div className="stage-body">
            <div className="stage-head">
              <b>{title(st.stage_name)}</b>
              <span className="muted">{date(st.published_at, true)}</span>
              <Pill tone={st.claim.confidence >= 0.9 ? "good" : "warn"}>
                {st.claim.outlets.length} {st.claim.outlets.length === 1 ? "source" : "sources"} · {Math.round(st.claim.confidence * 100)}% confidence
              </Pill>
              {st.claim.authoritative && <Pill tone="good">Company or official filing</Pill>}
            </div>
            {quote.get(st.stage) && <blockquote>{quote.get(st.stage)}</blockquote>}
            <p className="small muted">
              {st.claim.outlets.map(source).join(", ")}
              {st.overlaps_previous && " · same week as the update before, so measured together"}
            </p>
          </div>
        </li>
      ))}
    </ol>
  );
}
