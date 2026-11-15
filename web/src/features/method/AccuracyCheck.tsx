// How accurately we read the news: scored on hand-checked sentences.
import { useState } from "react";
import { api, type S } from "../../api/client";
import { humanize } from "../../shared/labels";
import { Fact, State } from "../../shared/ui";

const FIELD_NAMES: Record<string, string> = {
  event_type: "Recognising the event", attribution_kind: "Knowing who said it",
  is_speculative: "Rumour or fact", is_background: "New news or old background",
};

export function AccuracyCheck({ llmPreset }: { llmPreset: string }) {
  const [result, setResult] = useState<S["Evaluation"] | null>(null);
  const [state, setState] = useState<{ busy: boolean; error: string | null }>({ busy: false, error: null });
  const run = () => {
    setState({ busy: true, error: null });
    api.evaluation().then((r) => { setResult(r); setState({ busy: false, error: null }); })
      .catch((e: Error) => setState({ busy: false, error: e.message }));
  };
  return (
    <div className="accuracy">
      <h3>How accurately we read the news</h3>
      <p className="small">Scored on hand-checked example sentences before any reading method is trusted.
        Reading method in use: <b>{llmPreset === "off" ? "word lists" : `language model (${llmPreset})`}</b>.</p>
      <button className="primary small" onClick={run} disabled={state.busy}>{state.busy ? "Checking…" : "Run the accuracy check"}</button>
      <State error={state.error}>
        {result && (
          <div className="facts">
            {result.fields.map((f) => (
              <Fact key={f.field} label={FIELD_NAMES[f.field] ?? humanize(f.field)} value={`${Math.round(f.accuracy * 100)}% correct`}
                    tone={f.accuracy >= 0.9 ? "good" : f.accuracy >= 0.75 ? "ok" : "warn"} />
            ))}
          </div>
        )}
      </State>
    </div>
  );
}
