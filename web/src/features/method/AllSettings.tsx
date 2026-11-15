// Every number used, with the reason for it (folded away: for reviewers).
import type { S } from "../../api/client";
import { humanize } from "../../shared/labels";

type Section = Record<string, unknown> & { rationale?: Record<string, string> };

export function AllSettings({ method }: { method: S["Method"] }) {
  const sections = Object.entries(method.methodology).filter(([, v]) => typeof v === "object") as [string, Section][];
  return (
    <details className="details all-settings">
      <summary>All settings and the reason for each</summary>
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
      <h3>Language models</h3>
      {Object.entries(method.llm_presets).map(([name, p]) => (
        <div key={name} className="setting">
          <b>{humanize(name)}</b> <span className="mono small">{p.model}</span>{method.llm_preset_in_use === name && " (in use)"}
          <div className="small muted">{p.why}</div>
        </div>
      ))}
    </details>
  );
}
