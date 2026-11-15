// What happened: each event in order, the headline, and which outlets reported it.
import { date } from "../../shared/labels";
import { useNames } from "../../shared/names";
import { Pill } from "../../shared/ui";
import type { StoryData } from "./context";

const CLAIM = {
  confirmed: { text: "Confirmed", tone: "good" },
  corroborated: { text: "Two outlets agree", tone: "ok" },
  single_source: { text: "One outlet so far", tone: "warn" },
} as const;

export function Timeline({ story, assessment }: StoryData) {
  const { title, outlet } = useNames();
  const quote = new Map(story.events.map((e) => [e.stage, e.summary]));
  return (
    <ol className="timeline">
      {assessment.stages.map((st, i) => {
        const c = CLAIM[st.claim.status as keyof typeof CLAIM];
        return (
          <li key={`${st.stage}-${st.published_at}`} className="stage">
            <div className="stage-num">{i + 1}</div>
            <div className="stage-body">
              <div className="stage-head">
                <b>{title(st.stage_name)}</b>
                <span className="muted">{date(st.published_at, true)}</span>
                {c && <Pill tone={c.tone}>{c.text}</Pill>}
              </div>
              {quote.get(st.stage) && <blockquote>{quote.get(st.stage)}</blockquote>}
              <p className="small muted">
                Reported by {st.claim.outlets.map(outlet).join(", ")}
                {st.claim.authoritative && " · confirmed by the company or an official filing"}
                {st.overlaps_previous && " · in the same week as the event before"}
              </p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
