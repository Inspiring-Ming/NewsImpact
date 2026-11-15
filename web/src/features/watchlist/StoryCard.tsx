// A company with a developing story: the news, the story so far, and four plain answers.
import type { S } from "../../api/client";
import { CONFIRMED_TONE, COUNTRY, date, EVIDENCE, STATUS_TONE } from "../../shared/labels";
import { Pill } from "../../shared/ui";

export function StoryCard({ company, story }: { company: S["CompanyCard"]; story: S["StoryCard"] }) {
  const country = COUNTRY[company.country];
  const ev = EVIDENCE[story.evidence];
  const moved = story.reaction?.significant;
  return (
    <a className="story-card" href={`#/story/${story.storyline_id}`}>
      <div className="story-card-top">
        <div>
          <div className="company">{company.name}</div>
          <div className="muted small">{country?.flag} {country?.name ?? company.country} · {company.ticker}</div>
        </div>
        <span className="tag">{story.story_type}</span>
      </div>

      <p className="headline">“{story.latest_headline}”</p>

      <div>
        <div className="answer-label">The story so far</div>
        <ol className="chain">
          {story.events.map((e, i) => (
            <li key={`${e.title}-${i}`}><span className="chain-date">{date(e.published_at)}</span>{e.title}</li>
          ))}
        </ol>
      </div>

      <dl className="answers stacked">
        <dt>Status</dt>
        <dd><Pill tone={STATUS_TONE[story.status]}>{story.status_text}</Pill></dd>
        <dt>Stock reaction</dt>
        <dd className={moved ? (story.reaction!.value < 0 ? "bad" : "good") : ""}>{story.reaction_text}</dd>
        <dt>News confirmed?</dt>
        <dd><Pill tone={CONFIRMED_TONE[story.confirmed]}>{story.confirmed_text}</Pill></dd>
        <dt>Evidence</dt>
        <dd>{ev && <Pill tone={ev.tone}>{ev.text}</Pill>} <span className="muted small">{story.evidence_text}</span></dd>
      </dl>
      <span className="card-link">Read the full story →</span>
    </a>
  );
}
