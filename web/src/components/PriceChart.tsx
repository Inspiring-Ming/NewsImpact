// Stock vs. benchmark (both rebased to 100) with a marker for every storyline stage.
import type { S } from "../api/client";

const W = 720, H = 240, PAD = { l: 44, r: 12, t: 16, b: 28 };

export function PriceChart({ path, stages }: {
  path: S["PricePath"]; stages: { day: string; label: string }[];
}) {
  const pts = path.points;
  if (pts.length < 2) return <p className="muted">Not enough price data yet.</p>;
  const values = pts.flatMap((p) => [p.stock, p.benchmark]);
  const lo = Math.min(...values), hi = Math.max(...values);
  const x = (i: number) => PAD.l + (i / (pts.length - 1)) * (W - PAD.l - PAD.r);
  const y = (v: number) => PAD.t + (1 - (v - lo) / (hi - lo || 1)) * (H - PAD.t - PAD.b);
  const line = (key: "stock" | "benchmark") =>
    pts.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p[key]).toFixed(1)}`).join("");
  const indexOf = (d: string) => {
    const i = pts.findIndex((p) => p.day >= d);
    return i < 0 ? pts.length - 1 : i;
  };
  const ticks = [lo, (lo + hi) / 2, hi];
  return (
    <figure className="chart">
      <svg viewBox={`0 0 ${W} ${H}`} role="img"
           aria-label={`${path.ticker} versus ${path.benchmark}, rebased to 100`}>
        {ticks.map((t) => (
          <g key={t}>
            <line className="grid" x1={PAD.l} x2={W - PAD.r} y1={y(t)} y2={y(t)} />
            <text className="axis" x={PAD.l - 6} y={y(t) + 4} textAnchor="end">{t.toFixed(0)}</text>
          </g>
        ))}
        {stages.map((s, n) => {
          const i = indexOf(s.day);
          return (
            <g key={`${s.day}-${n}`}>
              <line className="marker" x1={x(i)} x2={x(i)} y1={PAD.t} y2={H - PAD.b} />
              <text className="marker-label" x={x(i) + 4} y={PAD.t + 12 + (n % 3) * 13}>{s.label}</text>
            </g>
          );
        })}
        <path className="line benchmark" d={line("benchmark")} />
        <path className="line stock" d={line("stock")} />
        <text className="axis" x={PAD.l} y={H - 8}>{pts[0].day}</text>
        <text className="axis" x={W - PAD.r} y={H - 8} textAnchor="end">{pts[pts.length - 1].day}</text>
      </svg>
      <figcaption>
        <span className="key stock" /> {path.ticker} &nbsp;
        <span className="key benchmark" /> {path.benchmark} (market) · both rebased to 100 · vertical lines = storyline stages
      </figcaption>
    </figure>
  );
}
