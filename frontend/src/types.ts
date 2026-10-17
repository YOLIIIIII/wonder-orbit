export type Energy = "low" | "medium" | "high";
export interface StarInput {
  title: string;
  original_text: string;
  description: string;
  category: string;
  tags: string[];
  interest_reason: string | null;
  source_type: "manual" | "paste" | "link";
  source_reference: string | null;
  estimated_minutes: number | null;
  estimated_budget: number | null;
  energy_level: Energy | null;
  status: "collected" | "exploring" | "archived";
}
export interface Star extends StarInput {
  id: string;
  created_at: string;
  updated_at: string;
}
export interface Proposal {
  title: string;
  description: string;
  estimated_minutes: number;
  estimated_budget: number | null;
  energy_level: Energy;
  steps: string[];
  based_on_star_ids: string[];
  rationale: string;
  uncertainties: string[];
}
export interface Reflection {
  outcome: "completed" | "skipped";
  user_feedback: string;
  liked_aspects: string[];
  disliked_aspects: string[];
}
export interface Quest extends Proposal {
  id: string;
  status: "accepted" | "completed" | "skipped";
  reflection: Reflection | null;
}
export interface Match {
  star_id: string;
  title: string;
  text: string;
  score: number;
  match_basis: string[];
}
export interface AgentRequest {
  request_type: "collect" | "explore";
  text: string;
  available_minutes?: number | null;
  budget?: number | null;
  energy_level?: Energy | null;
  source_type?: string;
  source_reference?: string | null;
}
export interface Run {
  run_id: string;
  request_type: string;
  status: string;
  mode: string;
  model_name: string;
  started_at: string;
  elapsed_ms: number | null;
  summary: string;
  error_type: string | null;
  events: { kind: string; name: string; status: string; elapsed_ms: number }[];
  state: {
    request: AgentRequest;
    draft?: { draft: StarInput; missing_fields: string[]; questions: string[] };
    proposals?: Proposal[];
    questions?: string[];
    related_stars?: Match[];
    validation?: { valid: boolean; errors: string[] }[];
  };
  decisions: Record<
    string,
    { approved: boolean; star_id?: string; quest_id?: string }
  >;
}
export interface Preference {
  categories: string[];
  min_minutes: number;
  max_minutes: number;
  max_budget: number | null;
  energy_level: Energy | null;
  constraints: string[];
}
export interface PreferenceData {
  explicit: Preference;
  candidates: {
    id: string;
    category: string;
    summary: string;
    reflection_id: string;
  }[];
}
export interface Stats {
  stars: number;
  quests: number;
  completed: number;
  categories: { name: string; count: number }[];
}
export interface Relation {
  from_id: string;
  to_id: string;
  from_title: string;
  to_title: string;
  reasons: string[];
}
