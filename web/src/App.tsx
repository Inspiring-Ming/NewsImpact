// Layout: header (brand, navigation, live status), the latest-events ticker, the current page, and the Ask NewsImpact assistant.
// Hash routes need no server routing, so the site works from any static host.
import { useEffect, useState } from "react";
import { match, ROUTES } from "./routes";
import { AskBot } from "./shared/AskBot";
import { StatusBar } from "./shared/StatusBar";
import { Ticker } from "./shared/Ticker";

function useHash(): string {
  const [hash, setHash] = useState(window.location.hash || "#/");
  useEffect(() => {
    const onChange = () => { setHash(window.location.hash || "#/"); window.scrollTo(0, 0); };
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return hash;
}

export function App() {
  const hash = useHash();
  const [refreshKey, setRefreshKey] = useState(0);
  const { route, params } = match(hash);
  const navActive = (href?: string) => (href === "#/" ? route === ROUTES[0] || hash.startsWith("#/event") : hash === href);
  return (
    <div className="app">
      <header className="topbar">
        <a className="brand" href="#/">NewsImpact<span>by Inspiring Ming</span></a>
        <nav>
          {ROUTES.filter((r) => r.nav).map((r) => (
            <a key={r.href} href={r.href} className={navActive(r.href) ? "active" : ""}>{r.nav}</a>
          ))}
        </nav>
        <StatusBar onChanged={() => setRefreshKey((k) => k + 1)} />
      </header>
      <Ticker refreshKey={refreshKey} />
      <main>{route.render(params, refreshKey)}</main>
      <footer>Research evidence for analysis, not investment advice · © Inspiring Ming</footer>
      <AskBot eventId={hash.startsWith("#/event/") ? params[0] : undefined} />
    </div>
  );
}
