import { FileText } from "lucide-react";

type Props = { value: string; onChange: (value: string) => void; disabled: boolean };
export default function ResumeInput({ value, onChange, disabled }: Props) {
  return (
    <section className="ra-ws-input-card" aria-labelledby="ra-resume-label">
      <div className="ra-ws-input-head"><span className="ra-ws-input-icon"><FileText size={21} aria-hidden="true" /></span><div><h2 id="ra-resume-label">Your resume</h2><p>The experience behind the application.</p></div><span className="ra-ws-input-index">01 / 02</span></div>
      <label className="ra-ws-sr-only" htmlFor="ra-resume">Paste your resume text</label>
      <textarea id="ra-resume" className="ra-ws-textarea" value={value} onChange={(e) => onChange(e.target.value)} disabled={disabled} placeholder="Paste your complete resume here...\n\nInclude experience, projects, skills and education." spellCheck={false} />
      <div className="ra-ws-input-foot"><span>Paste resume text · File upload coming later</span><span>{value.trim().length.toLocaleString()} characters</span></div>
    </section>
  );
}
