import { useState } from "react";
import { ArrowRight, CircleCheck, FileText, LoaderCircle, ShieldCheck, Sparkles, X } from "lucide-react";
import WorkspaceHeader from "../components/layout/WorkspaceHeader";
import ResumeInput from "../components/analyzer/ResumeInput";
import JobDescriptionInput from "../components/analyzer/JobDescriptionInput";
import Results from "./Results";
import ResumeStudio from "./ResumeStudio";
import FinalResume from "./FinalResume";
import { useAnalysis } from "../hooks/useAnalysis";

type Stage = "input" | "results" | "studio" | "final";
type Props = { onBack: () => void };

export default function Analyzer({ onBack }: Props) {
  const [stage, setStage] = useState<Stage>("input");
  const workflow = useAnalysis();
  const busy = workflow.operation !== null;

  const scrollTop = () => window.scrollTo({ top: 0, behavior: "auto" });
  const go = (next: Stage) => { setStage(next); scrollTop(); };
  const startNew = () => { workflow.reset(); go("input"); };

  const analyze = async () => { if (await workflow.analyze()) go("results"); };
  const review = async () => {
    const data = await workflow.submitReview();
    if (data?.next_nodes.includes("review_resume_edits")) go("studio");
    else if (data?.tailored_resume) go("final");
    else if (data) scrollTop();
  };
  const edits = async () => {
    const data = await workflow.submitEdits();
    if (data?.tailored_resume) go("final");
    else if (data?.status === "completed") go("results");
  };

  return <div className="ra-app ra-workspace">
    <WorkspaceHeader onBack={onBack} onNew={startNew} hasAnalysis={workflow.analysis !== null}/>
    <nav className="ra-ws-progress" aria-label="Analysis stages">
      {([
        ["input", "01", "Analyze"],
        ["results", "02", "Review"],
        ["studio", "03", "Improve"],
        ["final", "04", "Export"],
      ] as const).map(([key, number, name]) => {
        const available = key === "input" || (key === "results" && workflow.analysis !== null) ||
          (key === "studio" && workflow.isEditReview) ||
          (key === "final" && !!workflow.analysis?.tailored_resume);
        return <button key={key} type="button" className={stage === key ? "is-current" : ""} disabled={!available || busy} onClick={() => go(key)} aria-current={stage === key ? "step" : undefined}><span>{number}</span>{name}</button>;
      })}
    </nav>
    <main>
      {workflow.error && <div className="ra-ws-global-notice ra-ws-global-notice--error" role="alert"><span>{workflow.error}</span><button aria-label="Dismiss error" onClick={() => workflow.setError("")}><X size={17}/></button></div>}
      {workflow.message && <div className="ra-ws-global-notice ra-ws-global-notice--success" role="status"><CircleCheck size={17}/><span>{workflow.message}</span><button aria-label="Dismiss message" onClick={() => workflow.setMessage("")}><X size={17}/></button></div>}
      {stage === "input" && <div className="ra-ws-page ra-ws-input-page">
        <div className="ra-ws-page-heading ra-ws-input-intro"><div><span className="ra-ws-eyebrow"><span className="ra-ws-eyebrow-dot"/> YOUR NEXT OPPORTUNITY STARTS HERE</span><h1>Understand your <em>next move.</em></h1><p>Two inputs. One honest comparison. Discover what matches, where the gaps are, and what you can improve.</p></div><div className="ra-ws-heading-index">01 <span>/</span> 04</div></div>
        <div className="ra-ws-input-grid"><ResumeInput value={workflow.resume} onChange={workflow.setResume} disabled={busy}/><JobDescriptionInput value={workflow.jobDescription} onChange={workflow.setJobDescription} disabled={busy}/></div>
        <div className="ra-ws-analyze-bar"><div className="ra-ws-analyze-assurance"><ShieldCheck size={21}/><span><strong>Evidence over guesswork.</strong><small>Evidence first. You approve every edit.</small></span></div><button type="button" className="ra-ws-btn ra-ws-btn--primary ra-ws-btn--large" onClick={analyze} disabled={busy || !workflow.resume.trim() || !workflow.jobDescription.trim()}>{workflow.operation === "analyzing" ? <LoaderCircle className="ra-ws-spinner" size={19}/> : <Sparkles size={19}/>} {workflow.operation === "analyzing" ? "Analyzing your resume…" : "Analyze my resume"}<ArrowRight size={18}/></button></div>
        <div className="ra-ws-process-strip"><div><FileText size={20}/><span>Understand your experience</span></div><ArrowRight size={16}/><div><ShieldCheck size={20}/><span>Compare requirements</span></div><ArrowRight size={16}/><div><CircleCheck size={20}/><span>Review your results</span></div></div>
      </div>}
      {stage === "results" && workflow.analysis && <Results analysis={workflow.analysis} counts={workflow.counts} reviewEnabled={workflow.isHumanReview} reviewStatuses={workflow.reviewStatuses} onReviewStatus={workflow.setReviewStatus} additionalInfo={workflow.additionalInfo} onAdditionalInfo={workflow.setAdditionalInfo} optimize={workflow.optimize} onOptimize={workflow.setOptimize} onSubmitReview={review} loading={busy} onBack={() => go("input")} onStudio={() => go("studio")} onFinal={() => go("final")}/>}
      {stage === "studio" && workflow.analysis && <ResumeStudio proposals={workflow.analysis.edit_proposals ?? []} editChoices={workflow.editChoices} editedTexts={workflow.editedTexts} onChoice={workflow.setEditChoice} onEditText={workflow.setEditedText} onSubmit={edits} onBack={() => go("results")} loading={busy}/>}
      {stage === "final" && workflow.analysis?.tailored_resume && <FinalResume content={workflow.analysis.tailored_resume} proposals={workflow.analysis.edit_proposals ?? []} choices={workflow.editChoices} onBack={() => go("results")} onNew={startNew}/>}
    </main>
    <footer className="ra-ws-footer"><span>🖥️ <strong>Resume Analyzer</strong></span><span>Made for thoughtful, evidence-backed applications.</span><span>You're in control of every change.</span></footer>
  </div>;
}
