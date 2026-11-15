// One story, as plain questions answered in order. The page is a list of sections:
// to show something new, add one entry to SECTIONS.
import type { ComponentType } from "react";
import { api } from "../../api/client";
import { COUNTRY } from "../../shared/labels";
import { State } from "../../shared/ui";
import { useApi } from "../../shared/useApi";
import type { StoryData } from "./context";
import { EvidenceDetails } from "./EvidenceDetails";
import { InShort } from "./InShort";
import { PriceReaction } from "./PriceReaction";
import { Reactions } from "./Reactions";
import { Timeline } from "./Timeline";

const SECTIONS: { title: string; hint: (d: StoryData) => string; component: ComponentType<StoryData> }[] = [
  { title: "In short", hint: () => "The answers that matter, with the evidence behind them below.", component: InShort },
  { title: "What happened", hint: () => "Each event in the order it was reported, and which news outlets reported it.", component: Timeline },
  { title: "How the stock reacted", hint: (d) => `The share price compared with the ${d.company.benchmark_name}. If the stock falls further than the index, the news - not the whole market - is the likely cause.`, component: PriceReaction },
  { title: "Who was expected to react - and did they?", hint: () => "For each event, the reactions that usually follow, checked against market data.", component: Reactions },
  { title: "For analysts", hint: () => "Exact measurements and how this result can be reproduced.", component: EvidenceDetails },
];

export function StoryPage({ id }: { id: string }) {
  const summary = useApi(() => api.storySummary(id), [id]);
  const story = useApi(() => api.storyline(id), [id]);
  const assessment = useApi(() => api.assessment(id), [id]);
  const prices = useApi(() => api.prices(id), [id]);
  const company = summary.data, card = company?.stories[0], s = story.data, a = assessment.data;
  const country = company ? COUNTRY[company.country] : undefined;
  return (
    <>
      <a className="back" href="#/">← All companies</a>
      <State error={summary.error ?? story.error ?? assessment.error} loading={!company || !card || !s || !a}>
        {company && card && s && a && (
          <>
            <header className="story-head">
              <span className="tag">{card.story_type}</span>
              <h1>{company.name}</h1>
              <div className="muted">{country?.flag} {country?.name ?? company.country} · {company.ticker}</div>
            </header>
            {SECTIONS.map(({ title, hint, component: Body }) => {
              const data: StoryData = { company, card, story: s, assessment: a, prices: prices.data ?? null };
              return (
                <section key={title} className="section">
                  <div className="section-head"><h2>{title}</h2><p className="muted">{hint(data)}</p></div>
                  <Body {...data} />
                </section>
              );
            })}
          </>
        )}
      </State>
    </>
  );
}
