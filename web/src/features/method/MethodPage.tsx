// How it works: three parts, one tab each, each with its live data and definitions on hover.
// To explain a new part, add one entry to TABS.
import { useState, type ReactNode } from "react";
import { api, type S } from "../../api/client";
import { State, Tabs } from "../../shared/ui";
import { useApi } from "../../shared/useApi";
import { AllSettings } from "./AllSettings";
import { ConnectStep } from "./ConnectStep";
import { MonitorStep } from "./MonitorStep";
import { VerifyStep } from "./VerifyStep";

type Data = { method: S["Method"]; calibration: S["Calibration"] | null };

const TABS: { id: string; label: string; render: (d: Data) => ReactNode }[] = [
  { id: "sources", label: "1. News sources", render: (d) => <MonitorStep method={d.method} /> },
  { id: "events", label: "2. Events we detect", render: (d) => <ConnectStep {...d} /> },
  { id: "market", label: "3. Does it move the stock?", render: (d) => <VerifyStep method={d.method} /> },
];

export function MethodPage() {
  const method = useApi(api.method);
  const calibration = useApi(api.calibration);
  const [tab, setTab] = useState(TABS[0].id);
  return (
    <>
      <section className="hero compact">
        <h1>How it works</h1>
        <p className="lead">From news to measured stock moves, in three steps, with live data. Point at any underlined word for its meaning.</p>
      </section>
      <Tabs tabs={TABS} active={tab} onChange={setTab} />
      <State error={method.error} loading={method.loading}>
        {method.data && (
          <>
            {TABS.find((t) => t.id === tab)!.render({ method: method.data, calibration: calibration.data })}
            <AllSettings method={method.data} />
          </>
        )}
      </State>
    </>
  );
}
