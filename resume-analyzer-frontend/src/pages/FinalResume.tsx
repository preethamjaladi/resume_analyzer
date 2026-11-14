import { ArrowLeft, CheckCircle2, Download, FileCheck2, ShieldCheck } from "lucide-react";
import ResumePreview from "../components/editor/ResumePreview";
import type { EditChoice, ResumeEditProposal } from "../types/analysis";

type Props = { content: string; proposals: ResumeEditProposal[]; choices: Record<string, EditChoice>; onBack: () => void; onNew: () => void };
export default function FinalResume({ content, proposals, choices, onBack, onNew }: Props) {
  const approved = proposals.filter((p) => choices[p.edit_id] === "accept").length;
  const modified = proposals.filter((p) => choices[p.edit_id] === "edit").length;
  const rejected = proposals.length - approved - modified;
  const download = () => {
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "tailored_resume.txt";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  };
  return <div className="ra-ws-page ra-ws-final">
    <div className="ra-ws-page-heading"><div><span className="ra-ws-eyebrow"><CheckCircle2 size={15}/> REVIEW COMPLETE</span><h1>Your resume, <em>refined.</em></h1><p>Approved changes have been applied. Read through the final text before using it for an application.</p></div><div className="ra-ws-heading-index">04 <span>/</span> 04</div></div>
    <div className="ra-ws-final-grid"><ResumePreview content={content} onDownload={download}/><aside className="ra-ws-final-aside"><div className="ra-ws-aside-card ra-ws-final-success"><FileCheck2 size={31}/><h2>Ready for your review.</h2><p>This version reflects the edit decisions you submitted.</p><div className="ra-ws-final-stats"><div><strong>{approved}</strong><span>Accepted</span></div><div><strong>{modified}</strong><span>Modified</span></div><div><strong>{rejected}</strong><span>Rejected</span></div></div><button className="ra-ws-btn ra-ws-btn--primary ra-ws-btn--full" type="button" onClick={download}><Download size={17}/> Download TXT</button></div><div className="ra-ws-aside-card"><div className="ra-ws-aside-title"><ShieldCheck size={18}/><h3>Before you apply</h3></div><p>This preview is plain text, not a formatted PDF or DOCX. Double-check names, dates, claims and formatting after downloading.</p></div><button className="ra-ws-btn ra-ws-btn--subtle ra-ws-btn--full" type="button" onClick={onNew}>Start another analysis</button></aside></div>
    <div className="ra-ws-bottom-actions"><button className="ra-ws-btn ra-ws-btn--text" type="button" onClick={onBack}><ArrowLeft size={17}/> View analysis</button></div>
  </div>;
}
