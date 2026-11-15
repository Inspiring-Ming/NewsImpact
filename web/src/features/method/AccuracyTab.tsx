// How accurate the text analysis is, on hand-labelled sentences.
import { useState } from "react";
import { api, type S } from "../../api/client";
import { humanize } from "../../shared/labels";
import { Fact, State } from "../../shared/ui";

const FIELD_NAMES: Record<string, string> = {
  event_type: "What happened (event type)", attribution_kind: "Where the claim came from",
  is_speculative: "Rumour or fact", is_background: "News or background",
};

export function AccuracyTab() {
  const [result, setResult] = useState<S["Evaluation"] | null>(null);
  const [state, setState] = useState<{ busy: boolean; error: string | null }>({ busy: false, error: null });
  const run = () => {
    setState({ busy: true, error: null });
    api.evaluation().then((r) => { setResult(r); setState({ busy: false, error: null }); })
      .catch((e: Error) => setState({ busy: false, error: e.message }));
  };
  return (
    <>
      <p className="muted">
        Before any analysis method is trusted, it is scored on the same hand-labelled sentences.
        If a language model is switched on, running this check calls it (a few cents at most).
      </p>
      <button className="primary" onClick={run} disabled={state.busy}>{state.busy ? "Checking…" : "Run the accuracy check"}</button>
      <State error={state.error}>
        {result && (
          <>
            <div className="facts">
              {result.fields.map((f) => (
                <Fact key={f.field} label={FIELD_NAMES[f.field] ?? humanize(f.field)} value={`${Math.round(f.accuracy * 100)}% correct`}
                      tone={f.accuracy >= 0.9 ? "good" : f.accuracy >= 0.75 ? "ok" : "warn"} />
              ))}
            </div>
            <p className="small muted">{result.examples} sentences · method: <span className="mono">{result.chain}</span></p>
            {result.event_type_misses.length > 0 && (
              <details className="details">
                <summary>{result.event_type_misses.length} sentence(s) it got wrong</summary>
                <ul>{result.event_type_misses.map((m) => <li key={m.text} className="small">{m.text} — expected <b>{humanize(m.expected)}</b>, got {humanize(m.predicted)}</li>)}</ul>
              </details>
            )}
          </>
        )}
      </State>
    </>
  );
}
