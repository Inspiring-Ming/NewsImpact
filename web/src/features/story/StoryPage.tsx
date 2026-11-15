// One story, read top to bottom. The page is a list of sections: to show
// something new (e.g. analyst revisions), add one entry to SECTIONS.
import type { ComponentType } from "react";
import { api } from "../../api/client";
import { label, STATUS_TONE } from "../../shared/labels";
import { Pill, Section, State } from "../../shared/ui";
import { useApi } from "../../shared/useApi";
import type { StoryData } from "./context";
import { EvidenceDetails } from "./EvidenceDetails";
import { InShort } from "./InShort";
import { PriceReaction } from "./PriceReaction";
import { Timeline } from "./Timeline";

const SECTIONS: { title: string; hint?: string; component: ComponentType<StoryData> }[] = [
  { title: "In short", component: InShort },
  { title: "What the market did", hint: "Share price vs. its market. A gap after a marker is the reaction to that stage.", component: PriceReaction },
  { title: "How the story unfolded", hint: "Each stage, who reported it, and whether people acted as typically expected.", component: Timeline },
  { title: "Details", component: EvidenceDetails },
];

export function StoryPage({ id }: { id: string }) {
  const story = useApi(() => api.storyline(id), [id]);
  const assessment = useApi(() => api.assessment(id), [id]);
  const prices = useApi(() => api.prices(id), [id]);
  const s = story.data, a = assessment.data;
  return (
    <>
      <a className="back" href="#/">← All stories</a>
      <State error={story.error ?? assessment.error} loading={!s || !a}>
        {s && a && (
          <>
            <header className="story-head">
              <h1>{s.entity_name}</h1>
              <div className="story-head-meta">
                <span className="muted">{s.ticker} · {label(s.theme)}</span>
                <Pill tone={STATUS_TONE[s.status]}>{label(s.status)}</Pill>
              </div>
            </header>
            {SECTIONS.map(({ title, hint, component: Body }) => (
              <Section key={title} title={title} hint={hint}>
                <Body story={s} assessment={a} prices={prices.data ?? null} />
              </Section>
            ))}
          </>
        )}
      </State>
    </>
  );
}
