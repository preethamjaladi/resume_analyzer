import { AlertTriangle, ArrowRight, ClipboardCheck, LockKeyhole, Sparkles } from "lucide-react";

type Props = {
  hardGaps: string[];
  reviewEnabled: boolean;
  loading: boolean;
  additionalInfo: string;
  onAdditionalInfo: (value: string) => void;
  optimize: boolean;
  onOptimize: (value: boolean) => void;
  onReview: () => void;
  hasSuggestions: boolean;
};

export default function ReviewPanel({ hardGaps, reviewEnabled, loading, additionalInfo, onAdditionalInfo, optimize, onOptimize, onReview, hasSuggestions }: Props) {
  return <aside className="ra-ws-review-aside">
    <section className="ra-ws-aside-card">
      <div className="ra-ws-aside-title"><AlertTriangle size={18} aria-hidden="true"/><h3>Mandatory gaps</h3><span>{hardGaps.length}</span></div>
      {hardGaps.length === 0 ? <p className="ra-ws-side-muted">No mandatory gaps were returned in this analysis.</p> : <ul className="ra-ws-gap-list">{hardGaps.map((gap, idx) => <li key={`${idx}-${gap}`}>{gap}</li>)}</ul>}
    </section>
    <section className="ra-ws-aside-card ra-ws-review-card">
      <div className="ra-ws-aside-title"><ClipboardCheck size={18} aria-hidden="true"/><h3>Human review</h3></div>
      {reviewEnabled ? <>
        <p>AI can miss context. Open the requirements, verify each classification, then continue.</p>
        <label className="ra-ws-field-label" htmlFor="ra-additional-info">Additional truthful context <span>(optional)</span></label>
        <textarea id="ra-additional-info" className="ra-ws-small-textarea" placeholder="Additional relevant experience or context..." value={additionalInfo} onChange={(e) => onAdditionalInfo(e.target.value)} disabled={loading}/>
        <p className="ra-ws-mini-note">Additional context informs optimization; it does not automatically change the score.</p>
        <label className="ra-ws-switch-row"><input type="checkbox" checked={optimize} onChange={(e) => onOptimize(e.target.checked)} disabled={loading}/><span><strong>Generate resume improvements</strong><small>Review each proposed change before it is applied.</small></span><Sparkles size={18} aria-hidden="true"/></label>
        <button className="ra-ws-btn ra-ws-btn--primary ra-ws-btn--full" type="button" onClick={onReview} disabled={loading}>{loading ? "Submitting review…" : "Submit review"}<ArrowRight size={17} /></button>
      </> : <><p>The review stage has been completed or is not available. {hasSuggestions ? "Your improvement suggestions appear below." : "You can examine the report and start another analysis."}</p><div className="ra-ws-reviewed-note"><LockKeyhole size={15}/> Only approved edits are applied to your final resume.</div></>}
    </section>
  </aside>;
}
