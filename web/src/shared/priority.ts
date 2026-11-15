// Priority levels, defined once: name, order, colour class and what each means. The rules
// that assign them live on the server (app/views/guidance.py); the badge and the
// Priorities board both read this list, so a new level is one entry here.
import type { S } from "../api/client";

export interface Level {
  id: string;
  text: string;
  meaning: string;
  onBoard: boolean; // shown as a column on the Priorities board
}

export const LEVELS: Level[] = [
  { id: "act", text: "Act now", meaning: "Confirmed news with an unusual stock move or a new update in the last 24 hours.", onBoard: true },
  { id: "check", text: "Check", meaning: "Confirmed news with a normal move, or an unusual move that is not yet confirmed.", onBoard: true },
  { id: "background", text: "Background", meaning: "One source so far and no unusual stock move.", onBoard: false },
];

export const level = (id: string): Level => LEVELS.find((l) => l.id === id) ?? LEVELS[LEVELS.length - 1];

/** Events in priority order (by LEVELS), newest update first within a level. */
export function byPriority(companies: S["CompanyCard"][]) {
  const rank = (id: string) => LEVELS.findIndex((l) => l.id === id);
  const last = (e: S["EventCard"]) => e.updates[e.updates.length - 1].published_at;
  return companies.flatMap((c) => c.events.map((e) => ({ c, e })))
    .sort((a, b) => rank(a.e.priority) - rank(b.e.priority) || last(b.e).localeCompare(last(a.e)));
}
