// Across all storylines: do the playbooks' expectations and windows match reality?
import { api } from "../api/client";
import { Badge, Card, Loading, num, Page, pct } from "../components/ui";
import { useApi } from "../components/useApi";

export function Calibration() {
  const { data, error, loading } = useApi(api.calibration);
  return (
    <Page
      title="Calibration"
      intro="Playbooks start as reasoned expectations. As storylines accumulate, these tables test them on real reactions (BMP cross-sectional test) and real time between stages. Fewer than 20 events = indicative only."
    >
      <Loading error={error} loading={loading} />
      {data && (
        <>
          <Card title="Does each stage move each channel as expected?" wide>
            <table>
              <thead><tr><th>Story type</th><th>Stage</th><th>Channel</th><th>Expected</th><th>Events</th><th>Mean z</th><th>BMP z</th><th>Consistent</th><th>Finding</th></tr></thead>
              <tbody>
                {data.reactions.map((r) => (
                  <tr key={r.theme + r.stage_name + r.channel}>
                    <td>{r.theme.replace(/_/g, " ")}</td><td>{r.stage_name.replace(/_/g, " ")}</td>
                    <td>{r.channel.replace(/_/g, " ")}</td><td>{r.expected}</td><td>{r.n_events}</td>
                    <td>{num(r.mean_statistic)}</td><td>{num(r.cross_sectional_z)}</td><td>{pct(r.share_consistent)}</td>
                    <td><Badge value={r.finding} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
          <Card title="Do link windows fit the time between stages?" wide>
            <table>
              <thead><tr><th>Story type</th><th>Gaps seen</th><th>Median days</th><th>90th percentile days</th><th>Configured window</th><th>Suggested</th></tr></thead>
              <tbody>
                {data.windows.map((w) => (
                  <tr key={w.theme}>
                    <td>{w.theme.replace(/_/g, " ")}</td><td>{w.n_gaps}</td><td>{num(w.median_days, 1)}</td>
                    <td>{num(w.quantile_days, 1)}</td><td>{w.configured_days}</td><td>{w.suggested_days ?? "needs ≥ 20 gaps"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </>
      )}
    </Page>
  );
}
