import { Lightbulb } from "lucide-react";
import { isResumeSuggestions } from "../../types/analysis";

type Props = { value: unknown };
export default function Suggestions({ value }: Props) {
  if (value == null) return null;
  return <section className="ra-ws-suggestions"><div className="ra-ws-section-heading"><div><span className="ra-ws-eyebrow">YOUR NEXT STEPS</span><h2>Improvement suggestions</h2><p>Recommendations are not approved edits. Verify them against your actual experience.</p></div></div>
    {isResumeSuggestions(value) && value.suggestions.length > 0 ?
      <div className="ra-ws-suggestion-grid">{value.suggestions.map((suggestion, idx) => <article className="ra-ws-suggestion" key={`${suggestion.section}-${idx}`}><div className="ra-ws-suggestion-top"><span className="ra-ws-suggestion-icon"><Lightbulb size={19}/></span><span className={`ra-ws-priority ra-ws-priority--${suggestion.priority}`}>{suggestion.priority} priority</span></div><h3>{suggestion.section} · {suggestion.action}</h3><p>{suggestion.reason}</p><div className="ra-ws-proposed-copy">{suggestion.suggested_text}</div></article>)}</div>
    : <pre className="ra-ws-raw-suggestions">{typeof value === "string" ? value : JSON.stringify(value, null, 2)}</pre>}
  </section>;
}
