import { FormEvent, useMemo, useState } from "react";
import { generatePlan } from "./api";
import type { PlanRequest, PlanResponse } from "./types";

const ALL_INTERESTS = [
  "food",
  "nature",
  "museums",
  "nightlife",
  "shopping",
  "history",
  "architecture",
  "wellness",
  "music"
];

const initialRequest: PlanRequest = {
  destinationCity: "Barcelona",
  destinationCountry: "Spain",
  startDate: "2026-06-10",
  endDate: "2026-06-14",
  travelStyle: "balanced",
  touristVsLocal: 40,
  walkingTolerance: 60,
  groupType: "friends",
  interests: ["food", "architecture", "nightlife"],
  notes: "I want a colorful, artsy trip with local energy and one iconic attraction per day."
};

export default function App() {
  const [request, setRequest] = useState<PlanRequest>(initialRequest);
  const [result, setResult] = useState<PlanResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const tripLength = useMemo(() => {
    const start = new Date(request.startDate);
    const end = new Date(request.endDate);
    const diff = Math.round((end.getTime() - start.getTime()) / 86400000) + 1;
    return Number.isFinite(diff) && diff > 0 ? diff : 0;
  }, [request.startDate, request.endDate]);

  const toggleInterest = (interest: string) => {
    setRequest((prev) => {
      const has = prev.interests.includes(interest);
      const interests = has
        ? prev.interests.filter((i) => i !== interest)
        : [...prev.interests, interest];
      return { ...prev, interests };
    });
  };

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await generatePlan(request);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <div className="glow glow-one" />
      <div className="glow glow-two" />
      <header className="hero">
        <p className="eyebrow">RoamRight</p>
        <h1>Plan your next vibe-heavy adventure</h1>
        <p className="subtitle">
          Personality-aware itineraries for people who want both iconic spots and local energy.
        </p>
      </header>

      <main className="layout">
        <form className="card form-card" onSubmit={onSubmit}>
          <h2>Trip Details</h2>
          <div className="grid two-col">
            <label>
              City
              <input
                value={request.destinationCity}
                onChange={(e) => setRequest({ ...request, destinationCity: e.target.value })}
                required
              />
            </label>
            <label>
              Country
              <input
                value={request.destinationCountry}
                onChange={(e) => setRequest({ ...request, destinationCountry: e.target.value })}
                required
              />
            </label>
            <label>
              Start Date
              <input
                type="date"
                value={request.startDate}
                onChange={(e) => setRequest({ ...request, startDate: e.target.value })}
                required
              />
            </label>
            <label>
              End Date
              <input
                type="date"
                value={request.endDate}
                onChange={(e) => setRequest({ ...request, endDate: e.target.value })}
                required
              />
            </label>
          </div>

          <div className="grid two-col">
            <label>
              Travel Style
              <select
                value={request.travelStyle}
                onChange={(e) =>
                  setRequest({
                    ...request,
                    travelStyle: e.target.value as PlanRequest["travelStyle"]
                  })
                }
              >
                <option value="relaxed">Relaxed</option>
                <option value="balanced">Balanced</option>
                <option value="packed">Packed</option>
              </select>
            </label>
            <label>
              Group
              <select
                value={request.groupType}
                onChange={(e) =>
                  setRequest({ ...request, groupType: e.target.value as PlanRequest["groupType"] })
                }
              >
                <option value="solo">Solo</option>
                <option value="friends">Friends</option>
                <option value="family">Family</option>
                <option value="couple">Couple</option>
              </select>
            </label>
          </div>

          <label>
            Tourist ↔ Local ({request.touristVsLocal})
            <input
              type="range"
              min={0}
              max={100}
              value={request.touristVsLocal}
              onChange={(e) => setRequest({ ...request, touristVsLocal: Number(e.target.value) })}
            />
          </label>

          <label>
            Walking Tolerance ({request.walkingTolerance})
            <input
              type="range"
              min={0}
              max={100}
              value={request.walkingTolerance}
              onChange={(e) => setRequest({ ...request, walkingTolerance: Number(e.target.value) })}
            />
          </label>

          <fieldset>
            <legend>Interests</legend>
            <div className="chips">
              {ALL_INTERESTS.map((interest) => {
                const selected = request.interests.includes(interest);
                return (
                  <button
                    type="button"
                    key={interest}
                    className={selected ? "chip active" : "chip"}
                    onClick={() => toggleInterest(interest)}
                  >
                    {interest}
                  </button>
                );
              })}
            </div>
          </fieldset>

          <label>
            Personalization Notes
            <textarea
              rows={4}
              value={request.notes}
              onChange={(e) => setRequest({ ...request, notes: e.target.value })}
              placeholder="Tell RoamRight your vibe: pacing, hidden gems, nightlife, food priorities, etc."
            />
          </label>

          <button className="primary-btn" disabled={loading || tripLength <= 0}>
            {loading ? "Generating..." : "Generate Itinerary"}
          </button>

          {tripLength <= 0 && <p className="hint">End date must be on or after start date.</p>}
          {error && <p className="error">{error}</p>}
        </form>

        <section className="card result-card">
          <h2>Your Itinerary</h2>
          <p className="pill">{tripLength} day trip</p>
          {!result && <p className="empty">Generate a plan to see your itinerary here.</p>}
          {result && (
            <>
              <pre className="itinerary">{result.itineraryText}</pre>
              <h3>Top Activity Picks</h3>
              <ul className="activity-list">
                {result.topActivities.map((activity) => (
                  <li key={`${activity.name}-${activity.category}`}>
                    <strong>{activity.name}</strong>
                    <span>
                      {activity.category}
                      {activity.neighborhood ? ` · ${activity.neighborhood}` : ""}
                    </span>
                  </li>
                ))}
              </ul>
            </>
          )}
        </section>
      </main>
    </div>
  );
}
