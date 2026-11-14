import { ArrowUpRight, FileSearch, ListChecks, PencilLine, ShieldCheck } from "lucide-react";

const features = [
  { icon: FileSearch, number: "01", title: "See what really matches", description: "Compare your resume with a job description, requirement by requirement." },
  { icon: ShieldCheck, number: "02", title: "Trust the evidence", description: "Understand which parts of your resume support each assessment." },
  { icon: PencilLine, number: "03", title: "Improve without inventing", description: "Review suggested rewrites and keep complete control of what changes." },
];

export default function FeatureShowcase() {
  return (
    <section className="ra-features ra-section" id="features">
      <div className="ra-section-heading">
        <div><span className="ra-section-kicker">WHY IT MATTERS</span><h2>Less guessing.<br/><em>More clarity.</em></h2></div>
        <p>Your experience is more than a list of keywords. Get useful, explainable insights before you hit apply.</p>
      </div>
      <div className="ra-feature-grid">
        {features.map(({ icon: Icon, number, title, description }) => (
          <article className="ra-feature" key={number}>
            <div className="ra-feature-top"><span className="ra-feature-icon"><Icon size={24} strokeWidth={1.6} aria-hidden="true" /></span><span className="ra-feature-number">{number} / 03</span></div>
            <h3>{title}</h3><p>{description}</p><ArrowUpRight size={19} className="ra-feature-arrow" aria-hidden="true" />
          </article>
        ))}
      </div>
      <div className="ra-insight-showcase" id="why-us">
        <div className="ra-insight-copy"><span className="ra-section-kicker">BUILT FOR TRANSPARENCY</span><h2>Every insight has a <em>reason.</em></h2><p>See each requirement, the matching evidence, and what still needs review. A score should start a conversation—not end it.</p><div className="ra-insight-rule"><ListChecks size={19} /> Requirement-by-requirement breakdown</div><div className="ra-insight-rule"><ShieldCheck size={19} /> Human-reviewed improvements</div></div>
        <div className="ra-insight-visual">
          <div className="ra-insight-panel"><div className="ra-insight-panel-header"><span>Requirement analysis</span><span className="ra-preview-sample">EXAMPLE</span></div>
            <div className="ra-requirement-item"><div><strong>Python development</strong><small>Verified in recent experience</small></div><span className="ra-chip ra-chip--success">Matched</span></div>
            <div className="ra-requirement-item"><div><strong>Cloud infrastructure</strong><small>Evidence needs review</small></div><span className="ra-chip ra-chip--partial">Partial</span></div>
            <div className="ra-requirement-item"><div><strong>Kubernetes</strong><small>No evidence provided</small></div><span className="ra-chip">Unknown</span></div>
            <div className="ra-insight-panel-footer"><span><ShieldCheck size={15} /> Human review included</span><span>Sample data</span></div>
          </div>
        </div>
      </div>
    </section>
  );
}
