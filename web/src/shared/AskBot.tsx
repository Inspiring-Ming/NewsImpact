// Ask NewsImpact: a chat assistant on every page. Answers come from AI that may only look up
// NewsImpact's own data (events, sources, stock moves, stored articles); every answer is
// checked on the server before it is shown, with the links it relied on.
// On an event page it knows which event is open; suggested questions come from live data.
import { useEffect, useRef, useState } from "react";
import { api, type S } from "../api/client";
import { eventLabel } from "./labels";

const STATUS: Record<S["Answer"]["status"], string> = {
  answered: "", not_in_our_data: "Not in our data", checks_failed: "Held back by our checks",
  limit_reached: "Daily limit reached", unavailable: "Not available",
};
const STEP: Record<string, string> = {
  find_company: "found the company", list_events: "listed events",
  get_event: "read the event", search_articles: "searched articles",
};

type Message = { id: number; question: string; answer?: S["Answer"]; error?: string };

export function AskBot({ eventId }: { eventId?: string }) {
  const [available, setAvailable] = useState(false);
  const [open, setOpen] = useState(false);
  const [question, setQuestion] = useState("");
  const [thread, setThread] = useState<Message[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [context, setContext] = useState<string | null>(null);
  const input = useRef<HTMLInputElement>(null);
  const end = useRef<HTMLDivElement>(null);
  const busy = thread.some((m) => !m.answer && !m.error);

  useEffect(() => { api.assistant().then((s) => setAvailable(s.available)).catch(() => setAvailable(false)); }, []);
  useEffect(() => setThread([]), [eventId]); // a new event (or the home page) starts a new conversation

  // Suggested questions from what is live right now: the open event, or this week's biggest move.
  useEffect(() => {
    if (!open) return;
    let live = true;
    const load = eventId
      ? api.eventSummary(eventId).then((c) => {
          const e = c.events[0];
          if (!live) return;
          setContext(`${c.name} · ${eventLabel(e)}`);
          setSuggestions([`Why did ${c.name}'s stock move?`, `Who reported this ${eventLabel(e).toLowerCase()}, and is it confirmed?`,
                          `What other events did ${c.name} have recently?`]);
        })
      : api.companies().then((cs) => {
          const moves = cs.flatMap((c) => c.events.filter((e) => e.stock_move != null).map((e) => ({ c, m: Math.abs(e.stock_move!) })));
          const top = moves.sort((a, b) => b.m - a.m)[0]?.c;
          if (!live) return;
          setContext(null);
          setSuggestions([...(top ? [`Why did ${top.name}'s stock move?`] : []),
                          "Which events this week are confirmed?", "Any takeover news about Australian companies?"]);
        });
    load.catch(() => live && setSuggestions([]));
    input.current?.focus();
    return () => { live = false; };
  }, [open, eventId]);

  useEffect(() => { end.current?.scrollIntoView({ block: "end", behavior: "smooth" }); }, [thread]);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  async function ask(q: string) {
    q = q.trim();
    if (q.length < 3 || busy) return;
    const id = Date.now();
    setQuestion("");
    setThread((t) => [...t, { id, question: q }]);
    const done = (patch: Partial<Message>) => setThread((t) => t.map((m) => (m.id === id ? { ...m, ...patch } : m)));
    try { done({ answer: await api.ask(q, eventId) }); }
    catch (e) { done({ error: e instanceof Error ? e.message : String(e) }); }
  }

  if (!available) return null;
  return (
    <>
      {open && (
        <section className="bot-panel" role="dialog" aria-label="Ask NewsImpact">
          <header className="bot-head">
            <BotFace />
            <div>
              <b>Ask NewsImpact</b>
              <span>Answers only from our live data · every number checked · no advice</span>
            </div>
            <button className="bot-close" onClick={() => setOpen(false)} aria-label="Close">×</button>
          </header>
          {context && <p className="bot-context">Looking at: <b>{context}</b></p>}
          <div className="bot-thread">
            {thread.length === 0 && (
              <div className="bot-msg bot">
                <p>Hi! Ask me what happened to a company, who reported it, or how the stock moved. I look it up in NewsImpact's events and articles and show you the sources.</p>
              </div>
            )}
            {thread.map((m) => (
              <div key={m.id}>
                <div className="bot-msg me"><p>{m.question}</p></div>
                <div className="bot-msg bot">
                  {!m.answer && !m.error && <p className="bot-typing" aria-label="Looking it up"><i /><i /><i /> <span>Looking it up…</span></p>}
                  {m.error && <p className="bad">{m.error}</p>}
                  {m.answer && <Reply answer={m.answer} />}
                </div>
              </div>
            ))}
            <div ref={end} />
          </div>
          {thread.length === 0 && suggestions.length > 0 && (
            <div className="bot-suggestions">
              {suggestions.map((s) => <button key={s} type="button" onClick={() => void ask(s)}>{s}</button>)}
            </div>
          )}
          <form className="bot-form" onSubmit={(e) => { e.preventDefault(); void ask(question); }}>
            <input ref={input} value={question} maxLength={500} placeholder={eventId ? "Ask about this event…" : "Ask about any company or event…"}
                   onChange={(e) => setQuestion(e.target.value)} aria-label="Your question" />
            <button className="primary" disabled={busy || question.trim().length < 3} aria-label="Send">↑</button>
          </form>
        </section>
      )}
      <button className={`bot-launcher${open ? " open" : ""}`} onClick={() => setOpen((o) => !o)}
              aria-expanded={open} aria-label={open ? "Close Ask NewsImpact" : "Open Ask NewsImpact"}>
        <BotFace />
        <span>{open ? "Close" : "Ask NewsImpact"}</span>
      </button>
    </>
  );
}

function Reply({ answer }: { answer: S["Answer"] }) {
  return (
    <>
      {STATUS[answer.status] && <span className={`bot-tag ${answer.status}`}>{STATUS[answer.status]}</span>}
      <p>{answer.text}</p>
      {answer.sources.length > 0 && (
        <ul className="bot-sources">
          {answer.sources.map((s) => (
            <li key={s.url}><a href={s.url} target="_blank" rel="noreferrer"><b>{s.source}</b>{s.title || s.url} ↗</a></li>
          ))}
        </ul>
      )}
      {answer.tools_used.length > 0 && (
        <p className="bot-steps">{answer.tools_used.map((t, i) => <span key={i}>{STEP[t] ?? t.replace(/_/g, " ")}</span>)}</p>
      )}
    </>
  );
}

function BotFace() {
  return (
    <svg className="bot-face" viewBox="0 0 32 32" aria-hidden="true">
      <circle cx="16" cy="16" r="15" className="bot-face-bg" />
      <line x1="16" y1="3" x2="16" y2="7" className="bot-face-line" />
      <circle cx="16" cy="3" r="1.6" className="bot-face-dot" />
      <rect x="7.5" y="9" width="17" height="14" rx="5" className="bot-face-head" />
      <circle cx="12.5" cy="15.5" r="1.8" className="bot-face-eye" />
      <circle cx="19.5" cy="15.5" r="1.8" className="bot-face-eye" />
      <path d="M13 19.5 q3 2 6 0" className="bot-face-line" />
    </svg>
  );
}
