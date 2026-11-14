import { ArrowUpRight, ArrowRight, Check, FileText, ShieldCheck, Sparkles, AlertCircle } from "lucide-react";

type Props = { onStart: () => void };

function ProductPreview() {
  return (
    <div className="ra-product-preview" aria-label="Illustrative Resume Analyzer results dashboard">
      <div className="ra-preview-top">
        <div className="ra-preview-title"><span className="ra-preview-dot" /> Resume analysis</div>
        <span className="ra-preview-sample">SAMPLE REPORT</span>
      </div>
      <div className="ra-preview-content">
        <div className="ra-preview-heading">
          <div>
            <span className="ra-mini-label">ROLE COMPARISON</span>
            <h3>AI Engineer</h3>
            <p>A clearer picture of your qualifications.</p>
          </div>
          <span className="ra-preview-complete"><Check size={13} /> Complete</span>
        </div>
        <div className="ra-preview-grid">
          <div className="ra-preview-score">
            <div className="ra-preview-score-ring">
              <div><strong>84<span>%</span></strong><small>JD alignment</small></div>
            </div>
            <div className="ra-preview-score-meta"><span className="ra-preview-positive" /> 12 requirements matched</div>
          </div>
          <div className="ra-preview-findings">
            <div className="ra-preview-finding"><span className="ra-finding-icon ra-finding-icon--success"><Check size={15} /></span><span><strong>Python & FastAPI</strong><small>Evidence found in experience</small></span></div>
            <div className="ra-preview-finding"><span className="ra-finding-icon ra-finding-icon--success"><ShieldCheck size={15} /></span><span><strong>LLM workflows</strong><small>Supported by project details</small></span></div>
            <div className="ra-preview-finding"><span className="ra-finding-icon ra-finding-icon--warning"><AlertCircle size={15} /></span><span><strong>Cloud deployment</strong><small>Additional evidence may help</small></span></div>
          </div>
        </div>
        <div className="ra-preview-foot"><span><Sparkles size={15} /> Evidence-backed insights</span><span>View breakdown <ArrowRight size={14} /></span></div>
      </div>
      <div className="ra-floating-note"><span className="ra-floating-note__icon"><FileText size={17}/></span><div><strong>Your resume, understood.</strong><small>Not just scanned for keywords.</small></div></div>
    </div>
  );
}

export default function Hero({ onStart }: Props) {
  return (
    <section className="ra-hero" id="top">
      <div className="ra-hero-copy">
        <div className="ra-eyebrow"><span className="ra-eyebrow-dot" /> THE SMARTER WAY TO APPLY</div>
        <h1>Your resume deserves a <em>closer look.</em></h1>
        <p className="ra-hero-description">Know what matches, understand what's missing, and improve your resume with evidence—not guesswork.</p>
        <div className="ra-hero-actions">
          <button type="button" className="ra-button ra-button--primary ra-button--large" onClick={onStart}>Analyze your resume <ArrowUpRight size={19} aria-hidden="true" /></button>
          <a className="ra-button ra-button--outline ra-button--large" href="#how-it-works">See how it works <ArrowRight size={17} aria-hidden="true" /></a>
        </div>
        <div className="ra-hero-footnote"><ShieldCheck size={16} aria-hidden="true" /> Honest insights. You approve every edit.</div>
      </div>
      <div className="ra-hero-visual"><div className="ra-hero-visual__frame"><ProductPreview /></div><div className="ra-hero-orbit ra-hero-orbit--one" /><div className="ra-hero-orbit ra-hero-orbit--two" /></div>
    </section>
  );
}
