// Who we expected to react, and did they? Each prediction next to what was measured.
import { describe, DIRECTION, humanize, label, RESULT } from "../../shared/labels";
import { useNames } from "../../shared/names";
import { Pill } from "../../shared/ui";
import type { StoryData } from "./context";

export function Reactions({ assessment, company }: StoryData) {
  const { title } = useNames();
  return (
    <div className="table-wrap card">
      <table className="reactions">
        <thead><tr><th>After</th><th>Who</th><th>What we expected</th><th>Did it happen?</th></tr></thead>
        <tbody>
          {assessment.stages.flatMap((st) => st.decisions.map((d, j) => {
            const r = RESULT[d.verdict] ?? { text: humanize(d.verdict), tone: "neutral" as const };
            return (
              <tr key={`${st.stage_name}-${d.actor}-${d.decision}`}>
                <td className="small">{j === 0 ? title(st.stage_name) : ""}</td>
                <td><b>{label(d.actor)}</b></td>
                <td>
                  {d.decision}
                  {d.channel && <div className="muted small">so the {label(d.channel)} should {DIRECTION[d.expected] ?? d.expected}</div>}
                </td>
                <td>
                  <Pill tone={r.tone}>{r.text}</Pill>
                  {d.evidence && <div className="small">{describe(d.evidence, company.benchmark_name)}</div>}
                </td>
              </tr>
            );
          }))}
        </tbody>
      </table>
    </div>
  );
}
