
import type {
  AnalysisResponse,
  EditReviewDecision,
  RequirementReviewDecision,
} from "../types/analysis";

// Held only in JavaScript memory.
// Not persisted to localStorage or cookies.
let activeSessionToken: string | null = null;

type StartAnalysisResponse = AnalysisResponse & {
  session_token: string;
};

async function parseError(
  response: Response
): Promise<string> {
  try {
    const payload: unknown = await response.json();

    if (
      payload &&
      typeof payload === "object" &&
      "detail" in payload
    ) {
      const detail = (
        payload as { detail: unknown }
      ).detail;

      return typeof detail === "string"
        ? detail
        : JSON.stringify(detail);
    }
  } catch {
    // Fall back to the HTTP status.
  }

  return `Request failed (HTTP ${response.status}).`;
}

async function postJSON<TResponse>(
  path: string,
  body: unknown,
  requiresSession = false,
): Promise<TResponse> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (requiresSession) {
    if (!activeSessionToken) {
      throw new Error(
        "Session expired or unavailable. Start a new analysis."
      );
    }

    headers["X-Analysis-Token"] = activeSessionToken;
  }

  const response = await fetch(`/api${path}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
    cache: "no-store",
  });

  if (!response.ok) {
    if (
      requiresSession &&
      (response.status === 401 ||
        response.status === 403 ||
        response.status === 404)
    ) {
      activeSessionToken = null;
    }

    throw new Error(await parseError(response));
  }

  return response.json() as Promise<TResponse>;
}

export const analysisAPI = {
  async start(
    resume: string,
    jobDescription: string
  ): Promise<AnalysisResponse> {
    activeSessionToken = null;

    const response = await postJSON<StartAnalysisResponse>(
      "/analyses",
      {
        resume,
        job_description: jobDescription,
      },
    );

    // Keep the secret out of React application state.
    const { session_token, ...analysis } = response;

    activeSessionToken = session_token;

    return analysis;
  },

  submitReview(
    threadId: string,
    reviews: RequirementReviewDecision[],
    additionalInformation: string[],
    approvedForOptimization: boolean,
  ) {
    return postJSON<AnalysisResponse>(
      `/analyses/${encodeURIComponent(threadId)}/review`,
      {
        reviews,
        additional_information: additionalInformation,
        approved_for_optimization: approvedForOptimization,
      },
      true,
    );
  },

  submitEdits(
    threadId: string,
    decisions: EditReviewDecision[],
  ) {
    return postJSON<AnalysisResponse>(
      `/analyses/${encodeURIComponent(threadId)}/edits`,
      {
        decisions,
      },
      true,
    );
  },

  clearSession() {
    activeSessionToken = null;
  },
};
