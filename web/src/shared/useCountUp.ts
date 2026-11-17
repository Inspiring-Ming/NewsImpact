// Key numbers count up from zero when a page opens, the way a trading screen ticks in.
// Works on a plain number or on formatted text ("−18.5%", "1.4×", "2 of 3"): the first
// number is animated, its sign, decimals and the words around it are kept. People who
// turn motion off (prefers-reduced-motion) get the final value straight away.
import { useEffect, useRef, useState, type ReactNode } from "react";

const NUM = /\d+(?:\.\d+)?/;
const MS = 700;
const reduced = () => typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

export function useCountUp(value: ReactNode): ReactNode {
  const text = typeof value === "number" ? String(value) : typeof value === "string" ? value : null;
  const m = text?.match(NUM);
  const target = m ? Number(m[0]) : null;
  const [shown, setShown] = useState<number | null>(target === null || reduced() ? target : 0);
  const from = useRef(0);

  useEffect(() => {
    if (target === null || reduced()) { setShown(target); return; }
    const start = performance.now(), begin = from.current;
    let frame = 0;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / MS);
      const v = begin + (target - begin) * (1 - (1 - t) ** 3); // ease-out
      setShown(v);
      from.current = v;
      if (t < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [target]);

  if (!text || !m || shown === null) return value;
  const decimals = m[0].split(".")[1]?.length ?? 0;
  return text.slice(0, m.index) + shown.toFixed(decimals) + text.slice(m.index! + m[0].length);
}
