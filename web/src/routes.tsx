// The ONE route table. To add a page: add a feature folder and one entry here.
import type { ReactNode } from "react";
import { WatchlistPage } from "./features/watchlist/WatchlistPage";
import { MethodPage } from "./features/method/MethodPage";
import { EventPage } from "./features/event/EventPage";

export interface Route {
  pattern: RegExp;
  nav?: string; // shown in the header when set
  href?: string;
  render: (params: string[], refreshKey: number) => ReactNode;
}

export const ROUTES: Route[] = [
  { pattern: /^#\/?$/, nav: "Watchlist", href: "#/", render: (_, k) => <WatchlistPage refreshKey={k} /> },
  { pattern: /^#\/event\/(.+)$/, render: ([id]) => <EventPage key={id} id={id} /> },
  { pattern: /^#\/method$/, nav: "How it works", href: "#/method", render: () => <MethodPage /> },
];

export function match(hash: string): { route: Route; params: string[] } {
  for (const route of ROUTES) {
    const m = hash.match(route.pattern);
    if (m) return { route, params: m.slice(1) };
  }
  return { route: ROUTES[0], params: [] };
}
