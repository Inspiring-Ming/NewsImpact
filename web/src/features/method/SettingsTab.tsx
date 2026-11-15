// Every setting and the reason for it.
import { api } from "../../api/client";
import { humanize, label } from "../../shared/labels";
import { Pill, State } from "../../shared/ui";
import { useApi } from "../../shared/useApi";

type Section = Record<string, unknown> & { rationale?: Record<string, string> };

export function SettingsTab() {
  const { data, error, loading } = useApi(api.method);
  const sections = data ? (Object.entries(data.methodology).filter(([, v]) => typeof v === "object") as [string, Section][]) : [];
  return (
    <State error={error} loading={loading}>
      {data && (
        <>
          <p className="muted">No number is arbitrary: each starts from a stated reason and is revised as data accumulates.</p>
          <h3>Story types</h3>
          {data.playbooks.map((p) => (
            <div key={p.theme} className="setting">
              <b>{label(p.theme)}</b> <span className="muted">· followed for {p.link_window_days} days</span>
              <div className="small">{p.stages.map((s) => label(s.name)).join(" → ")}</div>
              <div className="small muted">{p.window_why}</div>
            </div>
          ))}
          {sections.map(([name, sec]) => (
            <div key={name}>
              <h3>{humanize(name)}</h3>
              {Object.entries(sec.rationale ?? {}).map(([key, why]) => (
                <div key={key} className="setting">
                  <b>{humanize(key.split(".").pop() ?? key)}</b>{" "}
                  <span className="mono small">{JSON.stringify(key.split(".").reduce<unknown>((v, k) => (v as Record<string, unknown> | undefined)?.[k], sec))}</span>
                  <div className="small muted">{why}</div>
                </div>
              ))}
            </div>
          ))}
          <h3>Language model</h3>
          {Object.entries(data.llm_presets).map(([name, p]) => (
            <div key={name} className="setting">
              <b>{humanize(name)}</b> <span className="mono small">{p.model}</span>{" "}
              {data.llm_preset_in_use === name && <Pill tone="good">in use</Pill>}
              <div className="small muted">{p.why}</div>
            </div>
          ))}
        </>
      )}
    </State>
  );
}
