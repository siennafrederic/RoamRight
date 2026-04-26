import type { PlanRequest, PlanResponse, RefineRequest } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function generatePlan(payload: PlanRequest): Promise<PlanResponse> {
  const response = await fetch(`${API_BASE_URL}/api/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Failed to generate itinerary");
  }

  return response.json() as Promise<PlanResponse>;
}

export async function refinePlan(payload: RefineRequest): Promise<PlanResponse> {
  const response = await fetch(`${API_BASE_URL}/api/refine`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Failed to refine itinerary");
  }
  return response.json() as Promise<PlanResponse>;
}
