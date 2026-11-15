// One story, shown through the same four steps as the whole product.
import type { S } from "../../api/client";
import { CONFIDENCE, date, describe, STATUS } from "../../shared/labels";
import { useNames } from "../../shared/names";
import { STEPS } from "../../shared/steps";
import { Pill } from "../../shared/ui";

export function StoryCard({ item }: { item: S["BriefingItem"] }) {
  const { title } = useNames();
  const status = STATUS[item.status];
  const conf = CONFIDENCE[item.confidence];
  const r = item.reaction;
  const rail: Record<string, { value: string; note: string; tone?: string }> = {
    monitor: { value: `${item.outlets}`, note: item.outlets === 1 ? "outlet reported it" : "outlets reported it" },
    connect: { value: `${item.stages}`, note: item.stages === 1 ? "event so far" : "events linked" },
    anticipate: { value: `${item.predictions}`, note: "reactions predicted" },
    verify: r
      ? { value: describe(r), note: r.significant ? "clear market move" : "within normal swings",
          tone: r.significant ? (r.value < 0 ? "bad" : "good") : undefined }
      : { value: "—", note: "waiting for market data" },
  };
  return (
    <a className="story-card" href={`#/story/${item.storyline_id}`}>
      <div className="story-card-top">
        <div>
          <div className="company">{item.company} <span className="muted small">{item.ticker} · {item.market}</span></div>
          <div className="story-type">{title(item.theme)}</div>
        </div>
        {status && <Pill tone={status.tone}>{status.text}</Pill>}
      </div>
      <p className="headline">“{item.latest_summary}”</p>
      <div className="muted small">Latest event: {title(item.latest_stage)} · {date(item.latest_at)}</div>
      <ol className="rail">
        {STEPS.map((s) => (
          <li key={s.id} className={`step-${s.id}`}>
            <span className="step-n">{s.n}</span>
            <b className={rail[s.id].tone ?? ""}>{rail[s.id].value}</b>
            <span className="muted small">{rail[s.id].note}</span>
          </li>
        ))}
      </ol>
      <div className="story-card-foot">
        <span className="small">
          {item.stages_confirmed} of {item.stages} events verified ·{" "}
          {item.expectations_measured ? `${item.expectations_met} of ${item.expectations_measured} predicted reactions happened` : "reactions not tested yet"}
        </span>
        {conf && <Pill tone={conf.tone}>{conf.text}</Pill>}
      </div>
    </a>
  );
}
