// Small inline visuals used across pages, so a number is also seen at a glance.
// Every visual sits next to its number in words: colour is never the only cue.
import type { Tone } from "./labels";

/** A move against the market as a bar from a centre line: left = worse, right = better. */
export function MoveBar({ value, unusual, span = 0.2 }: { value: number; unusual: boolean; span?: number }) {
  const w = Math.min(Math.abs(value) / span, 1) * 50;
  const tone = unusual ? (value < 0 ? "bad" : "good") : "neutral";
  return (
    <span className="movebar" aria-hidden="true">
      <span className={`movebar-fill ${tone}`} style={value < 0 ? { right: "50%", width: `${w}%` } : { left: "50%", width: `${w}%` }} />
    </span>
  );
}

/** A ratio to normal (e.g. trading volume 3.7×) with a tick at 1× = a normal day. */
export function RatioBar({ value, max = 5 }: { value: number; max?: number }) {
  return (
    <span className="ratiobar" aria-hidden="true">
      <span className={`ratiobar-fill ${value >= 2 ? "warn" : "neutral"}`} style={{ width: `${Math.min(value / max, 1) * 100}%` }} />
      <span className="ratiobar-tick" style={{ left: `${100 / max}%` }} />
    </span>
  );
}

/** A share from 0 to 1 as a filled bar. */
export function Meter({ value, tone }: { value: number; tone: Tone }) {
  return (
    <span className="meter" aria-hidden="true">
      <span className={`meter-fill ${tone}`} style={{ width: `${Math.max(0, Math.min(value, 1)) * 100}%` }} />
    </span>
  );
}

/** One dot per item, up to `max` (sources reporting, updates so far...). */
export function Dots({ n, of, max = 6 }: { n: number; of?: number; max?: number }) {
  const total = Math.min(of ?? n, max);
  return (
    <span className="dots" aria-hidden="true">
      {Array.from({ length: total }, (_, i) => <span key={i} className={i < n ? "on" : "off"} />)}
      {(of ?? n) > max && <span className="more">+</span>}
    </span>
  );
}

/** Source reliability: a newspaper's 75% starting estimate is already good evidence. */
export const reliabilityTone = (x: number): Tone => (x >= 0.75 ? "good" : x >= 0.6 ? "warn" : "bad");

/** Stock minus its index at each close, as a small line: 0 = the close before the event
 *  (dashed), the event day marked. Drawn in on first view. */
export function Sparkline({ values, eventAt, label }: { values: readonly number[]; eventAt?: number | null; label: string }) {
  if (values.length < 2) return null;
  const W = 96, H = 30, P = 3;
  const span = Math.max(0.02, ...values.map(Math.abs));
  const x = (i: number) => P + (i / (values.length - 1)) * (W - 2 * P);
  const y = (v: number) => H / 2 - (v / span) * (H / 2 - P);
  const d = values.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join("");
  const last = values[values.length - 1];
  return (
    <svg className={`spark ${last < 0 ? "bad" : "good"}`} viewBox={`0 0 ${W} ${H}`} width={W} height={H} role="img" aria-label={label}>
      <title>{label}</title>
      <line className="spark-zero" x1={P} x2={W - P} y1={H / 2} y2={H / 2} />
      {eventAt != null && <line className="spark-event" x1={x(eventAt)} x2={x(eventAt)} y1={P} y2={H - P} />}
      <path className="spark-line" d={d} pathLength={1} />
      <circle className="spark-end" cx={x(values.length - 1)} cy={y(last)} r={2.5} />
    </svg>
  );
}
