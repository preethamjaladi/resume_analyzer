import { CheckCircle2, CircleHelp, ShieldCheck, Target } from "lucide-react";
import type { AnalysisResponse } from "../../types/analysis";

type Counts = { met: number; partially_met: number; not_met: number; unknown: number };
type Props = { analysis: AnalysisResponse; counts: Counts };

export default function ScoreOverview({ analysis, counts }: Props) {
  const score = analysis.match_score == null ? null : Math.max(0, Math.min(100, analysis.match_score));
  const total = analysis.requirement_matches.length;
  return (
    <section className="ra-ws-overview" aria-label="Analysis summary">
      <div className="ra-ws-score-panel">
        <span className="ra-ws-eyebrow">YOUR JD ALIGNMENT</span>
        <div className="ra-ws-score-ring" style={{ background: `conic-gradient(var(--ra-coffee) ${score ?? 0}%, #453328 0)` }} role="img" aria-label={score === null ? "Alignment score unavailable" : `${score} percent job description alignment`}>
          <div className="ra-ws-score-ring-center"><strong>{score === null ? "—" : `${Math.round(score)}%`}</strong><small>alignment</small></div>
        </div>
        <p>Based on extracted job requirements, not a hiring probability or official ATS score.</p>
      </div>
      <div className="ra-ws-summary-panel">
        <div className="ra-ws-summary-heading"><div><span className="ra-ws-eyebrow">THE BIG PICTURE</span><h2>Clarity before your next application.</h2></div><Target size={26} aria-hidden="true" /></div>
        <p className="ra-ws-summary-blurb">See where your resume provides evidence, where the match is partial, and what deserves a second look.</p>
        <div className="ra-ws-count-grid">
          <div><CheckCircle2 size={18} className="ra-ws-good"/><strong>{counts.met}</strong><span>Matched</span></div>
          <div><ShieldCheck size={18} className="ra-ws-warm"/><strong>{counts.partially_met}</strong><span>Partial</span></div>
          <div><Target size={18} className="ra-ws-alert"/><strong>{counts.not_met}</strong><span>Not met</span></div>
          <div><CircleHelp size={18} className="ra-ws-muted-icon"/><strong>{counts.unknown}</strong><span>Unknown</span></div>
        </div>
        <div className="ra-ws-summary-bottom">{total} requirements assessed <span>•</span> Evidence-based comparison</div>
      </div>
    </section>
  );
}
