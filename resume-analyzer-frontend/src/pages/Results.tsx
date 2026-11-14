import { ArrowLeft, ArrowRight, CheckCircle2, ShieldCheck } from "lucide-react";
import ScoreOverview from "../components/analyzer/ScoreOverview";
import RequirementList from "../components/analyzer/RequirementList";
import ReviewPanel from "../components/analyzer/ReviewPanel";
import Suggestions from "../components/analyzer/Suggestions";
import type { AnalysisResponse, MatchStatus } from "../types/analysis";

type Counts = { met: number; partially_met: number; not_met: number; unknown: number };
type Props = {
  analysis: AnalysisResponse;
  counts: Counts;
  reviewEnabled: boolean;
  reviewStatuses: Record<string, MatchStatus>;
  onReviewStatus: (id: string, status: MatchStatus) => void;
  additionalInfo: string;
  onAdditionalInfo: (value: string) => void;
  optimize: boolean;
  onOptimize: (value: boolean) => void;
  onSubmitReview: () => void;
  onBack: () => void;
  onStudio: () => void;
  onFinal: () => void;
  loading: boolean;
};

export default function Results({ analysis, counts, reviewEnabled, reviewStatuses, onReviewStatus, additionalInfo, onAdditionalInfo, optimize, onOptimize, onSubmitReview, onBack, onStudio, onFinal, loading }: Props) {
  const editReviewReady = analysis.status === "paused" && analysis.next_nodes.includes("review_resume_edits");
  return <div className="ra-ws-page ra-ws-results">
    <div className="ra-ws-page-heading"><div><span className="ra-ws-eyebrow"><ShieldCheck size={15}/> YOUR ANALYSIS REPORT</span><h1>Here's how your resume <em>stacks up.</em></h1><p>Your results, backed by explanations—not made-up hiring probabilities.</p></div><div className="ra-ws-heading-index">02 <span>/</span> 04</div></div>
    <ScoreOverview analysis={analysis} counts={counts}/>
    <div className="ra-ws-results-grid"><RequirementList matches={analysis.requirement_matches} reviewEnabled={reviewEnabled} reviewStatuses={reviewStatuses} onReviewStatus={onReviewStatus}/><ReviewPanel hardGaps={analysis.hard_gaps} reviewEnabled={reviewEnabled} loading={loading} additionalInfo={additionalInfo} onAdditionalInfo={onAdditionalInfo} optimize={optimize} onOptimize={onOptimize} onReview={onSubmitReview} hasSuggestions={analysis.resume_suggestions != null}/></div>
    <Suggestions value={analysis.resume_suggestions}/>
    {editReviewReady && <div className="ra-ws-next-panel"><div><span className="ra-ws-eyebrow">NEXT UP</span><h2>Improve it, on your terms.</h2><p>Review each proposed edit before anything changes.</p></div><button type="button" className="ra-ws-btn ra-ws-btn--primary" onClick={onStudio}>Open Resume Studio <ArrowRight size={18}/></button></div>}
    {analysis.tailored_resume && <div className="ra-ws-next-panel"><div><span className="ra-ws-eyebrow"><CheckCircle2 size={15}/> REVIEW COMPLETE</span><h2>Your approved resume is ready.</h2><p>View the final content and download the TXT file.</p></div><button type="button" className="ra-ws-btn ra-ws-btn--primary" onClick={onFinal}>View final resume <ArrowRight size={18}/></button></div>}
    {analysis.status === "completed" && !editReviewReady && !analysis.tailored_resume && <div className="ra-ws-complete-note"><CheckCircle2 size={19}/> Your analysis is complete. You can revisit its breakdown or start another comparison.</div>}
    <div className="ra-ws-bottom-actions"><button type="button" className="ra-ws-btn ra-ws-btn--subtle" onClick={onBack}><ArrowLeft size={17}/> Back to inputs</button></div>
  </div>;
}
