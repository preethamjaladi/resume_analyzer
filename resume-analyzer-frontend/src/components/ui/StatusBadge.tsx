import type { MatchStatus } from "../../types/analysis";
import { MATCH_LABELS } from "../../types/analysis";

export default function StatusBadge({ status }: { status: MatchStatus }) {
  return <span className={`ra-ws-status ra-ws-status--${status}`}><span className="ra-ws-status-dot" />{MATCH_LABELS[status]}</span>;
}
