import { Check, Pencil, ShieldCheck, X } from "lucide-react";
import type { EditChoice, ResumeEditProposal } from "../../types/analysis";

type Props = {
  proposal: ResumeEditProposal;
  index: number;
  choice: EditChoice;
  editedText: string;
  onChoice: (id: string, choice: EditChoice) => void;
  onEditText: (id: string, text: string) => void;
};

export default function EditProposal({ proposal, index, choice, editedText, onChoice, onEditText }: Props) {
  return <article className="ra-ws-edit-card">
    <div className="ra-ws-edit-top"><div><span className="ra-ws-eyebrow">SUGGESTION {String(index + 1).padStart(2, "0")} · {proposal.operation.toUpperCase()}</span><h2>{proposal.section.replaceAll("_", " ")}</h2></div><span className="ra-ws-edit-id">{proposal.requirement_id ?? proposal.edit_id}</span></div>
    <div className="ra-ws-diff-grid"><section className="ra-ws-diff ra-ws-diff--original"><div className="ra-ws-diff-label"><span className="ra-ws-diff-dot"/>Original resume</div><p>{proposal.original_text || "(No existing text — proposed insertion)"}</p></section><section className="ra-ws-diff ra-ws-diff--proposed"><div className="ra-ws-diff-label"><span className="ra-ws-diff-dot"/>Suggested revision</div><p>{proposal.proposed_text || "(Proposed deletion)"}</p></section></div>
    <div className="ra-ws-edit-rationale"><div><ShieldCheck size={17}/> Why this change?</div><p>{proposal.reason}</p>{proposal.supporting_evidence?.length > 0 && <div className="ra-ws-edit-evidence"><strong>Supporting evidence</strong><ul>{proposal.supporting_evidence.map((evidence, i) => <li key={i}>{evidence}</li>)}</ul></div>}</div>
    <div className="ra-ws-edit-actions"><span>YOUR DECISION</span><div role="group" aria-label={`Decision for ${proposal.edit_id}`}><button type="button" className={choice === "accept" ? "is-selected" : ""} aria-pressed={choice === "accept"} onClick={() => onChoice(proposal.edit_id, "accept")}><Check size={16}/> Accept</button><button type="button" className={choice === "edit" ? "is-selected" : ""} aria-pressed={choice === "edit"} onClick={() => onChoice(proposal.edit_id, "edit")}><Pencil size={16}/> Edit</button><button type="button" className={choice === "reject" ? "is-selected" : ""} aria-pressed={choice === "reject"} onClick={() => onChoice(proposal.edit_id, "reject")}><X size={16}/> Reject</button></div></div>
    {choice === "edit" && <div className="ra-ws-edit-custom"><label htmlFor={`ra-edit-${proposal.edit_id}`}>Your replacement text</label><textarea id={`ra-edit-${proposal.edit_id}`} value={editedText} onChange={(e) => onEditText(proposal.edit_id, e.target.value)} rows={4} /></div>}
    <p className="ra-ws-edit-safety">{choice === "reject" ? "Original wording will be preserved unless you choose another option." : choice === "edit" ? "Your written replacement will be sent for application." : "The suggested revision will be applied once submitted."}</p>
  </article>;
}
