// Tab 2 - how news becomes an event made of updates, with the event types and observed timing.
import type { S } from "../../api/client";
import { label } from "../../shared/labels";
import { Term } from "../../shared/Term";
import { StepBlock } from "./StepBlock";

export function ConnectStep({ method, calibration }: { method: S["Method"]; calibration: S["Calibration"] | null }) {
  const gaps = new Map((calibration?.windows ?? []).map((w) => [w.theme, w]));
  return (
    <StepBlock term="eventsTab">
      <div className="table-wrap">
        <table>
          <thead><tr><th>Event type</th><th>Usual updates, in order</th><th className="num"><Term id="window" /></th><th><Term id="seen" /></th></tr></thead>
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
    </StepBlock>
  );
}
