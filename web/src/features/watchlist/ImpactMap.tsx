// Impact map: every event with a measured stock move, by sector. Position = how much
// better or worse than its market the stock did; dot size = number of sources;
// blue = unusual move (also labelled with the company name, so colour is never the only
// cue); faded = no update for RECENT_DAYS, so what is happening now stands out; a gentle
// pulse marks events updated in the last 24 hours. Hover or keyboard focus shows a card.
// Filters fade out the events that do not match (the axes stay put, so positions compare).
import { useState } from "react";
import type { S } from "../../api/client";
import { eventLabel, pct, SECTOR_SHORT, SECTORS, vsWords } from "../../shared/labels";
import { Term } from "../../shared/Term";

const W = 1000, ROW = 30, PAD = { l: 96, r: 24, t: 10, b: 34 };
const RECENT_DAYS = 30; // matches the shortest event window (earnings, job cuts)
const DAY = 86_400_000;
// "Alphabet (Google)" -> "Alphabet": labels stay short; the tooltip has the full name.
const shortName = (name: string) => name.replace(/\s*\(.*\)$/, "");
const lastUpdate = (e: S["EventCard"]) => Math.max(...e.updates.map((u) => Date.parse(u.published_at)));

interface Dot { c: S["CompanyCard"]; e: S["EventCard"] }

const SHOW: { id: string; label: string; test: (d: Dot, now: number) => boolean }[] = [
  { id: "all", label: "All", test: () => true },
  { id: "confirmed", label: "Confirmed", test: (d) => d.e.verified },
  { id: "unusual", label: "Unusual moves", test: (d) => d.e.stock_move_unusual },
  { id: "recent", label: `Updated in ${RECENT_DAYS} days`, test: (d, now) => now - lastUpdate(d.e) < RECENT_DAYS * DAY },
];

export function ImpactMap({ companies }: { companies: S["CompanyCard"][] }) {
  const [hover, setHover] = useState<{ d: Dot; x: number; y: number } | null>(null);
  const [show, setShow] = useState("all");
  const [type, setType] = useState("");
  const dots: Dot[] = companies.flatMap((c) => c.events.filter((e) => e.stock_move != null).map((e) => ({ c, e })));
  if (!dots.length) return null;
  const sectors = [...new Set(dots.map((d) => d.c.sector))].sort();
  const H = PAD.t + sectors.length * ROW + PAD.b;
  const step = 0.05;
  const span = Math.max(step, Math.ceil(Math.max(...dots.map((d) => Math.abs(d.e.stock_move!))) / step) * step);
  const x = (v: number) => PAD.l + ((v + span) / (2 * span)) * (W - PAD.l - PAD.r);
  const y = (sector: string) => PAD.t + sectors.indexOf(sector) * ROW + ROW / 2;
  const r = (sources: number) => 4 + Math.min(sources, 6);
  // Labels: one per company (unusual moves only), biggest move first. Each tries above, below,
  // right, then left of its dot and takes the first spot that overlaps no other label or dot;
  // with none free it stays unlabelled (the hover card still names it).
  type Box = { x0: number; x1: number; y0: number; y1: number };
  const CH = 6.4, LH = 12;
  const hits = (a: Box, b: Box) => a.x0 < b.x1 && b.x0 < a.x1 && a.y0 < b.y1 && b.y0 < a.y1;
  const dotBoxes = dots.map((d) => {
    const cx = x(d.e.stock_move!), cy = y(d.c.sector), rr = r(d.e.sources);
    return { id: d.e.event_id, b: { x0: cx - rr, x1: cx + rr, y0: cy - rr, y1: cy + rr } };
  });
  const taken: Box[] = [];
  const labels = new Map<string, { x: number; y: number; anchor: "start" | "middle" | "end" }>();
  const named = new Set<string>();
  for (const d of dots.filter((d) => d.e.stock_move_unusual).sort((a, b) => Math.abs(b.e.stock_move!) - Math.abs(a.e.stock_move!))) {
    if (named.has(d.c.ticker)) continue;
    named.add(d.c.ticker);
    const name = shortName(d.c.name), w = name.length * CH, cx = x(d.e.stock_move!), cy = y(d.c.sector), rr = r(d.e.sources);
    const spots = [
      { x: cx, y: cy - rr - 4, anchor: "middle" as const, b: { x0: cx - w / 2, x1: cx + w / 2, y0: cy - rr - 4 - LH, y1: cy - rr - 2 } },
      { x: cx, y: cy + rr + 12, anchor: "middle" as const, b: { x0: cx - w / 2, x1: cx + w / 2, y0: cy + rr + 1, y1: cy + rr + 2 + LH } },
      { x: cx + rr + 4, y: cy + 4, anchor: "start" as const, b: { x0: cx + rr + 3, x1: cx + rr + 4 + w, y0: cy - LH / 2, y1: cy + LH / 2 } },
      { x: cx - rr - 4, y: cy + 4, anchor: "end" as const, b: { x0: cx - rr - 4 - w, x1: cx - rr - 3, y0: cy - LH / 2, y1: cy + LH / 2 } },
    ];
    const free = spots.find((sp) => sp.b.x0 >= PAD.l - 4 && sp.b.x1 <= W - PAD.r + 4 && sp.b.y0 >= 0
      && !taken.some((t) => hits(t, sp.b)) && !dotBoxes.some((o) => o.id !== d.e.event_id && hits(o.b, sp.b)));
    if (free) { taken.push(free.b); labels.set(d.e.event_id, free); }
  }
  const now = Date.now();
  const test = SHOW.find((f) => f.id === show)!.test;
  const shown = (d: Dot) => test(d, now) && (!type || d.e.event_type === type);
  const types = [...new Set(dots.map((d) => d.e.event_type))].sort();
  const nShown = dots.filter(shown).length;
  const recent = (d: Dot) => now - lastUpdate(d.e) < RECENT_DAYS * DAY;
  const fresh = (d: Dot) => now - lastUpdate(d.e) < DAY;
  const nRecent = dots.filter(recent).length;
  const nFresh = dots.filter(fresh).length;
  const open = (d: Dot) => (window.location.hash = `#/event/${d.e.event_id}`);
  const describe = (d: Dot) => `${d.c.name}, ${eventLabel(d.e)}: ${pct(d.e.stock_move!)} ${vsWords(d.e.stock_move!, d.c.index_name)}, ` +
    `${d.e.sources} ${d.e.sources === 1 ? "source" : "sources"}, ${d.e.verified ? "confirmed" : "not yet confirmed"}. Open event`;
  const ticks = Array.from({ length: Math.round((2 * span) / step) + 1 }, (_, i) => -span + i * step);
  return (
    <figure className="card impact-map">
      <figcaption className="map-head">
        <h2><Term id="map" /> <span className="small muted">{dots.length} events · {nRecent} updated in the last {RECENT_DAYS} days</span></h2>
        <span className="small muted map-legend">
          <span className="swatch unusual" /> Unusual move <span className="swatch normal" /> Normal range · bigger dot = more sources · faded = no update for {RECENT_DAYS} days
          {nFresh > 0 && <> · <span className="swatch fresh" /> pulsing = updated in the last 24 h ({nFresh})</>}
        </span>
      </figcaption>
      <div className="map-filters" role="group" aria-label="Show on the map">
        {SHOW.map((f) => (
          <button key={f.id} type="button" className={`chip${show === f.id ? " on" : ""}`} aria-pressed={show === f.id}
                  onClick={() => setShow(f.id)}>{f.label}</button>
        ))}
        <select value={type} onChange={(ev) => setType(ev.target.value)} aria-label="Event type">
          <option value="">Every event type</option>
          {types.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <span className="small muted" aria-live="polite">showing {nShown} of {dots.length}</span>
      </div>
      <div className="map-body">
        <div className="map-canvas">
        <svg viewBox={`0 0 ${W} ${H}`} role="group" aria-label="Impact map: stock moves against the market for each event, by sector. Each dot is a link to its event">
          {sectors.map((s) => (
            <g key={s}>
              <line className="row-line" x1={PAD.l} x2={W - PAD.r} y1={y(s)} y2={y(s)} />
              <circle className={`sector-key sec-${SECTORS.indexOf(s) + 1}`} cx={PAD.l - 4} cy={y(s)} r={3} />
              <text className="axis" x={PAD.l - 10} y={y(s) + 4} textAnchor="end">{SECTOR_SHORT[s] ?? s}</text>
            </g>
          ))}
          {ticks.map((t) => (
            <g key={t}>
              <line className={Math.abs(t) < 1e-9 ? "zero" : "grid"} x1={x(t)} x2={x(t)} y1={PAD.t} y2={H - PAD.b} />
              <text className="axis" x={x(t)} y={H - PAD.b + 16} textAnchor="middle">{Math.abs(t) < 1e-9 ? "0" : pct(t, 0)}</text>
            </g>
          ))}
          <text className="axis" x={PAD.l} y={H - 4}>← worse than its market</text>
          <text className="axis" x={W - PAD.r} y={H - 4} textAnchor="end">better than its market →</text>
          {[...dots].sort((a, b) => b.e.sources - a.e.sources).map((d) => {
            const cx = x(d.e.stock_move!), cy = y(d.c.sector);
            return (
              <g key={d.e.event_id} className={`dot-g${recent(d) ? "" : " old"}${fresh(d) ? " fresh" : ""}${shown(d) ? "" : " out"}`} onClick={() => open(d)}
                 role="link" tabIndex={shown(d) ? 0 : -1} aria-hidden={!shown(d)} aria-label={describe(d)}
                 onKeyDown={(ev) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); open(d); } }}
                 onMouseEnter={() => setHover({ d, x: cx, y: cy })} onMouseLeave={() => setHover(null)}
                 onFocus={() => setHover({ d, x: cx, y: cy })} onBlur={() => setHover(null)}>
                <circle className="hit" cx={cx} cy={cy} r={r(d.e.sources) + 6} />
                {fresh(d) && <circle className={`pulse ${d.e.stock_move_unusual ? "unusual" : "normal"}`} cx={cx} cy={cy} r={r(d.e.sources)} />}
                <circle className={`dot ${d.e.stock_move_unusual ? "unusual" : "normal"}`} cx={cx} cy={cy} r={r(d.e.sources)} />
                {labels.has(d.e.event_id) && (() => {
                  const l = labels.get(d.e.event_id)!;
                  return <text className="dot-label" x={l.x} y={l.y} textAnchor={l.anchor}>{shortName(d.c.name)}</text>;
                })()}
              </g>
            );
          })}
        </svg>
        {hover && (() => {
          const { d, x: hx, y: hy } = hover, m = d.e.stock_move!;
          // Kept inside the map: anchored left/right near the edges, below the dot in the top rows.
          const side = hx / W < 0.25 ? "left" : hx / W > 0.75 ? "right" : "mid";
          return (
            <div className={`map-tip ${side}${hy / H < 0.35 ? " below" : ""}`} role="tooltip"
                 style={{ left: `${(hx / W) * 100}%`, top: `${(hy / H) * 100}%` }}>
              <div className="tip-head"><b>{d.c.name}</b> <span className="tip-ticker">{d.c.ticker}</span></div>
              <div className="tip-event">{eventLabel(d.e)}</div>
              <div className="tip-move"><b className={m < 0 ? "bad" : "good"}>{pct(m)}</b> {vsWords(m, d.c.index_name)}</div>
              <div className="tip-meta">
                {d.e.sources} {d.e.sources === 1 ? "source" : "sources"} · <span className={d.e.verified ? "good" : "warn"}>{d.e.verified ? "✓ confirmed" : "○ not yet confirmed"}</span>
              </div>
              <div className="tip-meta">{d.e.stock_move_period} · {d.e.stock_move_unusual ? "unusual move" : "normal range"} · last update {new Date(lastUpdate(d.e)).toLocaleDateString()}</div>
            </div>
          );
        })()}
        </div>
      </div>
    </figure>
  );
}
