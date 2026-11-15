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

export const confidenceTone = (x: number): Tone => (x >= 0.9 ? "good" : x >= 0.6 ? "warn" : "bad");

/** Source reliability: a newspaper's 75% starting estimate is already good evidence. */
export const reliabilityTone = (x: number): Tone => (x >= 0.75 ? "good" : x >= 0.6 ? "warn" : "bad");
