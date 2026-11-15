// The workflow with live numbers: the product's idea shown as what it has actually done.
import { api } from "../../api/client";
import { STEPS } from "../../shared/steps";
import { useApi } from "../../shared/useApi";

export function PipelineBanner({ refreshKey }: { refreshKey: number }) {
  const { data } = useApi(api.pipeline, [refreshKey]);
  const byStep = new Map((data?.steps ?? []).map((s) => [s.step, s]));
  return (
    <ol className="pipeline" aria-label="What NewsImpact has done so far">
      {STEPS.map((s) => {
        const live = byStep.get(s.id);
        return (
          <li key={s.id} className={`pipe step-${s.id}`}>
            <div className="pipe-head"><span className="step-n">{s.n}</span>{s.name}</div>
            <div className="pipe-num">{live ? live.headline.toLocaleString() : "–"}</div>
            <div className="pipe-text">{live?.detail ?? s.verb}</div>
          </li>
        );
      })}
    </ol>
  );
}
