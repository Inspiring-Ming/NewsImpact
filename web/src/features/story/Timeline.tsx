// Stage by stage: what was reported, who confirmed it, what people were expected to do, what happened.
import { CLAIM, date, describe, EXPECTED, humanize, label, VERDICT } from "../../shared/labels";
import { Pill } from "../../shared/ui";
import type { StoryData } from "./context";

export function Timeline({ story, assessment }: StoryData) {
  const quote = new Map(story.events.map((e) => [e.stage, e.summary]));
  return (
    <ol className="timeline">
      {assessment.stages.map((st, i) => {
        const claim = CLAIM[st.claim.status];
        return (
          <li key={`${st.stage}-${st.published_at}`} className="stage">
            <div className="stage-num">{i + 1}</div>
            <div className="stage-body">
              <div className="stage-head">
                <b>{label(st.stage_name)}</b>
                <span className="muted">{date(st.published_at)}</span>
                {claim && <Pill tone={claim.tone}>{claim.text}</Pill>}
                {st.overlaps_previous && <Pill tone="neutral">Same week as the previous stage</Pill>}
              </div>
              {quote.get(st.stage) && <blockquote>{quote.get(st.stage)}</blockquote>}
              <p className="small muted">
                Reported by {st.claim.outlets.join(", ")}
                {st.claim.origins.length !== st.claim.outlets.length && ` · ${st.claim.origins.length} independent source(s)`}
                {st.claim.authoritative && " · confirmed by the company or a filing"}
              </p>
              {st.decisions.length > 0 && (
                <ul className="expectations">
                  {st.decisions.map((d) => {
                    const v = VERDICT[d.verdict] ?? { text: humanize(d.verdict), tone: "neutral" as const };
                    return (
                      <li key={d.actor + d.decision}>
                        <div>
                          <b>{humanize(d.actor)}</b> {d.decision}
                          {d.channel && <span className="muted"> → expect {label(d.channel).toLowerCase()} to {EXPECTED[d.expected] ?? d.expected}</span>}
                        </div>
                        <div className="expectation-result">
                          {d.evidence && <span className="small">{describe(d.evidence)}</span>}
                          <Pill tone={v.tone}>{v.text}</Pill>
                        </div>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
