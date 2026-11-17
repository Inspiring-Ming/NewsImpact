// Typed access to the /v1 API. Types come from schema.ts, generated from the
// server's OpenAPI document (npm run gen:api) - never hand-written.
import type { components } from "./schema";

export type S = components["schemas"];

async function request<T>(method: "GET" | "POST" | "PUT" | "DELETE", path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const res = await fetch(path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `${res.status} ${res.statusText}`);
  }
  return (await res.json()) as T;
}

export const api = {
  overview: () => request<S["Overview"]>("GET", "/v1/overview"),
  monitor: () => request<S["MonitorStatus"]>("GET", "/v1/monitor"),
  runRound: () => request<S["MonitorStatus"]>("POST", "/v1/monitor/run"),
  loadDemo: () => request<Record<string, number>>("POST", "/v1/demo/load"),
  companies: () => request<S["CompanyCard"][]>("GET", "/v1/companies"),
  me: () => request<{ user_id: string; admin: boolean; guest: boolean }>("GET", "/v1/me"),
  watchlist: () => request<string[]>("GET", "/v1/watchlist"),
  follow: (ticker: string) => request<string[]>("PUT", `/v1/watchlist/${encodeURIComponent(ticker)}`),
  unfollow: (ticker: string) => request<string[]>("DELETE", `/v1/watchlist/${encodeURIComponent(ticker)}`),
  alerts: () => request<Record<string, string>>("GET", "/v1/alerts"),
  eventSummary: (id: string) => request<S["CompanyCard"]>("GET", `/v1/events/${id}/summary`),
  storyline: (id: string) => request<S["Storyline"]>("GET", `/v1/storylines/${id}`),
  assessment: (id: string) => request<S["Assessment"]>("GET", `/v1/storylines/${id}/assessment`),
  prices: (id: string) => request<S["PricePath"] | null>("GET", `/v1/storylines/${id}/prices`),
  sources: () => request<S["SourceWithReliability"][]>("GET", "/v1/sources"),
  coverage: () => request<S["OutletCoverage"][]>("GET", "/v1/coverage"),
  method: () => request<S["Method"]>("GET", "/v1/method"),
  eventTypes: () => request<S["TypeStats"][]>("GET", "/v1/event-types"),
  assistant: () => request<S["AssistantStatus"]>("GET", "/v1/assistant"),
  ask: (question: string, eventId?: string) =>
    request<S["Answer"]>("POST", "/v1/assistant/ask", { question, event_id: eventId ?? null }),
};
