// How accurately we read the news: our reading of 56 hand-labelled sentences compared with
// the human label. Shown automatically; computed once per server start.
import { api } from "../../api/client";
import { humanize } from "../../shared/labels";
import { State } from "../../shared/ui";
import { Term } from "../../shared/Term";
import { useApi } from "../../shared/useApi";
import { Meter } from "../../shared/viz";

const FIELD_NAMES: Record<string, string> = {
  event_type: "Which event it is", attribution_kind: "Who said it",
  is_speculative: "Rumour or fact", is_background: "New news or old background",
};

export function AccuracyCheck({ llmPreset }: { llmPreset: string }) {
  const result = useApi(api.evaluation);
  return (
    <div className="accuracy">
      <h3><Term id="accuracy" /></h3>
      <p className="small muted">Reading method: {llmPreset === "off" ? "word lists" : `language model (${llmPreset})`} · checked on {result.data?.examples ?? "…"} sentences labelled by hand</p>
      <State error={result.error} loading={result.loading}>
        <div className="accuracy-rows">
          {result.data?.fields.map((f) => (
            <div key={f.field} className="accuracy-row">
              <span>{FIELD_NAMES[f.field] ?? humanize(f.field)}</span>
              <Meter value={f.accuracy} tone={f.accuracy >= 0.9 ? "good" : f.accuracy >= 0.75 ? "warn" : "bad"} />
              <b>{Math.round(f.accuracy * 100)}%</b>
            </div>
          ))}
        </div>
      </State>
    </div>
  );
}
