// Everything a story section may need. New sections receive the same object.
import type { S } from "../../api/client";

export interface StoryData {
  company: S["CompanyCard"];
  card: S["StoryCard"];
  story: S["Storyline"];
  assessment: S["Assessment"];
  prices: S["PricePath"] | null;
}
