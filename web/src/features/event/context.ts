// Everything one event page shows, loaded once and handed to each tab.
import type { S } from "../../api/client";

export interface EventData {
  company: S["CompanyCard"];
  card: S["EventCard"];
  story: S["Storyline"];
  assessment: S["Assessment"];
  prices: S["PricePath"] | null;
}
