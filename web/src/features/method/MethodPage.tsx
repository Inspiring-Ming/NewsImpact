// How it works and why to trust it. The page is a list of tabs: to add a topic,
// add one entry to TABS.
import { useState, type ComponentType } from "react";
import { Tabs } from "../../shared/ui";
import { HowItWorks } from "../briefing/HowItWorks";
import { AccuracyTab } from "./AccuracyTab";
import { CalibrationTab } from "./CalibrationTab";
import { SettingsTab } from "./SettingsTab";
import { SourcesTab } from "./SourcesTab";

const TABS: { id: string; label: string; component: ComponentType }[] = [
  { id: "sources", label: "Sources", component: SourcesTab },
  { id: "accuracy", label: "Analysis accuracy", component: AccuracyTab },
  { id: "calibration", label: "Track record", component: CalibrationTab },
  { id: "settings", label: "Settings & reasons", component: SettingsTab },
];

export function MethodPage() {
  const [tab, setTab] = useState(TABS[0].id);
  const Body = TABS.find((t) => t.id === tab)!.component;
  return (
    <>
      <section className="hero compact">
        <h1>How it works</h1>
        <HowItWorks />
      </section>
      <Tabs tabs={TABS} active={tab} onChange={setTab} />
      <div className="tab-panel"><Body /></div>
    </>
  );
}
