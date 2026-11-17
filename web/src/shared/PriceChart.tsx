// Share price vs. its market (both rebased to 100), with a numbered marker for every update.
import type { S } from "../api/client";

const W = 760, H = 260, PAD = { l: 40, r: 16, t: 24, b: 30 };

export function PriceChart({ path, stages, benchmarkName, window }: {
  path: S["PricePath"]; stages: { day: string; label: string }[]; benchmarkName: string;
  /** The days the reaction is measured over, shaded; past the last close = still to come. */
  window?: { from: string; to: string; label: string };
}) {
  const pts = path.points;
  if (pts.length < 2) return <p className="muted">Not enough price history yet.</p>;
  const values = pts.flatMap((p) => [p.stock, p.benchmark]);
  const lo = Math.min(...values), hi = Math.max(...values);
  const x = (i: number) => PAD.l + (i / (pts.length - 1)) * (W - PAD.l - PAD.r);
  const y = (v: number) => PAD.t + (1 - (v - lo) / (hi - lo || 1)) * (H - PAD.t - PAD.b);
  const line = (key: "stock" | "benchmark") =>
    pts.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p[key]).toFixed(1)}`).join("");
  const at = (d: string) => { const i = pts.findIndex((p) => p.day >= d); return i < 0 ? pts.length - 1 : i; };
  const last = pts[pts.length - 1];
  // Stages on the same trading day share one marker ("2·3") instead of hiding each other.
  const markers: { i: number; nums: number[] }[] = [];
  stages.forEach((s, n) => {
    const i = at(s.day);
    const same = markers.find((m) => m.i === i);
    if (same) same.nums.push(n + 1); else markers.push({ i, nums: [n + 1] });
  });
  return (
    <figure className="chart">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${path.ticker} share price compared with the ${benchmarkName}`}>
        {[lo, (lo + hi) / 2, hi].map((t) => (
          <g key={t}>
            <line className="grid" x1={PAD.l} x2={W - PAD.r} y1={y(t)} y2={y(t)} />
            <text className="axis" x={PAD.l - 6} y={y(t) + 4} textAnchor="end">{t.toFixed(0)}</text>
          </g>
        ))}
        {window && (() => {
          const x0 = x(at(window.from)), future = window.to > last.day;
          const x1 = future ? W - PAD.r : x(at(window.to));
          return (
            <g className={`measure-window${future ? " pending" : ""}`}>
              <rect x={x0} y={PAD.t} width={Math.max(4, x1 - x0)} height={H - PAD.t - PAD.b} />
              <text x={Math.min(x0 + 4, W - PAD.r - 4)} y={H - PAD.b - 6} textAnchor={x0 > W * 0.7 ? "end" : "start"}
                    dx={x0 > W * 0.7 ? Math.max(4, x1 - x0) - 8 : 0}>{window.label}</text>
            </g>
          );
        })()}
        {markers.map(({ i, nums }) => (
          <g key={i}>
            <line className="marker" x1={x(i)} x2={x(i)} y1={PAD.t - 8} y2={H - PAD.b} />
            <rect className="marker-dot" x={x(i) - 6 - nums.length * 4} y={PAD.t - 17} rx={9}
                  width={12 + nums.length * 8} height={18} />
            <text className="marker-num" x={x(i)} y={PAD.t - 4} textAnchor="middle">{nums.join("·")}</text>
          </g>
        ))}
        <path className="line benchmark" d={line("benchmark")} />
        <path className="line stock" d={line("stock")} />
        <text className="axis" x={PAD.l} y={H - 8}>{pts[0].day}</text>
        <text className="axis" x={W - PAD.r} y={H - 8} textAnchor="end">{last.day}</text>
      </svg>
      <figcaption>
        <span className="key stock" /> {path.ticker} share price <span className="key benchmark" /> {benchmarkName} ·
        both start at 100, so the gap between the lines is how much the stock did better or worse · numbers = updates{window ? " · shaded = the days the reaction is measured over" : ""}
      </figcaption>
    </figure>
  );
}
