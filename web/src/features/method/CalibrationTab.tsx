// Across many stories: do the expectations and time windows hold up?
import { api } from "../../api/client";
import { label } from "../../shared/labels";
import { Pill, State } from "../../shared/ui";
import { useApi } from "../../shared/useApi";

const FINDING = {
  supported: { text: "Holds up", tone: "good" }, contradicted: { text: "Does not hold", tone: "bad" },
  not_significant: { text: "No clear effect", tone: "neutral" }, indicative: { text: "Too few stories yet", tone: "muted" },
  no_data: { text: "No data yet", tone: "muted" },
} as const;

export function CalibrationTab() {
  const { data, error, loading } = useApi(api.calibration);
  const rows = (data?.reactions ?? []).filter((r) => r.n_events > 0);
  return (
    <>
      <p className="muted">
        Each story type starts from reasoned expectations. As stories accumulate (20+ per stage), these become measured facts.
      </p>
      <State error={error} loading={loading}>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Story type</th><th>Stage</th><th>Expected</th><th>Stories</th><th>Finding</th></tr></thead>
            <tbody>
              {rows.map((r) => {
                const f = FINDING[r.finding as keyof typeof FINDING];
                return (
                  <tr key={r.theme + r.stage_name + r.channel}>
                    <td>{label(r.theme)}</td><td>{label(r.stage_name)}</td>
                    <td>{label(r.channel)} {r.expected === "uncertain" ? "moves" : r.expected === "up" ? "rises" : "falls"}</td>
                    <td>{r.n_events}</td><td><Pill tone={f.tone}>{f.text}</Pill></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <h3>How long we follow a story</h3>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Story type</th><th>Window</th><th>Typical gap between stages</th></tr></thead>
            <tbody>
              {(data?.windows ?? []).map((w) => (
                <tr key={w.theme}>
                  <td>{label(w.theme)}</td><td>{w.configured_days} days</td>
                  <td>{w.median_days != null ? `${w.median_days.toFixed(1)} days (from ${w.n_gaps} gap${w.n_gaps === 1 ? "" : "s"})` : "not observed yet"}
                    {w.suggested_days && <span className="muted"> · suggests {w.suggested_days} days</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </State>
      <p className="small muted">Method: standardized cross-sectional (BMP) tests across stories; see docs/07.</p>
    </>
  );
}
