import { FormEvent, useEffect, useMemo, useState } from "react";
import { generatePlan, refinePlan } from "./api";
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

const BACKGROUND_IMAGES = [
  "/images/eduardo-rodriguez-7GWTKyvUjag-unsplash.jpg",
  "/images/florian-wehde-WBGjg0DsO_g-unsplash.jpg",
  "/images/harrison-fitts-VXHqJN52K6s-unsplash.jpg",
  "/images/henrique-ferreira-62QRdDoe44M-unsplash.jpg",
  "/images/jorge-fernandez-salas-C7MUgJowo8s-unsplash.jpg",
  "/images/jorge-fernandez-salas-ChSZETOal-I-unsplash.jpg",
  "/images/jorge-fernandez-salas-v8XeGZf8tcs-unsplash.jpg",
  "/images/sam-williams-UuGAw6nF0Vw-unsplash.jpg",
  "/images/susan-flynn-cHOkA_U_CPM-unsplash.jpg",
  "/images/taisia-karaseva-s3kdLmeYxXs-unsplash.jpg",
  "/images/tomas-nozina-UP22zkjJGZo-unsplash.jpg",
  "/images/victoriano-izquierdo-HoevDVvxInw-unsplash.jpg",
  "/images/vienna-reyes-5X1y4fvpIV0-unsplash.jpg"
];

const initialRequest: PlanRequest = {
  destinationCity: "Barcelona",
  destinationCountry: "Spain",
  startDate: "2026-06-10",
  endDate: "2026-06-14",
  arrivalTime: "10:00",
  departureTime: "20:00",
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
  const [refineFeedback, setRefineFeedback] = useState("");
  const [bgIndex, setBgIndex] = useState(0);
  const [showResultView, setShowResultView] = useState(false);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setBgIndex((prev) => (prev + 1) % BACKGROUND_IMAGES.length);
    }, 9000);
    return () => window.clearInterval(timer);
  }, []);

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
      setShowResultView(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  const onRefine = async () => {
    if (!result || !refineFeedback.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await refinePlan({
        baseRequest: request,
        currentItineraryText: result.itineraryText,
        feedback: refineFeedback.trim()
      });
      setResult(data);
      setRefineFeedback("");
      setShowResultView(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Refinement failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <div
        className="slideshow-bg"
        style={{ backgroundImage: `url("${BACKGROUND_IMAGES[bgIndex]}")` }}
      />
      <div className="slideshow-overlay" />
      <header className="hero">
        <div className="hero-content">
          <p className="brand-title">RoamRight</p>
          <h1>
            plan trips that <span className="accent-actually">actually</span> match your vibe
          </h1>
          <p className="subtitle">
            From hidden alleys to iconic skylines — your trip, your tempo
          </p>
        </div>
        <p className="scroll-hint">Scroll down to start planning</p>
      </header>

      <main className="layout single-panel">
        {!showResultView && !loading && (
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
            <label>
              Arrival Time
              <input
                type="time"
                value={request.arrivalTime}
                onChange={(e) => setRequest({ ...request, arrivalTime: e.target.value })}
                required
              />
            </label>
            <label>
              Departure Time
              <input
                type="time"
                value={request.departureTime}
                onChange={(e) => setRequest({ ...request, departureTime: e.target.value })}
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
            {loading ? "Generating..." : "Generate Your Perfect Trip"}
          </button>

          {tripLength <= 0 && <p className="hint">End date must be on or after start date.</p>}
          {error && <p className="error">{error}</p>}
          </form>
        )}

        {loading && (
          <section className="card loading-card">
            <div className="spinner" />
            <h2>Building your itinerary...</h2>
            <p>Matching your vibe with activities, timing, and flow.</p>
          </section>
        )}

        {!loading && showResultView && result && (
          <section className="card result-card">
          <h2>Your Perfect Trip</h2>
          <p className="pill">{tripLength} day trip</p>
            <button
              type="button"
              className="secondary-btn"
              onClick={() => {
                setShowResultView(false);
                setError(null);
              }}
            >
              Edit Trip Details
            </button>
            <>
              <div className="day-grid">
                {result.days.map((d) => (
                  <article className="day-card" key={`day-${d.day}`}>
                    <h3>Day {d.day}</h3>
                    <ul>
                      <li>
                        <strong>Morning:</strong>
                        <ul>
                          {d.morning.length === 0 ? <li>No morning plan (travel window).</li> : null}
                          {d.morning.map((item, idx) => (
                            <li key={`m-${d.day}-${idx}`}>{item}</li>
                          ))}
                        </ul>
                      </li>
                      <li>
                        <strong>Afternoon:</strong>
                        <ul>
                          {d.afternoon.length === 0 ? <li>No afternoon plan (travel window).</li> : null}
                          {d.afternoon.map((item, idx) => (
                            <li key={`a-${d.day}-${idx}`}>{item}</li>
                          ))}
                        </ul>
                      </li>
                      <li>
                        <strong>Evening:</strong>
                        <ul>
                          {d.evening.length === 0 ? <li>No evening plan (travel window).</li> : null}
                          {d.evening.map((item, idx) => (
                            <li key={`e-${d.day}-${idx}`}>{item}</li>
                          ))}
                        </ul>
                      </li>
                    </ul>
                  </article>
                ))}
              </div>

              <div className="explanation-box">
                <h3>How This Trip Flows</h3>
                <ul>
                  {result.explanationBullets.map((line, i) => (
                    <li key={`expl-${i}`}>{line}</li>
                  ))}
                </ul>
              </div>

              <div className="explanation-box">
                <h3>Refine This Plan</h3>
                <textarea
                  rows={3}
                  value={refineFeedback}
                  onChange={(e) => setRefineFeedback(e.target.value)}
                  placeholder="Example: make day 2 more local and reduce walking; add one late-night music stop."
                />
                <button
                  className="primary-btn"
                  type="button"
                  onClick={onRefine}
                  disabled={loading || !refineFeedback.trim()}
                >
                  {loading ? "Refining..." : "Refine Itinerary"}
                </button>
              </div>
            </>
          </section>
        )}
      </main>
    </div>
  );
}
