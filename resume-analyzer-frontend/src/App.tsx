
import { useEffect, useState } from "react";
import {
  FileText,
  BriefcaseBusiness,
  Sparkles,
  LoaderCircle,
  AlertCircle,
  CheckCircle2,
  ClipboardCheck,
  Pencil,
  ThumbsUp,
  ThumbsDown,
  Download,
} from "lucide-react";

type MatchStatus = "met" | "partially_met" | "not_met" | "unknown";
type EditChoice = "accept" | "edit" | "reject";

interface RequirementMatch {
  requirement_id: string;
  status: MatchStatus;
  evidence: string | null;
  match_type: string;
  explanation: string;
}

interface ResumeEditProposal {
  edit_id: string;
  requirement_id?: string | null;
  section: string;
  operation: "replace" | "insert" | "delete";
  start_index: number;
  end_index: number;
  original_text: string;
  proposed_text: string;
  supporting_evidence: string[];
  reason: string;
}

interface EditDecision {
  edit_id: string;
  decision: EditChoice;
  edited_text?: string | null;
}

interface AnalysisResponse {
  thread_id: string;
  status: "paused" | "completed";
  next_nodes: string[];
  review_completed: boolean;
  match_score: number | null;
  hard_gaps: string[];
  requirement_matches: RequirementMatch[];
  resume_suggestions?: unknown;
  edit_proposals: ResumeEditProposal[];
  tailored_resume: string | null;
}

const statusStyles: Record<MatchStatus, string> = {
  met: "bg-emerald-100 text-emerald-700",
  partially_met: "bg-amber-100 text-amber-700",
  not_met: "bg-red-100 text-red-700",
  unknown: "bg-slate-100 text-slate-700",
};

const statusLabels: Record<MatchStatus, string> = {
  met: "Met",
  partially_met: "Partially Met",
  not_met: "Not Met",
  unknown: "Unknown",
};

// Formats the suggestions without assuming a specific
// nested structure inside ResumeSuggestions.
function formatSuggestions(value: unknown): string {
  if (value == null) return "";

  if (typeof value === "string") return value;

  return JSON.stringify(value, null, 2);
}

async function readApiError(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();

    if (typeof body === "object" && body !== null && "detail" in body) {
      const detail = body.detail;

      return typeof detail === "string"
        ? detail
        : JSON.stringify(detail);
    }
  } catch {
    // Use HTTP status when the response is not JSON.
  }

  return `Request failed (${response.status})`;
}

function App() {
  // Analysis
  const [resume, setResume] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Human review
  const [reviewStatuses, setReviewStatuses] = useState<
    Record<string, MatchStatus>
  >({});
  const [additionalInfo, setAdditionalInfo] = useState("");
  const [optimize, setOptimize] = useState(false);
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewMessage, setReviewMessage] = useState("");

  // Resume edit review
  const [editChoices, setEditChoices] = useState<
    Record<string, EditChoice>
  >({});
  const [editedTexts, setEditedTexts] = useState<
    Record<string, string>
  >({});
  const [submittingEdits, setSubmittingEdits] = useState(false);

  const isHumanReview =
    analysis?.status === "paused" &&
    analysis.next_nodes.includes("human_review");

  const isEditReview =
    analysis?.status === "paused" &&
    analysis.next_nodes.includes("review_resume_edits");

  const proposals = analysis?.edit_proposals ?? [];

  // Initialize edit decisions whenever proposals change.
  // Default to Reject so edits require explicit approval.
  useEffect(() => {
    if (!isEditReview) return;

    setEditChoices(
      Object.fromEntries(
        proposals.map((proposal) => [proposal.edit_id, "reject"])
      )
    );

    setEditedTexts(
      Object.fromEntries(
        proposals.map((proposal) => [
          proposal.edit_id,
          proposal.proposed_text,
        ])
      )
    );
  }, [isEditReview, analysis?.thread_id, analysis?.edit_proposals]);

  // Step 1: Analyze resume
  const analyzeResume = async () => {
    if (!resume.trim() || !jobDescription.trim()) {
      setError("Please provide both your resume and job description.");
      return;
    }

    setLoading(true);
    setError("");
    setAnalysis(null);
    setReviewMessage("");
    setReviewStatuses({});
    setEditChoices({});
    setEditedTexts({});
    setAdditionalInfo("");
    setOptimize(false);

    try {
      const response = await fetch("/api/analyses", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          resume,
          job_description: jobDescription,
        }),
      });

      if (!response.ok) {
        throw new Error(await readApiError(response));
      }

      const data: AnalysisResponse = await response.json();

      setAnalysis(data);

      setReviewStatuses(
        Object.fromEntries(
          data.requirement_matches.map((match) => [
            match.requirement_id,
            match.status,
          ])
        )
      );
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Analysis failed."
      );
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Submit human review
  const submitReview = async () => {
    if (!analysis || !isHumanReview) return;

    setSubmittingReview(true);
    setError("");
    setReviewMessage("");

    const reviews = analysis.requirement_matches.map((match) => {
      const selectedStatus =
        reviewStatuses[match.requirement_id] ?? match.status;

      if (selectedStatus === match.status) {
        return {
          requirement_id: match.requirement_id,
          decision: "approve",
        };
      }

      return {
        requirement_id: match.requirement_id,
        decision: "correct",
        corrected_status: selectedStatus,
        reason: "Corrected during human review",
      };
    });

    try {
      const response = await fetch(
        `/api/analyses/${analysis.thread_id}/review`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            reviews,
            additional_information: additionalInfo.trim()
              ? [additionalInfo.trim()]
              : [],
            approved_for_optimization: optimize,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(await readApiError(response));
      }

      const data: AnalysisResponse = await response.json();
      setAnalysis(data);

      if (data.next_nodes.includes("review_resume_edits")) {
        setReviewMessage(
          "Human review completed. Review the proposed resume edits below."
        );
      } else if (data.status === "completed") {
        setReviewMessage(
          optimize
            ? "Optimization finished. Review the suggestions and any generated resume below."
            : "Human review completed. The match score has been updated."
        );
      } else {
        setReviewMessage(
          "Human review submitted. The workflow is paused."
        );
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Review submission failed."
      );
    } finally {
      setSubmittingReview(false);
    }
  };

  // Step 3: Submit decisions for proposed resume edits
  const submitEditDecisions = async () => {
    if (!analysis || !isEditReview) return;

    setError("");
    setReviewMessage("");

    const decisions: EditDecision[] = proposals.map((proposal) => {
      const decision = editChoices[proposal.edit_id] ?? "reject";

      return {
        edit_id: proposal.edit_id,
        decision,
        ...(decision === "edit"
          ? {
              edited_text:
                editedTexts[proposal.edit_id] ??
                proposal.proposed_text,
            }
          : {}),
      };
    });

    const invalidEdit = decisions.find(
      (item) =>
        item.decision === "edit" &&
        !item.edited_text?.trim()
    );

    if (invalidEdit) {
      setError(
        `Please enter replacement text for ${invalidEdit.edit_id}.`
      );
      return;
    }

    setSubmittingEdits(true);

    try {
      const response = await fetch(
        `/api/analyses/${analysis.thread_id}/edits`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ decisions }),
        }
      );

      if (!response.ok) {
        throw new Error(await readApiError(response));
      }

      const data: AnalysisResponse = await response.json();
      setAnalysis(data);

      if (data.status === "completed") {
        setReviewMessage(
          "Resume edit review completed. The approved changes have been applied."
        );
      } else {
        setReviewMessage(
          "Edit decisions submitted. The workflow is paused."
        );
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to submit edit decisions."
      );
    } finally {
      setSubmittingEdits(false);
    }
  };

  // Download generated text resume locally.
  const downloadResume = () => {
    if (!analysis?.tailored_resume) return;

    const blob = new Blob([analysis.tailored_resume], {
      type: "text/plain;charset=utf-8",
    });

    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");

    anchor.href = url;
    anchor.download = "tailored_resume.txt";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();

    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {/* Header */}
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center gap-3 px-6 py-5">
          <div className="rounded-xl bg-indigo-600 p-2.5 text-white">
            <FileText size={22} />
          </div>

          <div>
            <h1 className="text-xl font-bold">
              Resume Analyzer
            </h1>
            <p className="text-sm text-slate-500">
              AI-powered resume and job description analysis
            </p>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-8 px-6 py-10">
        {/* Introduction */}
        <section>
          <h2 className="text-3xl font-bold tracking-tight">
            How well does your resume match?
          </h2>
          <p className="mt-3 text-slate-600">
            Analyze requirements, review AI classifications,
            and approve targeted resume improvements.
          </p>
        </section>

        {/* Inputs */}
        <section className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center gap-2">
              <FileText className="text-indigo-600" size={20} />
              <h3 className="text-lg font-semibold">
                Your Resume
              </h3>
            </div>

            <textarea
              value={resume}
              onChange={(e) => setResume(e.target.value)}
              placeholder="Paste your resume here..."
              className="h-72 w-full resize-y rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
            />

            <p className="mt-2 text-xs text-slate-500">
              Paste your complete resume text.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center gap-2">
              <BriefcaseBusiness
                className="text-indigo-600"
                size={20}
              />
              <h3 className="text-lg font-semibold">
                Job Description
              </h3>
            </div>

            <textarea
              value={jobDescription}
              onChange={(e) =>
                setJobDescription(e.target.value)
              }
              placeholder="Paste the job description here..."
              className="h-72 w-full resize-y rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
            />

            <p className="mt-2 text-xs text-slate-500">
              Include requirements and qualifications.
            </p>
          </div>
        </section>

        {/* Analyze */}
        <div className="flex flex-col items-center gap-4">
          <button
            onClick={analyzeResume}
            disabled={loading || submittingReview || submittingEdits}
            className="flex items-center gap-2 rounded-xl bg-indigo-600 px-8 py-3.5 font-semibold text-white transition hover:bg-indigo-700 disabled:opacity-60"
          >
            {loading ? (
              <LoaderCircle
                className="animate-spin"
                size={20}
              />
            ) : (
              <Sparkles size={20} />
            )}

            {loading ? "Analyzing..." : "Analyze Resume"}
          </button>

          {error && (
            <div
              role="alert"
              className="flex items-center gap-2 text-sm text-red-600"
            >
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}
        </div>

        {/* Analysis */}
        {analysis && (
          <section className="space-y-6">
            <div className="flex items-center gap-2">
              <CheckCircle2
                className="text-emerald-600"
                size={22}
              />
              <h2 className="text-2xl font-bold">
                Analysis Results
              </h2>
            </div>

            {/* Score */}
            <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
              <p className="text-sm font-medium text-slate-500">
                Resume Match Score
              </p>
              <div className="mt-3 text-5xl font-bold text-indigo-600">
                {analysis.match_score == null
                  ? "N/A"
                  : `${analysis.match_score}%`}
              </div>
              <p className="mt-3 text-sm text-slate-500">
                Weighted estimate from extracted job requirements.
                Not an official ATS score.
              </p>
            </div>

            {/* Requirements */}
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h3 className="mb-5 text-xl font-semibold">
                Requirement Analysis
              </h3>

              <div className="space-y-4">
                {analysis.requirement_matches.map((match) => {
                  const selectedStatus =
                    reviewStatuses[match.requirement_id] ??
                    match.status;

                  return (
                    <div
                      key={match.requirement_id}
                      className="rounded-xl border border-slate-200 p-5"
                    >
                      <div className="mb-3 flex items-center justify-between gap-3">
                        <span className="font-semibold">
                          {match.requirement_id}
                        </span>
                        <span
                          className={`rounded-full px-3 py-1 text-xs font-semibold ${
                            statusStyles[match.status]
                          }`}
                        >
                          {statusLabels[match.status]}
                        </span>
                      </div>

                      <p className="text-sm leading-relaxed text-slate-700">
                        {match.explanation}
                      </p>

                      {isHumanReview && (
                        <div className="mt-4">
                          <label
                            htmlFor={`review-${match.requirement_id}`}
                            className="mb-2 block text-sm font-medium"
                          >
                            Review Classification
                          </label>

                          <select
                            id={`review-${match.requirement_id}`}
                            value={selectedStatus}
                            onChange={(e) =>
                              setReviewStatuses((previous) => ({
                                ...previous,
                                [match.requirement_id]:
                                  e.target.value as MatchStatus,
                              }))
                            }
                            className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
                          >
                            <option value="met">Met</option>
                            <option value="partially_met">
                              Partially Met
                            </option>
                            <option value="not_met">
                              Not Met
                            </option>
                            <option value="unknown">
                              Unknown
                            </option>
                          </select>

                          {selectedStatus !== match.status && (
                            <p className="mt-2 text-xs font-medium text-amber-700">
                              Changed from:{" "}
                              {statusLabels[match.status]}
                            </p>
                          )}
                        </div>
                      )}

                      {match.evidence && (
                        <div className="mt-4 rounded-lg bg-slate-50 p-3">
                          <p className="mb-1 text-xs font-semibold text-slate-500">
                            Supporting Evidence
                          </p>
                          <p className="text-sm text-slate-700">
                            {match.evidence}
                          </p>
                        </div>
                      )}
                    </div>
                  );
                })}

                {analysis.requirement_matches.length === 0 && (
                  <p className="text-sm text-slate-500">
                    No requirement matches were returned.
                  </p>
                )}
              </div>
            </div>

            {/* Hard Gaps */}
            {analysis.hard_gaps.length > 0 && (
              <div className="rounded-2xl border border-red-200 bg-red-50 p-6">
                <h3 className="mb-3 text-lg font-semibold text-red-800">
                  Missing Mandatory Requirements
                </h3>
                <ul className="list-disc space-y-2 pl-5 text-sm text-red-700">
                  {analysis.hard_gaps.map((gap, index) => (
                    <li key={index}>{gap}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Human Review */}
            {isHumanReview && (
              <div className="rounded-2xl border border-indigo-200 bg-white p-6 shadow-sm">
                <div className="flex items-center gap-2">
                  <ClipboardCheck
                    className="text-indigo-600"
                    size={22}
                  />
                  <h3 className="text-xl font-semibold">
                    Complete Human Review
                  </h3>
                </div>

                <p className="mt-3 text-sm text-slate-600">
                  Verify the classifications above and correct
                  inaccurate assessments.
                </p>

                <div className="mt-5">
                  <label
                    htmlFor="additional-info"
                    className="mb-2 block text-sm font-medium"
                  >
                    Additional Information (Optional)
                  </label>
                  <textarea
                    id="additional-info"
                    value={additionalInfo}
                    onChange={(e) =>
                      setAdditionalInfo(e.target.value)
                    }
                    placeholder="Additional truthful experience or context..."
                    className="h-28 w-full rounded-xl border border-slate-200 p-3 text-sm focus:border-indigo-500 focus:outline-none"
                  />
                  <p className="mt-1 text-xs text-slate-500">
                    Passed to optimization. Does not automatically
                    change your match score.
                  </p>
                </div>

                <label className="mt-5 flex items-center gap-3 text-sm">
                  <input
                    type="checkbox"
                    checked={optimize}
                    onChange={(e) =>
                      setOptimize(e.target.checked)
                    }
                    className="h-4 w-4 accent-indigo-600"
                  />
                  Generate AI resume improvement suggestions
                </label>

                <button
                  onClick={submitReview}
                  disabled={submittingReview}
                  className="mt-6 flex items-center gap-2 rounded-xl bg-indigo-600 px-6 py-3 font-semibold text-white hover:bg-indigo-700 disabled:opacity-60"
                >
                  {submittingReview ? (
                    <LoaderCircle
                      size={18}
                      className="animate-spin"
                    />
                  ) : (
                    <ClipboardCheck size={18} />
                  )}
                  {submittingReview
                    ? "Submitting Review..."
                    : "Submit Review"}
                </button>
              </div>
            )}

            {/* AI Suggestions */}
            {analysis.resume_suggestions != null && (
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="mb-4 flex items-center gap-2">
                  <Sparkles className="text-indigo-600" size={22} />
                  <h3 className="text-xl font-semibold">
                    AI Resume Suggestions
                  </h3>
                </div>

                <p className="mb-4 text-sm text-slate-600">
                  These are suggestions, not automatically
                  approved changes. Review them against your
                  actual experience.
                </p>

                <pre className="max-h-96 overflow-auto whitespace-pre-wrap break-words rounded-xl bg-slate-50 p-4 text-sm text-slate-700">
                  {formatSuggestions(analysis.resume_suggestions)}
                </pre>
              </div>
            )}

            {/* Edit Approval */}
            {isEditReview && (
              <div className="space-y-5 rounded-2xl border border-indigo-200 bg-white p-6 shadow-sm">
                <div>
                  <h3 className="text-xl font-semibold">
                    Review Proposed Resume Edits
                  </h3>
                  <p className="mt-2 text-sm text-slate-600">
                    Approve, modify, or reject each proposed
                    change. No edit is approved by default.
                  </p>
                </div>

                {proposals.map((proposal) => {
                  const choice =
                    editChoices[proposal.edit_id] ?? "reject";

                  return (
                    <div
                      key={proposal.edit_id}
                      className="space-y-4 rounded-xl border border-slate-200 p-5"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div>
                          <p className="font-semibold">
                            {proposal.edit_id}
                          </p>
                          <p className="text-xs text-slate-500">
                            {proposal.section} · {proposal.operation}
                            {proposal.requirement_id
                              ? ` · ${proposal.requirement_id}`
                              : ""}
                          </p>
                        </div>
                      </div>

                      <p className="text-sm text-slate-600">
                        {proposal.reason}
                      </p>

                      <div className="grid gap-4 lg:grid-cols-2">
                        <div className="rounded-xl border border-red-100 bg-red-50 p-4">
                          <p className="mb-2 text-xs font-bold uppercase tracking-wide text-red-700">
                            Original Text
                          </p>
                          <p className="whitespace-pre-wrap break-words text-sm text-slate-800">
                            {proposal.original_text || "(No text)"}
                          </p>
                        </div>

                        <div className="rounded-xl border border-emerald-100 bg-emerald-50 p-4">
                          <p className="mb-2 text-xs font-bold uppercase tracking-wide text-emerald-700">
                            Proposed Text
                          </p>
                          <p className="whitespace-pre-wrap break-words text-sm text-slate-800">
                            {proposal.proposed_text || "(No text)"}
                          </p>
                        </div>
                      </div>

                      {proposal.supporting_evidence?.length > 0 && (
                        <div className="rounded-lg bg-slate-50 p-3">
                          <p className="mb-2 text-xs font-semibold text-slate-500">
                            Supporting Evidence
                          </p>
                          {proposal.supporting_evidence.map(
                            (evidence, index) => (
                              <p
                                key={index}
                                className="mt-1 whitespace-pre-wrap text-sm text-slate-700"
                              >
                                {evidence}
                              </p>
                            )
                          )}
                        </div>
                      )}

                      <div className="grid grid-cols-3 gap-2">
                        {(
                          [
                            ["accept", "Accept", ThumbsUp],
                            ["edit", "Edit", Pencil],
                            ["reject", "Reject", ThumbsDown],
                          ] as const
                        ).map(([value, label, Icon]) => (
                          <button
                            key={value}
                            type="button"
                            onClick={() =>
                              setEditChoices((previous) => ({
                                ...previous,
                                [proposal.edit_id]: value,
                              }))
                            }
                            aria-pressed={choice === value}
                            className={`flex items-center justify-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition ${
                              choice === value
                                ? "border-indigo-600 bg-indigo-50 text-indigo-700"
                                : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                            }`}
                          >
                            <Icon size={16} />
                            {label}
                          </button>
                        ))}
                      </div>

                      {choice === "edit" && (
                        <div>
                          <label
                            htmlFor={`edit-${proposal.edit_id}`}
                            className="mb-2 block text-sm font-semibold"
                          >
                            Your Replacement Text
                          </label>
                          <textarea
                            id={`edit-${proposal.edit_id}`}
                            value={
                              editedTexts[proposal.edit_id] ?? ""
                            }
                            onChange={(e) =>
                              setEditedTexts((previous) => ({
                                ...previous,
                                [proposal.edit_id]:
                                  e.target.value,
                              }))
                            }
                            className="min-h-32 w-full rounded-xl border border-slate-300 p-3 text-sm focus:border-indigo-500 focus:outline-none"
                          />
                        </div>
                      )}

                      <p className="text-xs text-slate-500">
                        Decision: {choice.toUpperCase()}
                      </p>
                    </div>
                  );
                })}

                {proposals.length === 0 && (
                  <p className="text-sm text-slate-600">
                    No applicable edits were generated.
                  </p>
                )}

                <button
                  onClick={submitEditDecisions}
                  disabled={submittingEdits || proposals.length === 0}
                  className="flex items-center gap-2 rounded-xl bg-indigo-600 px-6 py-3 font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {submittingEdits ? (
                    <LoaderCircle
                      size={18}
                      className="animate-spin"
                    />
                  ) : (
                    <CheckCircle2 size={18} />
                  )}
                  {submittingEdits
                    ? "Applying Decisions..."
                    : "Submit Edit Decisions"}
                </button>
              </div>
            )}

            {/* Tailored Resume */}
            {analysis.tailored_resume != null && (
              <div className="rounded-2xl border border-emerald-200 bg-white p-6 shadow-sm">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <h3 className="text-xl font-semibold">
                    Tailored Resume
                  </h3>

                  <button
                    onClick={downloadResume}
                    disabled={!analysis.tailored_resume}
                    className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-60"
                  >
                    <Download size={17} />
                    Download TXT
                  </button>
                </div>

                <p className="mt-2 text-sm text-slate-600">
                  Generated using your approved edits.
                  Review the final text before using it.
                </p>

                <pre className="mt-5 max-h-[650px] overflow-auto whitespace-pre-wrap break-words rounded-xl bg-slate-50 p-5 text-sm leading-relaxed text-slate-800">
                  {analysis.tailored_resume}
                </pre>
              </div>
            )}

            {/* Status */}
            {reviewMessage && (
              <div
                role="status"
                className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800"
              >
                {reviewMessage}
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
