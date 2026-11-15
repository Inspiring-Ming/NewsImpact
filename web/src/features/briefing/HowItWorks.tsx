// The product in four steps - the first thing a visitor reads.
const STEPS = [
  ["Monitor", "We read trusted US and Australian news outlets around the clock."],
  ["Connect", "Related news becomes one story: e.g. a scandal, then a resignation, then a successor."],
  ["Anticipate", "For each stage we know which decisions investors, analysts and boards typically make."],
  ["Verify", "We check every stage against independent sources and real market data, then conclude."],
];

export function HowItWorks() {
  return (
    <ol className="how">
      {STEPS.map(([title, text], i) => (
        <li key={title}>
          <span className="how-num">{i + 1}</span>
          <div><b>{title}</b><p>{text}</p></div>
        </li>
      ))}
    </ol>
  );
}
