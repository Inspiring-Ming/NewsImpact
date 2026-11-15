// Every setting and the reason for it - so no number is a mystery.
import { api } from "../api/client";
import { Badge, Card, Loading, Page } from "../components/ui";
import { useApi } from "../components/useApi";

type Section = Record<string, unknown> & { rationale?: Record<string, string> };

export function Method() {
  const { data, error, loading } = useApi(api.method);
  const sections = data ? Object.entries(data.methodology).filter(([, v]) => typeof v === "object") as [string, Section][] : [];
  return (
    <Page title="Method" intro="Every number is a reasoned starting point that is measured and revised (see Calibration). Values live in versioned files; every assessment records which version it used.">
      <Loading error={error} loading={loading} />
      {data && (
        <>
          <Card title="How long a story is followed" wide>
            <table>
              <thead><tr><th>Story type</th><th>Window</th><th>Basis</th><th>Why</th></tr></thead>
              <tbody>
                {data.playbooks.map((p) => (
                  <tr key={p.theme}>
                    <td><b>{p.theme.replace(/_/g, " ")}</b><div className="small muted">{p.stages.map((s) => s.name.replace(/_/g, " ")).join(" → ")}</div></td>
                    <td>{p.link_window_days} days</td><td>{p.window_basis}</td><td className="small">{p.window_why}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
          {sections.map(([name, section]) => (
            <Card key={name} title={`${name} settings`} wide>
              <table>
                <tbody>
                  {Object.entries(section.rationale ?? {}).map(([key, why]) => (
                    <tr key={key}>
                      <td><b>{key.replace(/_/g, " ")}</b></td>
                      <td className="mono small">{JSON.stringify(lookup(section, key))}</td>
                      <td className="small">{why}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          ))}
          <Card title="Language model options" wide>
            <table>
              <thead><tr><th>Preset</th><th>Model</th><th>Why</th></tr></thead>
              <tbody>
                {Object.entries(data.llm_presets).map(([name, p]) => (
                  <tr key={name}>
                    <td><b>{name}</b> {data.llm_preset_in_use === name && <Badge value="in use" />}</td>
                    <td className="mono small">{p.provider}: {p.model}</td><td className="small">{p.why}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="muted small">In use: <b>{data.llm_preset_in_use}</b>. Change with NI_LLM_PRESET (off | quality | economy | local).</p>
          </Card>
        </>
      )}
    </Page>
  );
}

function lookup(section: Section, key: string): unknown {
  return key.split(".").reduce<unknown>((v, k) => (v as Record<string, unknown> | undefined)?.[k], section);
}
