// Track record of one event type across every event we measured: what the share price is
// expected to do, the average move, and how often it went the expected way. Used by the
// event page ("past events like this") and How it works (one row per event type).
import type { S } from "../api/client";

export interface TypeRecord { expected?: string; n: number; avg: number | null; unusual: number; asExpected: number }

export function typeRecord(playbook: S["Playbook"], events: S["EventCard"][]): TypeRecord {
  const name = playbook.title || playbook.theme;
  const expected = playbook.stages.flatMap((s) => s.decisions).find((d) => d.market_channel === "price")?.expected_direction;
  const done = events.filter((e) => e.event_type === name && e.stock_move != null);
  const asExpected = done.filter((e) => expected === "uncertain" ? e.stock_move_unusual
    : expected === "down" ? e.stock_move! < 0 : expected === "up" ? e.stock_move! > 0 : false).length;
  return {
    expected, n: done.length, unusual: done.filter((e) => e.stock_move_unusual).length, asExpected,
    avg: done.length ? done.reduce((n, e) => n + e.stock_move!, 0) / done.length : null,
  };
}
