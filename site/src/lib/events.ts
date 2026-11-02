// Typed access to site/data/olaylar.json.
import raw from "../../data/olaylar.json";

export interface EventItem { month: string; type: string; title: string; change: number | null; origin: "derived" | "manual" }
export interface Events {
  generated_at: string; threshold: number; sample: boolean;
  source: { label: string; source: string; code: string | null; verified: boolean; sample: boolean } | null;
  events: EventItem[];
}
export const events = raw as unknown as Events;
