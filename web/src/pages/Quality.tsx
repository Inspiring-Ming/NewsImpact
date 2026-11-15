// How good is the text analysis? Scored on hand-labelled sentences.
import { useState } from "react";
import { api, type S } from "../api/client";
import { Card, Page, pct } from "../components/ui";

export function Quality() {
  const [result, setResult] = useState<S["Evaluation"] | null>(null);
  const [state, setState] = useState<"idle" | "running" | string>("idle");
  const run = () => {
    setState("running");
    api.evaluation().then((r) => { setResult(r); setState("idle"); }).catch((e: Error) => setState(e.message));
  };
  return (
    <Page
      title="Analysis quality"
      intro="Every analysis chain (word lists, or a language model preset) is scored on the same hand-labelled sentences before it is trusted. If a language model is on, running this calls it (within the monthly budget)."
      actions={<button className="primary" onClick={run} disabled={state === "running"}>{state === "running" ? "Scoring…" : "Run evaluation"}</button>}
    >
      {state !== "idle" && state !== "running" && <p className="error">{state}</p>}
      {result && (
        <>
          <p className="muted small">Chain: <span className="mono">{result.chain}</span> · {result.examples} labelled sentences</p>
          <div className="grid2">
            {result.fields.map((f) => (
              <Card key={f.field} title={`${f.field.replace(/_/g, " ")}: ${pct(f.accuracy)} accurate`}>
                <table>
                  <thead><tr><th>Label</th><th>Precision</th><th>Recall</th><th>F1</th><th>n</th></tr></thead>
                  <tbody>
                    {f.per_label.map((l) => (
                      <tr key={l.label}><td>{l.label.replace(/_/g, " ")}</td><td>{pct(l.precision)}</td><td>{pct(l.recall)}</td><td>{pct(l.f1)}</td><td>{l.support}</td></tr>
                    ))}
                  </tbody>
                </table>
              </Card>
            ))}
          </div>
          <Card title={`Event type misses (${result.event_type_misses.length})`} wide>
            <table>
              <thead><tr><th>Sentence</th><th>Expected</th><th>Predicted</th></tr></thead>
              <tbody>
                {result.event_type_misses.map((m) => (
                  <tr key={m.text}><td>{m.text}</td><td>{m.expected.replace(/_/g, " ")}</td><td>{m.predicted.replace(/_/g, " ")}</td></tr>
                ))}
              </tbody>
            </table>
          </Card>
        </>
      )}
    </Page>
  );
}
