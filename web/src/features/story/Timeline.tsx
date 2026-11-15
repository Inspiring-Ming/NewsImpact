// Each event: what was reported and by whom (step 1), how it fits the story (step 2),
// what we predicted people would do (step 3) and what really happened (step 4).
import { date, describe, DIRECTION, humanize, label, RESULT, SOURCES } from "../../shared/labels";
import { useNames } from "../../shared/names";
import { StepBadge } from "../../shared/steps";
import { Pill } from "../../shared/ui";
import type { StoryData } from "./context";

export function Timeline({ story, assessment }: StoryData) {
  const { title, outlet } = useNames();
  const quote = new Map(story.events.map((e) => [e.stage, e.summary]));
  return (
    <ol className="timeline">
      {assessment.stages.map((st, i) => {
        const src = SOURCES[st.claim.status];
        return (
          <li key={`${st.stage}-${st.published_at}`} className="stage">
            <div className="stage-num">{i + 1}</div>
            <div className="stage-body">
              <div className="stage-head">
                <b>{title(st.stage_name)}</b>
                <span className="muted">{date(st.published_at)}</span>
                {st.overlaps_previous && <span className="muted small">· same week as the event before</span>}
              </div>
              {quote.get(st.stage) && <blockquote>{quote.get(st.stage)}</blockquote>}
              <div className="stage-row">
                <StepBadge id="monitor" withName={false} />
                <span className="small">Reported by {st.claim.outlets.map(outlet).join(", ")}
                  {st.claim.authoritative && " · confirmed by the company or a filing"}</span>
                {src && <Pill tone={src.tone}>{src.text}</Pill>}
              </div>
              {st.decisions.length > 0 && (
                <table className="reactions">
                  <thead>
                    <tr>
                      <th><StepBadge id="anticipate" withName={false} /> Predicted reaction</th>
                      <th><StepBadge id="verify" withName={false} /> What happened</th>
                    </tr>
                  </thead>
                  <tbody>
                    {st.decisions.map((d) => {
                      const r = RESULT[d.verdict] ?? { text: humanize(d.verdict), tone: "neutral" as const };
                      return (
                        <tr key={d.actor + d.decision}>
                          <td>
                            <b>{label(d.actor)}</b> {d.decision}
                            {d.channel && <div className="muted small">so {label(d.channel)} should {DIRECTION[d.expected] ?? d.expected}</div>}
                          </td>
                          <td>
                            <Pill tone={r.tone}>{r.text}</Pill>
                            {d.evidence && <div className="small">{describe(d.evidence)}</div>}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
