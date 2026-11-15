// One storyline at a glance: what happened, how sure we are, what the market did.
import type { S } from "../../api/client";
import { CONFIDENCE, date, describe, label, STATUS_TONE } from "../../shared/labels";
import { Pill } from "../../shared/ui";

export function StoryCard({ item }: { item: S["BriefingItem"] }) {
  const conf = CONFIDENCE[item.confidence];
  const r = item.reaction;
  return (
    <a className="story-card" href={`#/story/${item.storyline_id}`}>
      <div className="story-card-top">
        <div>
          <div className="company">{item.company}</div>
          <div className="muted small">{item.ticker} · {item.market} · {label(item.theme)}</div>
        </div>
        <Pill tone={STATUS_TONE[item.status]}>{label(item.status)}</Pill>
      </div>
      <p className="headline">“{item.latest_summary}”</p>
      <div className="muted small">Latest: {label(item.latest_stage)} · {date(item.latest_at)}</div>
      <div className="story-card-facts">
        <div>
          <span className="muted small">Market reaction</span>
          <b className={r && r.significant ? (r.value < 0 ? "bad" : "good") : ""}>
            {r ? describe(r) : "not measured yet"}
          </b>
        </div>
        <div>
          <span className="muted small">Confirmed stages</span>
          <b>{item.stages_confirmed} of {item.stages}</b>
        </div>
        <div>
          <span className="muted small">Expectations met</span>
          <b>{item.expectations_measured ? `${item.expectations_met} of ${item.expectations_measured}` : "—"}</b>
        </div>
      </div>
      {conf && <Pill tone={conf.tone}>{conf.text}</Pill>}
    </a>
  );
}
