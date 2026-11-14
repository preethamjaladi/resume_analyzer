import { useMemo, useState } from "react";
import { analysisAPI } from "../services/api";
import type {
  AnalysisResponse,
  EditChoice,
  EditReviewDecision,
  MatchStatus,
  RequirementReviewDecision,
} from "../types/analysis";

type Operation = "analyzing" | "reviewing" | "applying" | null;

export function useAnalysis() {
  const [resume, setResume] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [operation, setOperation] = useState<Operation>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [reviewStatuses, setReviewStatuses] = useState<Record<string, MatchStatus>>({});
  const [additionalInfo, setAdditionalInfo] = useState("");
  const [optimize, setOptimize] = useState(false);
  const [editChoices, setEditChoices] = useState<Record<string, EditChoice>>({});
  const [editedTexts, setEditedTexts] = useState<Record<string, string>>({});

  const isHumanReview = !!analysis && analysis.status === "paused" && analysis.next_nodes.includes("human_review");
  const isEditReview = !!analysis && analysis.status === "paused" && analysis.next_nodes.includes("review_resume_edits");

  const counts = useMemo(() => ({
    met: (analysis?.requirement_matches ?? []).filter((m) => m.status === "met").length,
    partially_met: (analysis?.requirement_matches ?? []).filter((m) => m.status === "partially_met").length,
    not_met: (analysis?.requirement_matches ?? []).filter((m) => m.status === "not_met").length,
    unknown: (analysis?.requirement_matches ?? []).filter((m) => m.status === "unknown").length,
  }), [analysis]);

  const applyResponse = (data: AnalysisResponse, preserveEdits = false) => {
    setAnalysis(data);
    setReviewStatuses(Object.fromEntries(data.requirement_matches.map((m) => [m.requirement_id, m.status])));
    if (!preserveEdits) {
      setEditChoices(Object.fromEntries((data.edit_proposals ?? []).map((p) => [p.edit_id, "reject" as EditChoice])));
      setEditedTexts(Object.fromEntries((data.edit_proposals ?? []).map((p) => [p.edit_id, p.proposed_text])));
    }
  };

  const reset = () => {
    setAnalysis(null);
    setJobDescription("");
    setError("");
    setMessage("");
    setAdditionalInfo("");
    setOptimize(false);
    setReviewStatuses({});
    setEditChoices({});
    setEditedTexts({});
  };

  const analyze = async (): Promise<boolean> => {
    if (!resume.trim() || !jobDescription.trim()) {
      setError("Paste both your resume and the job description to continue.");
      return false;
    }
    setOperation("analyzing");
    setError("");
    setMessage("");
    try {
      const data = await analysisAPI.start(resume, jobDescription);
      applyResponse(data);
      return true;
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "We couldn't analyze your resume.");
      return false;
    } finally {
      setOperation(null);
    }
  };

  const submitReview = async (): Promise<AnalysisResponse | null> => {
    if (!analysis || !isHumanReview) return null;
    const reviews: RequirementReviewDecision[] = analysis.requirement_matches.map((match) => {
      const selected = reviewStatuses[match.requirement_id] ?? match.status;
      return selected === match.status
        ? { requirement_id: match.requirement_id, decision: "approve" }
        : { requirement_id: match.requirement_id, decision: "correct", corrected_status: selected, reason: "Corrected during human review" };
    });
    setOperation("reviewing");
    setError("");
    setMessage("");
    try {
      const data = await analysisAPI.submitReview(
        analysis.thread_id, reviews,
        additionalInfo.trim() ? [additionalInfo.trim()] : [],
        optimize,
      );
      applyResponse(data);
      setMessage(data.next_nodes.includes("review_resume_edits")
        ? "Review saved. Your resume suggestions are ready for approval."
        : "Review complete. Your updated analysis is ready.");
      return data;
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "We couldn't submit your review.");
      return null;
    } finally {
      setOperation(null);
    }
  };

  const submitEdits = async (): Promise<AnalysisResponse | null> => {
    if (!analysis || !isEditReview) return null;
    const proposals = analysis.edit_proposals ?? [];
    if (proposals.length === 0) {
      setError("There are no proposed edits to submit.");
      return null;
    }
    const decisions: EditReviewDecision[] = proposals.map((proposal) => {
      const decision = editChoices[proposal.edit_id] ?? "reject";
      return decision === "edit"
        ? { edit_id: proposal.edit_id, decision, edited_text: editedTexts[proposal.edit_id] ?? "" }
        : { edit_id: proposal.edit_id, decision };
    });
    if (decisions.some((d) => d.decision === "edit" && !d.edited_text?.trim())) {
      setError("Custom replacements cannot be empty. Update the text before submitting.");
      return null;
    }
    setOperation("applying");
    setError("");
    setMessage("");
    try {
      const data = await analysisAPI.submitEdits(analysis.thread_id, decisions);
      applyResponse(data, true);
      setMessage(data.tailored_resume
        ? "Your approved changes have been applied. Review the final resume before using it."
        : "Edit decisions submitted.");
      return data;
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "We couldn't apply your edit decisions.");
      return null;
    } finally {
      setOperation(null);
    }
  };

  const setReviewStatus = (id: string, status: MatchStatus) => {
    setReviewStatuses((prev) => ({ ...prev, [id]: status }));
  };
  const setEditChoice = (id: string, choice: EditChoice) => {
    setEditChoices((prev) => ({ ...prev, [id]: choice }));
  };
  const setEditedText = (id: string, value: string) => {
    setEditedTexts((prev) => ({ ...prev, [id]: value }));
  };

  return {
    resume, setResume, jobDescription, setJobDescription,
    analysis, operation, error, message, counts, isHumanReview, isEditReview,
    reviewStatuses, setReviewStatus, additionalInfo, setAdditionalInfo,
    optimize, setOptimize, editChoices, setEditChoice, editedTexts, setEditedText,
    analyze, reset, submitReview, submitEdits, setError, setMessage,
  };
}
