import { ArrowLeft, ArrowRight, ShieldCheck, Sparkles } from "lucide-react";
import EditProposal from "../components/editor/EditProposal";
import type { EditChoice, ResumeEditProposal } from "../types/analysis";

type Props = {
  proposals: ResumeEditProposal[];
  editChoices: Record<string, EditChoice>;
  editedTexts: Record<string, string>;
  onChoice: (id: string, choice: EditChoice) => void;
  onEditText: (id: string, value: string) => void;
  onSubmit: () => void;
  onBack: () => void;
  loading: boolean;
};

export default function ResumeStudio({ proposals, editChoices, editedTexts, onChoice, onEditText, onSubmit, onBack, loading }: Props) {
  const accepted = proposals.filter((p) => editChoices[p.edit_id] === "accept").length;
  const modified = proposals.filter((p) => editChoices[p.edit_id] === "edit").length;
  const rejected = proposals.length - accepted - modified;
  return <div className="ra-ws-page ra-ws-studio">
    <div className="ra-ws-page-heading"><div><span className="ra-ws-eyebrow"><Sparkles size={15}/> HUMAN-APPROVED IMPROVEMENTS</span><h1>Make every word <em>count.</em></h1><p>Compare every suggestion with your actual experience. You decide what changes—and what stays.</p></div><div className="ra-ws-heading-index">03 <span>/</span> 04</div></div>
    <div className="ra-ws-studio-summary"><div><strong>{proposals.length}</strong><span>Suggested edits</span></div><div><strong>{accepted}</strong><span>Accepted</span></div><div><strong>{modified}</strong><span>Modified</span></div><div><strong>{rejected}</strong><span>Kept unchanged</span></div><p><ShieldCheck size={16}/> Every edit starts rejected until you choose otherwise.</p></div>
    <div className="ra-ws-edit-list">{proposals.map((proposal, index) => <EditProposal key={proposal.edit_id} proposal={proposal} index={index} choice={editChoices[proposal.edit_id] ?? "reject"} editedText={editedTexts[proposal.edit_id] ?? proposal.proposed_text} onChoice={onChoice} onEditText={onEditText}/>)}</div>
    {proposals.length === 0 && <div className="ra-ws-empty-state">No proposed edits were returned. You can go back to the analysis report.</div>}
    <div className="ra-ws-bottom-actions"><button className="ra-ws-btn ra-ws-btn--subtle" type="button" onClick={onBack}><ArrowLeft size={17}/> Back to analysis</button><button className="ra-ws-btn ra-ws-btn--primary" type="button" onClick={onSubmit} disabled={loading || proposals.length === 0}>{loading ? "Applying your decisions…" : "Apply my decisions"}<ArrowRight size={18}/></button></div>
  </div>;
}
