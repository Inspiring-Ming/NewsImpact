// Typed access to the /v1 API. Types come from schema.ts, generated from the
// server's OpenAPI document (npm run gen:api) - never hand-written.
import type { components } from "./schema";

export type S = components["schemas"];

async function request<T>(method: "GET" | "POST" | "PUT" | "DELETE", path: string): Promise<T> {
  const res = await fetch(path, { method, headers: { Accept: "application/json" } });
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
  calibration: () => request<S["Calibration"]>("GET", "/v1/calibration"),
  evaluation: () => request<S["Evaluation"]>("GET", "/v1/evaluation"),
  method: () => request<S["Method"]>("GET", "/v1/method"),
};
