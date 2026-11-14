import { ChevronDown, FileSearch, SearchCheck } from "lucide-react";
import { useState } from "react";
import StatusBadge from "../ui/StatusBadge";
import type { MatchStatus, RequirementMatch } from "../../types/analysis";

const filterOptions: { label: string; value: MatchStatus | "all" }[] = [
  { label: "All", value: "all" }, { label: "Matched", value: "met" },
  { label: "Partial", value: "partially_met" }, { label: "Not met", value: "not_met" },
  { label: "Unknown", value: "unknown" },
];
const reviewOptions: { label: string; value: MatchStatus }[] = [
  { label: "Matched", value: "met" }, { label: "Partial", value: "partially_met" },
  { label: "Not met", value: "not_met" }, { label: "Unknown", value: "unknown" },
];

type Props = {
  matches: RequirementMatch[];
  reviewEnabled: boolean;
  reviewStatuses: Record<string, MatchStatus>;
  onReviewStatus: (id: string, status: MatchStatus) => void;
};

export default function RequirementList({ matches, reviewEnabled, reviewStatuses, onReviewStatus }: Props) {
  const [filter, setFilter] = useState<MatchStatus | "all">("all");
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const visible = matches.filter((match) => filter === "all" || match.status === filter);
  return (
    <section className="ra-ws-requirements" aria-labelledby="ra-requirements-title">
      <div className="ra-ws-section-heading"><div><span className="ra-ws-eyebrow">THE DETAILS</span><h2 id="ra-requirements-title">Requirement breakdown</h2><p>Every assessment has a reason. Open a row to inspect its evidence.</p></div><span className="ra-ws-count-tag">{matches.length} assessed</span></div>
      <div className="ra-ws-filters" role="group" aria-label="Filter requirements">
        {filterOptions.map((option) => <button key={option.value} type="button" aria-pressed={filter === option.value} className={`ra-ws-filter ${filter === option.value ? "is-active" : ""}`} onClick={() => setFilter(option.value)}>{option.label}</button>)}
      </div>
      <div className="ra-ws-requirement-list">
        {visible.map((match) => {
          const open = !!expanded[match.requirement_id];
          const corrected = reviewStatuses[match.requirement_id] ?? match.status;
          return <article key={match.requirement_id} className={`ra-ws-requirement ${open ? "is-open" : ""}`}>
            <button type="button" className="ra-ws-requirement-toggle" aria-expanded={open} onClick={() => setExpanded((prev) => ({ ...prev, [match.requirement_id]: !prev[match.requirement_id] }))}>
              <span className="ra-ws-requirement-symbol"><FileSearch size={17} aria-hidden="true" /></span>
              <span className="ra-ws-requirement-copy"><small>{match.requirement_id} · {match.match_type === "semantic" ? "Semantic comparison" : match.match_type === "exact" ? "Direct comparison" : "Requirement comparison"}</small><strong>{match.explanation || "Requirement assessment"}</strong></span>
              <StatusBadge status={match.status}/>
              <ChevronDown className="ra-ws-chevron" size={18} aria-hidden="true" />
            </button>
            {open && <div className="ra-ws-requirement-body">
              <div className="ra-ws-evidence"><div className="ra-ws-evidence-heading"><SearchCheck size={17}/> Supporting evidence</div><p>{match.evidence?.trim() || "No supporting evidence was returned for this requirement."}</p></div>
              {reviewEnabled && <div className="ra-ws-review-field"><label htmlFor={`ra-review-${match.requirement_id}`}>Your assessment</label><select id={`ra-review-${match.requirement_id}`} value={corrected} onChange={(e) => onReviewStatus(match.requirement_id, e.target.value as MatchStatus)}>{reviewOptions.map((o) => <option value={o.value} key={o.value}>{o.label}</option>)}</select>{corrected !== match.status && <span>Changed from {match.status.replaceAll("_", " ")}. Your correction will be submitted for review.</span>}</div>}
            </div>}
          </article>;
        })}
        {visible.length === 0 && <div className="ra-ws-empty-filter">No requirements in this category. Choose another filter.</div>}
      </div>
      <p className="ra-ws-requirement-note">The current API returns requirement IDs, explanations, and evidence—not the original JD requirement descriptions.</p>
    </section>
  );
}
