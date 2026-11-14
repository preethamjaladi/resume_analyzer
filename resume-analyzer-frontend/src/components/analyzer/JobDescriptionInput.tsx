import { BriefcaseBusiness } from "lucide-react";

type Props = { value: string; onChange: (value: string) => void; disabled: boolean };
export default function JobDescriptionInput({ value, onChange, disabled }: Props) {
  return (
    <section className="ra-ws-input-card" aria-labelledby="ra-jd-label">
      <div className="ra-ws-input-head"><span className="ra-ws-input-icon"><BriefcaseBusiness size={21} aria-hidden="true" /></span><div><h2 id="ra-jd-label">Job description</h2><p>What your next role is looking for.</p></div><span className="ra-ws-input-index">02 / 02</span></div>
      <label className="ra-ws-sr-only" htmlFor="ra-jd">Paste the job description</label>
      <textarea id="ra-jd" className="ra-ws-textarea" value={value} onChange={(e) => onChange(e.target.value)} disabled={disabled} placeholder="Paste the full job description...\n\nInclude required and preferred qualifications." spellCheck={false} />
      <div className="ra-ws-input-foot"><span>Include qualifications and responsibilities</span><span>{value.trim().length.toLocaleString()} characters</span></div>
    </section>
  );
}
