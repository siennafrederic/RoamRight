export type PlanRequest = {
  destinationCity: string;
  destinationCountry: string;
  startDate: string;
  endDate: string;
  travelStyle: "relaxed" | "balanced" | "packed";
  touristVsLocal: number;
  walkingTolerance: number;
  groupType: "solo" | "friends" | "family" | "couple";
  interests: string[];
  notes: string;
};

export type PlanResponse = {
  itineraryText: string;
  topActivities: Array<{
    name: string;
    category: string;
    neighborhood?: string;
  }>;
};
