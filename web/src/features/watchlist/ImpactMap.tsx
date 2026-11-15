// Impact map: every event with a measured stock move, by sector. Position = how much
// better or worse than its market the stock did; dot size = number of sources;
// blue = unusual move (also labelled with its ticker, so colour is never the only cue).
import { useState } from "react";
import type { S } from "../../api/client";
import { pct, SECTOR_SHORT, vsWords } from "../../shared/labels";
import { Term } from "../../shared/Term";

const W = 1000, ROW = 30, PAD = { l: 96, r: 24, t: 10, b: 34 };

interface Dot { c: S["CompanyCard"]; e: S["EventCard"] }

export function ImpactMap({ companies }: { companies: S["CompanyCard"][] }) {
  const [hover, setHover] = useState<{ d: Dot; x: number; y: number } | null>(null);
  const dots: Dot[] = companies.flatMap((c) => c.events.filter((e) => e.stock_move != null).map((e) => ({ c, e })));
  if (!dots.length) return null;
  const sectors = [...new Set(dots.map((d) => d.c.sector))].sort();
  const H = PAD.t + sectors.length * ROW + PAD.b;
  const step = 0.05;
  const span = Math.max(step, Math.ceil(Math.max(...dots.map((d) => Math.abs(d.e.stock_move!))) / step) * step);
  const x = (v: number) => PAD.l + ((v + span) / (2 * span)) * (W - PAD.l - PAD.r);
  const y = (sector: string) => PAD.t + sectors.indexOf(sector) * ROW + ROW / 2;
  const r = (sources: number) => 4 + Math.min(sources, 6);
  // Labels go above their dot; one that would overlap a neighbour's label in the same row goes below.
  const placed: { sector: string; x: number }[] = [];
  const below = new Set<string>();
  for (const d of dots.filter((d) => d.e.stock_move_unusual).sort((a, b) => a.e.stock_move! - b.e.stock_move!)) {
    const cx = x(d.e.stock_move!);
    const near = placed.some((p) => p.sector === d.c.sector && Math.abs(p.x - cx) < 44);
    if (near) below.add(d.e.event_id); else placed.push({ sector: d.c.sector, x: cx });
  }
  const ticks = Array.from({ length: Math.round((2 * span) / step) + 1 }, (_, i) => -span + i * step);
  return (
    <figure className="card impact-map">
      <figcaption className="map-head">
        <h2><Term id="map" /></h2>
        <span className="small muted map-legend">
          <span className="swatch unusual" /> Unusual move <span className="swatch normal" /> Normal range · bigger dot = more sources
        </span>
      </figcaption>
      <div className="map-body">
        <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Stock moves against the market for each event, by sector">
          {sectors.map((s) => (
            <g key={s}>
              <line className="row-line" x1={PAD.l} x2={W - PAD.r} y1={y(s)} y2={y(s)} />
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
              <g key={d.e.event_id} className="dot-g" onClick={() => (window.location.hash = `#/event/${d.e.event_id}`)}
                 onMouseEnter={() => setHover({ d, x: cx, y: cy })} onMouseLeave={() => setHover(null)}>
                <circle className="hit" cx={cx} cy={cy} r={r(d.e.sources) + 6} />
                <circle className={`dot ${d.e.stock_move_unusual ? "unusual" : "normal"}`} cx={cx} cy={cy} r={r(d.e.sources)} />
                {d.e.stock_move_unusual && (
                  <text className="dot-label" x={cx} textAnchor="middle"
                        y={below.has(d.e.event_id) ? cy + r(d.e.sources) + 12 : cy - r(d.e.sources) - 4}>{d.c.ticker.replace(".AX", "")}</text>
                )}
              </g>
            );
          })}
        </svg>
        {hover && (
          <div className="map-tip" style={{ left: `${(hover.x / W) * 100}%`, top: `${(hover.y / H) * 100}%` }}>
            <b>{hover.d.c.name}</b> · {hover.d.e.event_type}
            <div>{pct(hover.d.e.stock_move!)} · {vsWords(hover.d.e.stock_move!, hover.d.c.index_name)}</div>
            <div className="muted">{hover.d.e.stock_move_period} · {hover.d.e.stock_move_unusual ? "unusual move" : "normal range"} · {hover.d.e.sources} {hover.d.e.sources === 1 ? "source" : "sources"}</div>
          </div>
        )}
      </div>
    </figure>
  );
}
