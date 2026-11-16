// Ask NewsImpact about this event: answered by AI from our own data only (events, sources,
// stock moves, stored articles), checked before it is shown, with the links it relied on.
import { useState } from "react";
import { api, type S } from "../../api/client";
import { useApi } from "../../shared/useApi";
import type { EventData } from "./context";

const STATUS: Record<S["Answer"]["status"], string> = {
  answered: "", not_in_our_data: "Not in our data", checks_failed: "Held back by our checks",
  limit_reached: "Daily limit reached", unavailable: "Not available",
};

export function Ask({ company, card }: EventData) {
  const status = useApi(api.assistant);
  const suggestions = [
    `Why did ${company.name}'s stock move?`,
    `Is this ${card.event_type.toLowerCase()} confirmed, and by whom?`,
    `What other events did ${company.name} have recently?`,
  ];
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [answer, setAnswer] = useState<S["Answer"] | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function ask(q: string) {
    if (q.trim().length < 3) return;
    setQuestion(q); setBusy(true); setError(null); setAnswer(null);
    try { setAnswer(await api.ask(q, card.event_id)); }
    catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  }

  if (status.data && !status.data.available) {
    return <section className="card"><p className="muted">Ask is off: it needs the AI reading to be on (NI_LLM_PRESET).</p></section>;
  }
  return (
    <section className="card ask">
      <h3 className="card-kicker">Ask about this event</h3>
      <p className="small muted">Answered by AI only from NewsImpact's data: our events, their sources and stock moves, and the articles we stored. Every number is checked against that data; no investment advice.</p>
      <form className="ask-form" onSubmit={(e) => { e.preventDefault(); void ask(question); }}>
        <input value={question} maxLength={500} placeholder="Ask a question about this company or event"
               onChange={(e) => setQuestion(e.target.value)} aria-label="Your question" />
        <button className="primary" disabled={busy || question.trim().length < 3}>{busy ? "Looking it up…" : "Ask"}</button>
      </form>
      <div className="ask-suggestions">
        {suggestions.map((s) => <button key={s} type="button" className="small" disabled={busy} onClick={() => void ask(s)}>{s}</button>)}
      </div>
      {error && <p className="bad small">{error}</p>}
      {answer && (
        <div className="ask-answer">
          {STATUS[answer.status] && <p className="small muted"><b>{STATUS[answer.status]}</b></p>}
          <p>{answer.text}</p>
          {answer.sources.length > 0 && (
            <ul className="ask-sources small">
              {answer.sources.map((s) => <li key={s.url}><a href={s.url} target="_blank" rel="noreferrer">{s.title || s.url} ↗</a> <span className="muted">· {s.source}</span></li>)}
            </ul>
          )}
          {answer.tools_used.length > 0 && <p className="small muted">Looked up: {answer.tools_used.map((t) => t.replace(/_/g, " ")).join(" → ")}</p>}
        </div>
      )}
    </section>
  );
}
