// One storyline: conclusion, price chart, and every stage with its evidence.
import { api } from "../api/client";
import { PriceChart } from "../components/PriceChart";
import { Badge, Card, day, Loading, num, Page, pct } from "../components/ui";
import { useApi } from "../components/useApi";

export function StorylineDetail({ id }: { id: string }) {
  const story = useApi(() => api.storyline(id), [id]);
  const assessment = useApi(() => api.assessment(id), [id]);
  const prices = useApi(() => api.prices(id), [id]);
  const s = story.data;
  const a = assessment.data;
  const quotes = new Map((s?.events ?? []).map((e) => [e.stage, e]));

  return (
    <Page
      title={s ? `${s.ticker} · ${s.entity_name}` : "Storyline"}
      intro={s && <>{s.theme.replace(/_/g, " ")} · <Badge value={s.status} /> {a && <>· confidence <Badge value={a.confidence} /></>}</>}
      actions={<a href="#/storylines">← All storylines</a>}
    >
      <Loading error={story.error ?? assessment.error} loading={story.loading || assessment.loading} />
      {a && (
        <Card title="Conclusion" wide>
          <p className="conclusion">{a.conclusion}</p>
          {a.combined_reaction && (
            <p>
              <b>Combined reaction</b> (stages too close to separate): {a.combined_reaction.metric} ={" "}
              <b>{pct(a.combined_reaction.value, 1)}</b>, z = {num(a.combined_reaction.statistic)} <Badge value={a.combined_reaction.significant ? "consistent" : "not_significant"} />
            </p>
          )}
          <h3>Suggestions</h3>
          <ul>{a.suggestions.map((t) => <li key={t}>{t}</li>)}</ul>
          <p className="muted small">{a.disclaimer}</p>
        </Card>
      )}
      <Card title="Price reaction" wide>
        {prices.data ? (
          <PriceChart path={prices.data} stages={(a?.stages ?? []).map((st) => ({ day: day(st.published_at), label: st.stage_name.replace(/_/g, " ") }))} />
        ) : (
          <p className="muted">{prices.loading ? "Loading…" : "No price data connected (set NI_MARKET_DATA)."}</p>
        )}
      </Card>
      <h2 className="section">Stages and evidence</h2>
      <ol className="timeline">
        {(a?.stages ?? []).map((st) => (
          <li key={`${st.stage}-${st.published_at}`} className="stage">
            <div className="stage-head">
              <span className="date">{day(st.published_at)}</span>
              <b>{st.stage_name.replace(/_/g, " ")}</b>
              <Badge value={st.claim.status} />
              {st.overlaps_previous && <span className="badge neutral">overlaps previous stage</span>}
            </div>
            {quotes.get(st.stage) && <blockquote>{quotes.get(st.stage)!.summary}</blockquote>}
            <p className="small">
              Independent origins: {st.claim.origins.join(", ")} · reported by: {st.claim.outlets.join(", ")}
              {st.claim.authoritative && " · confirmed by the company or a filing"}
            </p>
            {st.decisions.length > 0 && (
              <table>
                <thead><tr><th>Who decides</th><th>Decision expected</th><th>Where it shows</th><th>Expected</th><th>Evidence</th><th>Verdict</th></tr></thead>
                <tbody>
                  {st.decisions.map((d) => (
                    <tr key={d.actor + d.decision}>
                      <td>{d.actor.replace(/_/g, " ")}</td>
                      <td>{d.decision}</td>
                      <td>{d.channel?.replace(/_/g, " ") ?? "real economy"}</td>
                      <td>{d.expected}</td>
                      <td className="small">{d.evidence ? `${d.evidence.metric} = ${num(d.evidence.value, 3)} (z ${num(d.evidence.statistic)})` : "–"}</td>
                      <td><Badge value={d.verdict} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </li>
        ))}
      </ol>
      {a && (
        <details className="provenance">
          <summary>Provenance (how to reproduce this result)</summary>
          <p className="small">Assessed {new Date(a.as_of).toLocaleString()} with {a.model_version}</p>
          <table><tbody>
            {Object.entries(a.provenance.components).map(([k, v]) => <tr key={k}><td>{k}</td><td className="mono">{v}</td></tr>)}
            {Object.entries(a.provenance.reference_data).map(([k, v]) => <tr key={k}><td>{k}</td><td className="mono">{v}</td></tr>)}
          </tbody></table>
        </details>
      )}
    </Page>
  );
}
