// How often we read the news right: the live reading method on hand-labelled test sentences
// (data/eval), counted as "right in N of M". Computed once per server start.
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
      <p className="small muted">
        How we test: {result.data?.examples ?? "…"} example sentences (made-up companies, written to include hard cases),
        each labelled by a person, are read with the same method as live news
        ({llmPreset === "off" ? "word lists" : "AI reading"}); we count how often we agree. The test runs again whenever the method changes.
      </p>
      <State error={result.error} loading={result.loading}>
        <div className="accuracy-rows">
          {result.data?.fields.map((f) => (
            <div key={f.field} className="accuracy-row">
              <span>{FIELD_NAMES[f.field] ?? humanize(f.field)}</span>
              <Meter value={f.accuracy} tone={f.accuracy >= 0.9 ? "good" : f.accuracy >= 0.75 ? "warn" : "bad"} />
              <span><b>{Math.round(f.accuracy * (result.data?.examples ?? 0))}</b> of {result.data?.examples} right</span>
            </div>
          ))}
        </div>
      </State>
    </div>
  );
}
