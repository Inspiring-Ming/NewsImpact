// How it works: the same four steps as the rest of the site, each with its rule and
// the live evidence behind it. To explain a new step, add one block here.
import { api } from "../../api/client";
import { State } from "../../shared/ui";
import { useApi } from "../../shared/useApi";
import { AllSettings } from "./AllSettings";
import { AnticipateStep } from "./AnticipateStep";
import { ConnectStep } from "./ConnectStep";
import { MonitorStep } from "./MonitorStep";
import { VerifyStep } from "./VerifyStep";

export function MethodPage() {
  const method = useApi(api.method);
  const calibration = useApi(api.calibration);
  return (
    <>
      <section className="hero compact">
        <h1>How it works</h1>
        <p className="lead">Four steps, each with a clear rule and the evidence behind it. No number is arbitrary: every setting has a stated reason and is checked against data as it accumulates.</p>
      </section>
      <State error={method.error} loading={method.loading}>
        {method.data && (
          <>
            <MonitorStep />
            <ConnectStep method={method.data} calibration={calibration.data} />
            <AnticipateStep method={method.data} calibration={calibration.data} />
            <VerifyStep method={method.data} />
            <AllSettings method={method.data} />
          </>
        )}
      </State>
    </>
  );
}
