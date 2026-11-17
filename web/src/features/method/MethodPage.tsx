// How it works: three parts, one tab each, each with its live data and every number explained
// in words next to it. To explain a new part, add one entry to TABS.
import { useState, type ReactNode } from "react";
import { api, type S } from "../../api/client";
import { Term } from "../../shared/Term";
import { State, Tabs } from "../../shared/ui";
import { useApi } from "../../shared/useApi";
import { AllSettings } from "./AllSettings";
import { ConnectStep } from "./ConnectStep";
import { MonitorStep } from "./MonitorStep";
import { VerifyStep } from "./VerifyStep";

export type MethodData = { method: S["Method"]; types: S["TypeStats"][] };

const TABS: { id: string; label: string; render: (d: MethodData) => ReactNode }[] = [
  { id: "sources", label: "1. News sources", render: (d) => <MonitorStep {...d} /> },
  { id: "events", label: "2. Events we detect", render: (d) => <ConnectStep {...d} /> },
  { id: "market", label: "3. Does it move the stock?", render: (d) => <VerifyStep {...d} /> },
];

export function MethodPage() {
  const method = useApi(api.method);
  const types = useApi(api.eventTypes);
  const [tab, setTab] = useState(TABS[0].id);
  return (
    <>
      <section className="hero compact">
        <h1>How it works</h1>
        <p className="lead">From news to measured stock moves, in three steps. Live numbers; point at any underlined word for the detail.</p>
      </section>
      <Tabs tabs={TABS} active={tab} onChange={setTab} />
      <State error={method.error ?? types.error} loading={method.loading || types.loading}>
        {method.data && types.data && (
          <>
            {TABS.find((t) => t.id === tab)!.render({ method: method.data, types: types.data })}
            <AllSettings method={method.data} />
          </>
        )}
      </State>
    </>
  );
}

/** The opening of a tab: a kicker, a headline, one line of explanation. */
export function Head({ kicker, title, dek }: { kicker: string; title: string; dek: ReactNode }) {
  return (
    <header className="hiw-head">
      <span className="hiw-kicker">{kicker}</span>
      <h2>{title}</h2>
      <p>{dek}</p>
    </header>
  );
}

/** Numbered steps on one line; the full explanation on hover. */
export function Flow({ steps }: { steps: { title: string; line: string; tip: string }[] }) {
  return (
    <ol className="stepper">
      {steps.map((s, i) => (
        <li key={s.title}>
          <span className="stepper-num">{String(i + 1).padStart(2, "0")}</span>
          <Term tip={s.tip}><b>{s.title}</b></Term>
          <span className="stepper-line">{s.line}</span>
        </li>
      ))}
    </ol>
  );
}

/** A methodology setting by path, e.g. setting(method, "validation", "confirmation_days"). */
export function setting(method: S["Method"], section: string, key: string): number | undefined {
  const sec = (method.methodology as Record<string, Record<string, unknown>>)[section];
  return typeof sec?.[key] === "number" ? (sec[key] as number) : undefined;
}
