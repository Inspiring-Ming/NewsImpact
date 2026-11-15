// One story, read top to bottom in the product's own four steps. The page is a
// list of sections: to show something new, add one entry to SECTIONS.
import type { ComponentType } from "react";
import { api } from "../../api/client";
import { STATUS } from "../../shared/labels";
import { useNames } from "../../shared/names";
import { StepTitle, type StepId } from "../../shared/steps";
import { Pill, State } from "../../shared/ui";
import { useApi } from "../../shared/useApi";
import type { StoryData } from "./context";
import { EvidenceDetails } from "./EvidenceDetails";
import { PriceReaction } from "./PriceReaction";
import { Summary } from "./Summary";
import { Timeline } from "./Timeline";

const SECTIONS: { title: string; step?: StepId; hint?: string; component: ComponentType<StoryData> }[] = [
  { title: "Conclusion", component: Summary },
  { title: "How the story unfolded", step: "connect", hint: "Each event, who reported it, what we predicted and what happened.", component: Timeline },
  { title: "What the share price did", step: "verify", hint: "The company's share price against its whole market. Numbers mark the events above.", component: PriceReaction },
  { title: "Statistics and sources", hint: "For analysts: the exact measurements and how this result can be reproduced.", component: EvidenceDetails },
];

export function StoryPage({ id }: { id: string }) {
  const story = useApi(() => api.storyline(id), [id]);
  const assessment = useApi(() => api.assessment(id), [id]);
  const prices = useApi(() => api.prices(id), [id]);
  const s = story.data, a = assessment.data;
  const status = s ? STATUS[s.status] : undefined;
  const { title } = useNames();
  return (
    <>
      <a className="back" href="#/">← All stories</a>
      <State error={story.error ?? assessment.error} loading={!s || !a}>
        {s && a && (
          <>
            <header className="story-head">
              <h1>{s.entity_name}</h1>
              <div className="story-head-meta">
                <span className="muted">{s.ticker} · {title(s.theme)}</span>
                {status && <Pill tone={status.tone}>{status.text}</Pill>}
              </div>
            </header>
            {SECTIONS.map(({ title, step, hint, component: Body }) => (
              <section key={title} className="section">
                {step ? <StepTitle id={step} title={title} hint={hint} /> : (
                  <div className="section-head"><h2>{title}</h2>{hint && <p className="muted">{hint}</p>}</div>
                )}
                <Body story={s} assessment={a} prices={prices.data ?? null} />
              </section>
            ))}
          </>
        )}
      </State>
    </>
  );
}
