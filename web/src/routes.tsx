// The ONE route table. To add a page: add a feature folder and one entry here.
import type { ReactNode } from "react";
import { BriefingPage } from "./features/briefing/BriefingPage";
import { MethodPage } from "./features/method/MethodPage";
import { StoryPage } from "./features/story/StoryPage";

export interface Route {
  pattern: RegExp;
  nav?: string; // shown in the header when set
  href?: string;
  render: (params: string[], refreshKey: number) => ReactNode;
}

export const ROUTES: Route[] = [
  { pattern: /^#\/?$/, nav: "Briefing", href: "#/", render: (_, k) => <BriefingPage refreshKey={k} /> },
  { pattern: /^#\/story\/(.+)$/, render: ([id]) => <StoryPage key={id} id={id} /> },
  { pattern: /^#\/method$/, nav: "How it works", href: "#/method", render: () => <MethodPage /> },
];

export function match(hash: string): { route: Route; params: string[] } {
  for (const route of ROUTES) {
    const m = hash.match(route.pattern);
    if (m) return { route, params: m.slice(1) };
  }
  return { route: ROUTES[0], params: [] };
}
