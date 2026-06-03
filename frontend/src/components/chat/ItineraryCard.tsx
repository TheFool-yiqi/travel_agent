import type { ItineraryDay } from "@/types/itinerary";

type ItineraryCardProps = {
  summary?: string;
  days: ItineraryDay[];
  budget?: Record<string, number>;
};

export function ItineraryCard({ summary, days, budget }: ItineraryCardProps) {
  if (days.length === 0) {
    return null;
  }

  return (
    <aside className="itinerary-card glass-card" aria-label="行程概览">
      <h3 className="font-serif-brand itinerary-card-title">行程概览</h3>
      {summary ? <p className="itinerary-card-summary">{summary}</p> : null}
      <ol className="itinerary-day-list">
        {days.map((day) => (
          <li key={day.day_number} className="itinerary-day-item">
            <div className="itinerary-day-header">
              <span className="itinerary-day-badge">Day {day.day_number}</span>
              {day.theme ? <span className="itinerary-day-theme">{day.theme}</span> : null}
            </div>
            <ul className="itinerary-activity-list">
              {(day.activities ?? []).map((activity) => (
                <li key={activity}>{activity}</li>
              ))}
            </ul>
          </li>
        ))}
      </ol>
      {budget?.total != null ? (
        <p className="itinerary-budget">
          预算估算：<strong>{Math.round(budget.total).toLocaleString()}</strong> 元
        </p>
      ) : null}
    </aside>
  );
}
