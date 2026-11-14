import type {
  AnalysisResponse,
  EditReviewDecision,
  RequirementReviewDecision,
} from "../types/analysis";

async function parseError(response: Response): Promise<string> {
  try {
    const payload: unknown = await response.json();
    if (payload && typeof payload === "object" && "detail" in payload) {
      const detail = (payload as { detail: unknown }).detail;
      return typeof detail === "string" ? detail : JSON.stringify(detail);
    }
  } catch {
    // Preserve the HTTP status if the server sent an unexpected body.
  }
  return `The request failed (HTTP ${response.status}).`;
}

async function postJSON<TResponse>(path: string, body: unknown): Promise<TResponse> {
  const response = await fetch(`/api${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json() as Promise<TResponse>;
}

export const analysisAPI = {
  start(resume: string, jobDescription: string) {
    return postJSON<AnalysisResponse>("/analyses", {
      resume,
      job_description: jobDescription,
    });
  },

  submitReview(
    threadId: string,
    reviews: RequirementReviewDecision[],
    additionalInformation: string[],
    approvedForOptimization: boolean,
  ) {
    return postJSON<AnalysisResponse>(`/analyses/${encodeURIComponent(threadId)}/review`, {
      reviews,
      additional_information: additionalInformation,
      approved_for_optimization: approvedForOptimization,
    });
  },

  submitEdits(threadId: string, decisions: EditReviewDecision[]) {
    return postJSON<AnalysisResponse>(`/analyses/${encodeURIComponent(threadId)}/edits`, {
      decisions,
    });
  },
};
