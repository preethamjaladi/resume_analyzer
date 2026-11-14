/** These types mirror resume_analyzer/api.py and schemas.py in the existing backend. */
export type MatchStatus = "met" | "partially_met" | "not_met" | "unknown";
export type EditChoice = "accept" | "edit" | "reject";

export interface RequirementMatch {
  requirement_id: string;
  status: MatchStatus;
  evidence: string | null;
  match_type: "exact" | "semantic" | "none" | string;
  explanation: string;
}

export interface ResumeEditProposal {
  edit_id: string;
  requirement_id: string | null;
  section: string;
  operation: "replace" | "insert" | "delete";
  start_index: number;
  end_index: number;
  original_text: string;
  proposed_text: string;
  supporting_evidence: string[];
  reason: string;
}

export interface ResumeSuggestion {
  requirement_id?: string | null;
  section: string;
  action: string;
  priority: "high" | "medium" | "low";
  current_text?: string | null;
  suggested_text: string;
  reason: string;
}

export interface ResumeSuggestions {
  suggestions: ResumeSuggestion[];
}

export interface AnalysisResponse {
  thread_id: string;
  status: "paused" | "completed";
  next_nodes: string[];
  interrupts?: unknown[];
  review_completed: boolean;
  match_score: number | null;
  hard_gaps: string[];
  requirement_matches: RequirementMatch[];
  resume_suggestions: ResumeSuggestions | string | null | unknown;
  edit_proposals: ResumeEditProposal[];
  tailored_resume: string | null;
}

export interface RequirementReviewDecision {
  requirement_id: string;
  decision: "approve" | "correct";
  corrected_status?: MatchStatus;
  reason?: string;
}

export interface EditReviewDecision {
  edit_id: string;
  decision: EditChoice;
  edited_text?: string;
}

export const MATCH_LABELS: Record<MatchStatus, string> = {
  met: "Matched",
  partially_met: "Partial match",
  not_met: "Not met",
  unknown: "Needs review",
};

export function isResumeSuggestions(value: unknown): value is ResumeSuggestions {
  return typeof value === "object" && value !== null &&
    "suggestions" in value && Array.isArray((value as { suggestions?: unknown }).suggestions);
}
