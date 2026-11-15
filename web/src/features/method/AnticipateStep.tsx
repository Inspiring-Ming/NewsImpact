// Step 3 - which reactions we predict for each event, and how often they have happened.
import type { S } from "../../api/client";
import { DIRECTION, label } from "../../shared/labels";
import { StepBlock } from "./StepBlock";

export function AnticipateStep({ method, calibration }: { method: S["Method"]; calibration: S["Calibration"] | null }) {
  const record = new Map((calibration?.reactions ?? []).map((r) => [`${r.theme}|${r.stage_name}|${r.channel}`, r]));
  return (
    <StepBlock id="anticipate"
      what="For every kind of event we list who usually reacts and how: large investors, analysts, option traders, boards, customers. These predictions are what we test in step 4."
      rules={[
        "Predictions come from the story type's playbook and are written as plain, testable statements (e.g. \"share price should fall\").",
        "Reactions that don't show in market data (e.g. a board review) are listed but marked as not testable in markets.",
        "Each prediction builds a track record across stories; with 20+ stories it is confirmed or dropped.",
      ]}>
      {method.playbooks.map((p) => (
        <details key={p.theme} className="details">
          <summary><b>{p.title || label(p.theme)}</b> · {p.stages.reduce((n, s) => n + s.decisions.length, 0)} predicted reactions</summary>
          {p.stages.map((s) => (
            <div key={s.name} className="small">
              <h4>{(s.title || label(s.name))}</h4>
              <ul className="rules">
                {s.decisions.map((d) => {
                  const r = d.market_channel ? record.get(`${p.theme}|${s.name}|${d.market_channel}`) : undefined;
                  return (
                    <li key={d.actor + d.decision}>
                      <b>{label(d.actor)}</b> {d.decision}
                      {d.market_channel && <> → {label(d.market_channel)} should {DIRECTION[d.expected_direction]}</>}
                      <span className="muted">
                        {" · "}{!d.market_channel ? "not testable in markets"
                          : r && r.n_events ? `happened in ${Math.round((r.share_consistent ?? 0) * r.n_events)} of ${r.n_events} stories` : "no tests yet"}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </details>
      ))}
    </StepBlock>
  );
}
