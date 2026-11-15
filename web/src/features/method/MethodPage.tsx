// How it works: four parts, one tab each, named in plain words with the industry or
// research term beside them. To explain a new part, add one entry to TABS.
import { useState, type ReactNode } from "react";
import { api, type S } from "../../api/client";
import { State, Tabs } from "../../shared/ui";
import { useApi } from "../../shared/useApi";
import { AllSettings } from "./AllSettings";
import { AnticipateStep } from "./AnticipateStep";
import { ConnectStep } from "./ConnectStep";
import { MonitorStep } from "./MonitorStep";
import { VerifyStep } from "./VerifyStep";

type Data = { method: S["Method"]; calibration: S["Calibration"] | null };

const TABS: { id: string; label: string; render: (d: Data) => ReactNode }[] = [
  { id: "sources", label: "1. News sources", render: (d) => <MonitorStep method={d.method} /> },
  { id: "stories", label: "2. Story tracking", render: (d) => <ConnectStep {...d} /> },
  { id: "reactions", label: "3. Expected reactions", render: (d) => <AnticipateStep {...d} /> },
  { id: "market", label: "4. Market reaction check", render: (d) => <VerifyStep {...d} /> },
];

export function MethodPage() {
  const method = useApi(api.method);
  const calibration = useApi(api.calibration);
  const [tab, setTab] = useState(TABS[0].id);
  return (
    <>
      <section className="hero compact">
        <h1>How it works</h1>
        <p className="lead">Four parts, each with a clear rule and the evidence behind it. Every number has a stated reason and is checked against data as it builds up.</p>
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
