// Step 2 - how related news becomes one story, with the story types and observed timing.
import type { S } from "../../api/client";
import { label } from "../../shared/labels";
import { AccuracyCheck } from "./AccuracyCheck";
import { StepBlock } from "./StepBlock";

export function ConnectStep({ method, calibration }: { method: S["Method"]; calibration: S["Calibration"] | null }) {
  const gaps = new Map((calibration?.windows ?? []).map((w) => [w.theme, w]));
  return (
    <StepBlock title="How we spot events and link them into stories"
      term="event detection and story tracking (news analytics)"
      what="Each sentence about a company is classified as an event (e.g. a recall or a resignation). Events about the same company that follow a known pattern are linked into one story."
      rules={[
        "Same company + same kind of story + within the story's time window = same story.",
        `Outlets publish out of order, so a concluded story still accepts its earlier events for ${method.late_report_days} days.`,
        "Background mentions (\"has had several recalls in the past\") are not treated as new events.",
        "While a story is open, we automatically search our outlets for its next event.",
      ]}>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Story type</th><th>Typical chain of events</th><th>Followed for</th><th>Seen so far</th></tr></thead>
          <tbody>
            {method.playbooks.map((p) => {
              const g = gaps.get(p.theme);
              return (
                <tr key={p.theme}>
                  <td><b>{p.title || label(p.theme)}</b></td>
                  <td className="small">{p.stages.map((s) => (s.title || label(s.name))).join(" → ")}</td>
                  <td>{p.link_window_days} days</td>
                  <td className="small">{g && g.n_gaps ? `typical gap ${g.median_days?.toFixed(1)} days (${g.n_gaps} observed)` : "no linked events yet"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="small muted">Time windows start as stated assumptions and are replaced by measured gaps once 20+ are observed.</p>
      <AccuracyCheck llmPreset={method.llm_preset_in_use} />
    </StepBlock>
  );
}
