// Tab 2 - how news becomes an event made of updates, with the event types and observed timing.
import type { S } from "../../api/client";
import { label } from "../../shared/labels";
import { AccuracyCheck } from "./AccuracyCheck";
import { StepBlock } from "./StepBlock";

export function ConnectStep({ method, calibration }: { method: S["Method"]; calibration: S["Calibration"] | null }) {
  const gaps = new Map((calibration?.windows ?? []).map((w) => [w.theme, w]));
  return (
    <StepBlock title="How we detect events and follow their updates"
      term="event detection and tracking (news analytics)"
      rules={[
        "Each sentence naming a tracked company is classified: which event type, who said it, rumour or fact.",
        "Same company + same event type + within the event's time window = an update to the same event.",
        `Sources publish out of order, so a complete event still accepts earlier updates for ${method.late_report_days} days.`,
        "Background mentions (\"has had several recalls in the past\") are not new updates.",
      ]}>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Event type</th><th>Typical updates</th><th className="num">Followed for</th><th>Seen so far</th></tr></thead>
          <tbody>
            {method.playbooks.map((p) => {
              const g = gaps.get(p.theme);
              return (
                <tr key={p.theme}>
                  <td><b>{p.title || label(p.theme)}</b></td>
                  <td className="small">{p.stages.map((s) => (s.title || label(s.name))).join(" → ")}</td>
                  <td className="num">{p.link_window_days} days</td>
                  <td className="small">{g && g.n_gaps ? `typical gap ${g.median_days?.toFixed(1)} days (${g.n_gaps} seen)` : "none linked yet"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="small muted">Time windows start as stated assumptions and are replaced by measured gaps once 20+ are seen.</p>
      <AccuracyCheck llmPreset={method.llm_preset_in_use} />
    </StepBlock>
  );
}
