export type PlanRequest = {
  destinationCity: string;
  destinationCountry: string;
  startDate: string;
  endDate: string;
  arrivalTime: string;
  departureTime: string;
  travelStyle: "relaxed" | "balanced" | "packed";
  touristVsLocal: number;
  walkingTolerance: number;
  groupType: "solo" | "friends" | "family" | "couple";
  interests: string[];
  notes: string;
};

export type DayPlan = {
  day: number;
  morning: string[];
  afternoon: string[];
  evening: string[];
};

export type PlanResponse = {
  days: DayPlan[];
  explanationBullets: string[];
  itineraryText: string;
  topActivities: Array<{
    name: string;
    category: string;
    neighborhood?: string;
  }>;
};

export type RefineRequest = {
  baseRequest: PlanRequest;
  currentItineraryText: string;
  feedback: string;
};
