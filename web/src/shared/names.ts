// Display names that live in the data, not in code: story types and events come from
// playbooks.json ("title"), outlets from sources.json ("name"). Loaded once, shared by all
// pages; anything unknown falls back to labels.ts.
import { useEffect, useState } from "react";
import { api } from "../api/client";
import { label } from "./labels";

interface Names { titles: Map<string, string>; outlets: Map<string, string> }

let cache: Promise<Names> | null = null;

function load(): Promise<Names> {
  cache ??= Promise.all([api.method(), api.sources()]).then(([m, s]) => {
    const titles = new Map<string, string>();
    for (const p of m.playbooks) {
      if (p.title) titles.set(p.theme, p.title);
      for (const st of p.stages) if (st.title) titles.set(st.name, st.title);
    }
    const outlets = new Map(s.map((x) => [x.source.source_id, x.source.name.split(" - ")[0]]));
    return { titles, outlets };
  }).catch(() => ({ titles: new Map(), outlets: new Map() }));
  return cache;
}

export function useNames() {
  const [names, setNames] = useState<Names>({ titles: new Map(), outlets: new Map() });
  useEffect(() => { load().then(setNames); }, []);
  return {
    /** story type or event code -> its title from playbooks.json */
    title: (code: string) => names.titles.get(code) ?? label(code),
    /** outlet id -> its name from sources.json */
    outlet: (id: string) => names.outlets.get(id) ?? id,
  };
}
