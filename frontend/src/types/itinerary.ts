export type ItineraryDay = {
  day_number: number;
  theme?: string;
  activities?: string[];
  meals?: string[];
  accommodation?: string;
  plan_b?: string;
};

export type ItineraryPayload = {
  summary?: string;
  days: ItineraryDay[];
  budget?: Record<string, number>;
};

/** API response from GET /itineraries/... */
export type ItineraryResponse = {
  id: string;
  session_id: string;
  user_id: string;
  days: ItineraryDay[] | Record<string, unknown>[];
  budget?: Record<string, number> | null;
  summary?: string | null;
  status: "draft" | "approved" | string;
  version: number;
  created_at: string;
  updated_at: string;
};

/** Normalize backend itinerary dict/list into ItineraryDay[]. */
export function normalizeItinerary(raw: unknown): ItineraryDay[] {
  if (!Array.isArray(raw)) {
    return [];
  }
  return raw.map((item, index) => {
    const row = item as Record<string, unknown>;
    const dayNumber = Number(row.day_number ?? index + 1);
    const activities = Array.isArray(row.activities)
      ? row.activities.map(String)
      : [row.morning, row.afternoon, row.evening].filter(Boolean).map(String);
    return {
      day_number: dayNumber,
      theme: row.theme ? String(row.theme) : undefined,
      activities,
      meals: Array.isArray(row.meals) ? row.meals.map(String) : undefined,
      accommodation: row.accommodation ? String(row.accommodation) : undefined,
      plan_b: row.plan_b ? String(row.plan_b) : undefined,
    };
  });
}
