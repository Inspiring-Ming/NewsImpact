// Layout and navigation (hash routes: no server routing needed, works from any static host).
import { useEffect, useState } from "react";
import { Calibration } from "./pages/Calibration";
import { Method } from "./pages/Method";
import { Outlets } from "./pages/Outlets";
import { Overview } from "./pages/Overview";
import { Quality } from "./pages/Quality";
import { StorylineDetail } from "./pages/StorylineDetail";
import { Storylines } from "./pages/Storylines";

const NAV = [
  ["#/", "Overview"], ["#/storylines", "Storylines"], ["#/outlets", "Outlets"],
  ["#/calibration", "Calibration"], ["#/quality", "Quality"], ["#/method", "Method"],
] as const;

function useRoute(): string {
  const [hash, setHash] = useState(window.location.hash || "#/");
  useEffect(() => {
    const onChange = () => setHash(window.location.hash || "#/");
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return hash;
}

function Screen({ route }: { route: string }) {
  const detail = route.match(/^#\/storylines\/(.+)$/);
  if (detail) return <StorylineDetail id={detail[1]} />;
  switch (route) {
    case "#/storylines": return <Storylines />;
    case "#/outlets": return <Outlets />;
    case "#/calibration": return <Calibration />;
    case "#/quality": return <Quality />;
    case "#/method": return <Method />;
    default: return <Overview />;
  }
}

export function App() {
  const route = useRoute();
  const section = "#/" + (route.split("/")[1] ?? "");
  return (
    <div className="app">
      <header className="topbar">
        <a className="brand" href="#/">NewsImpact <span>by Inspiring Ming</span></a>
        <nav>
          {NAV.map(([href, label]) => (
            <a key={href} href={href} className={section === href ? "active" : ""}>{label}</a>
          ))}
        </nav>
      </header>
      <main><Screen route={route} /></main>
      <footer className="muted small">Research evidence for analysis, not investment advice · © Inspiring Ming</footer>
    </div>
  );
}
