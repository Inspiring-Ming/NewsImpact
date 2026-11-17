// How it works: three parts, one tab each, each with its live data and every number explained
// in words next to it. To explain a new part, add one entry to TABS.
import { useState, type ReactNode } from "react";
import { api, type S } from "../../api/client";
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
        <p className="lead">From news to measured stock moves, in three steps. Every number here is live and says where it comes from.</p>
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

/** A numbered row of steps: how a part of the method works, in order. */
export function Flow({ steps }: { steps: { title: string; text: ReactNode }[] }) {
  return (
    <ol className="flow">
      {steps.map((s, i) => (
        <li key={s.title}><span className="flow-num">{i + 1}</span><b>{s.title}</b><p>{s.text}</p></li>
      ))}
    </ol>
  );
}

/** A methodology setting by path, e.g. setting(method, "validation", "confirmation_days"). */
export function setting(method: S["Method"], section: string, key: string): number | undefined {
  const sec = (method.methodology as Record<string, Record<string, unknown>>)[section];
  return typeof sec?.[key] === "number" ? (sec[key] as number) : undefined;
}
