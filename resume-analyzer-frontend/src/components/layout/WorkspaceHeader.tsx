import { ArrowLeft, ArrowUpRight, FilePlus2 } from "lucide-react";

type Props = { onBack: () => void; onNew: () => void; hasAnalysis: boolean };

export default function WorkspaceHeader({ onBack, onNew, hasAnalysis }: Props) {
  return (
    <header className="ra-ws-header">
      <button className="ra-ws-brand" type="button" onClick={onBack} aria-label="Return to Resume Analyzer home">
        <span className="ra-ws-brand-icon" aria-hidden="true">🖥️</span>
        <span>Resume Analyzer</span>
      </button>
      <div className="ra-ws-header-actions">
        <span className="ra-ws-header-caption">YOUR CAREER WORKSPACE</span>
        {hasAnalysis && <button className="ra-ws-btn ra-ws-btn--subtle ra-ws-btn--sm" type="button" onClick={onNew}><FilePlus2 size={16} /> New analysis</button>}
        <button className="ra-ws-btn ra-ws-btn--text ra-ws-btn--sm" type="button" onClick={onBack}><ArrowLeft size={16} /> Home <ArrowUpRight size={13} /></button>
      </div>
    </header>
  );
}
