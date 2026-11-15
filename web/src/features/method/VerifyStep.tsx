// Step 4 - the two checks behind every conclusion, and how accurate our reading of news is.
import { useState } from "react";
import { api, type S } from "../../api/client";
import { humanize } from "../../shared/labels";
import { Fact, State } from "../../shared/ui";
import { StepBlock } from "./StepBlock";

const FIELD_NAMES: Record<string, string> = {
  event_type: "Recognising the event", attribution_kind: "Knowing the source",
  is_speculative: "Rumour or fact", is_background: "News or background",
};

type Rec = Record<string, unknown>;

export function VerifyStep({ method }: { method: S["Method"] }) {
  const m = method.methodology as Rec;
  const market = (m.market ?? {}) as Rec;
  const validation = (m.validation ?? {}) as Rec;
  const windows = (market.windows ?? {}) as Record<string, [number, number]>;
  const price = windows.price ?? [0, 1];
  const [result, setResult] = useState<S["Evaluation"] | null>(null);
  const [state, setState] = useState<{ busy: boolean; error: string | null }>({ busy: false, error: null });
  const run = () => {
    setState({ busy: true, error: null });
    api.evaluation().then((r) => { setResult(r); setState({ busy: false, error: null }); })
      .catch((e: Error) => setState({ busy: false, error: e.message }));
  };
  return (
    <StepBlock id="verify"
      what="Every event and every predicted reaction is checked against evidence that does not come from the original article: other outlets, the company itself, and real market prices."
      rules={[
        <>Is the event true? <b>{String(validation.corroborating_origins ?? 2)} independent sources</b> must agree;
          it counts as verified with {String(validation.confirming_origins ?? 3)} sources, or when the company or a regulatory filing confirms it.</>,
        <>Did the market react? The share price is compared with its whole market (S&amp;P 500 for US, ASX 200 for Australia)
          from the event day to {price[1]} day(s) after. News after the 4 pm close counts from the next trading day.</>,
        <>A move counts as a clear reaction only if it is big enough to happen on <b>fewer than 1 normal day in 20</b>.</>,
        <>Confidence is <b>high</b> only when the events are verified and the market confirmed at least {Math.round(Number(validation.high_support ?? 0.6) * 100)}% of the tested predictions.</>,
      ]}>
      <p className="small">How accurately do we read the news? Each method is scored on {result?.examples ?? "the same"} hand-checked sentences before we trust it.</p>
      <button className="primary small" onClick={run} disabled={state.busy}>{state.busy ? "Checking…" : "Run the accuracy check"}</button>
      <State error={state.error}>
        {result && (
          <>
            <div className="facts">
              {result.fields.map((f) => (
                <Fact key={f.field} label={FIELD_NAMES[f.field] ?? humanize(f.field)} value={`${Math.round(f.accuracy * 100)}%`}
                      tone={f.accuracy >= 0.9 ? "good" : f.accuracy >= 0.75 ? "ok" : "warn"} />
              ))}
            </div>
            <p className="small muted">Language model in use: {method.llm_preset_in_use === "off" ? "none (word lists only)" : method.llm_preset_in_use}</p>
          </>
        )}
      </State>
    </StepBlock>
  );
}
