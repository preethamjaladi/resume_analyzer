"""Stage 3B evaluator for Resume Analyzer (does not modify production modules).

Run from the parent of the resume_analyzer package:
  python -m resume_analyzer.tests.evaluate --dry-run
  python -m resume_analyzer.tests.evaluate --case TC01
  python -m resume_analyzer.tests.evaluate --all

Gold-to-predicted alignment is conservative. Ambiguous, split, or merged requirements
are explicitly sent to REVIEW and excluded from classification metrics.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from difflib import SequenceMatcher
import json
from pathlib import Path
import re
import sys

STATUSES = {"met", "partially_met", "not_met", "unknown"}
WORD_RE = re.compile(r"[a-z0-9]+")
STOP = {"a", "an", "and", "or", "in", "with", "to", "the", "of", "for", "on", "at", "from", "using", "experience", "required", "preferred", "have", "must", "be", "is", "as", "including", "work", "working", "ability", "knowledge", "familiarity", "proficiency", "professional", "development", "developing"}


def normalize(text: str | None) -> str:
    return " ".join((text or "").split()).casefold()


def tokens(text: str) -> set[str]:
    return set(WORD_RE.findall(text.casefold())) - STOP


def to_dict(obj):
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, dict):
        return obj
    raise TypeError(f"Expected dict or Pydantic model, got {type(obj).__name__}")


def weighted_score(requirements: list[dict], key: str) -> float:
    weights = {"required": 3, "preferred": 1}
    values = {"met": 1, "partially_met": 0.5, "not_met": 0, "unknown": 0}
    total = sum(weights[x["importance"]] for x in requirements)
    earned = sum(weights[x["importance"]] * values[x[key]] for x in requirements)
    return round(100 * earned / total, 2) if total else 0.0


def load_cases(path: Path) -> tuple[dict, list[dict]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    cases = data["cases"]
    ids = [c["case_id"] for c in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Repeated case IDs")
    for c in cases:
        seen = set()
        for g in c["expected_requirements"]:
            if g["label_id"] in seen:
                raise ValueError(f"Repeated gold ID in {c['case_id']}")
            seen.add(g["label_id"])
            if g["expected_status"] not in STATUSES:
                raise ValueError(f"Bad status: {g['expected_status']}")
            for span in g.get("acceptable_evidence", []) + g.get("disallowed_evidence", []):
                if normalize(span) not in normalize(c["resume"]):
                    raise ValueError(f"Evidence span absent in {c['case_id']}/{g['label_id']}: {span}")
        for variant in c.get("input_variants", []):
            if not set(variant.get("expected_status_overrides", {})) <= seen:
                raise ValueError(f"Unknown gold ID in variant {variant['variant_id']}")
            for gold_id, spans in variant.get("acceptable_evidence_overrides", {}).items():
                for span in spans:
                    if normalize(span) not in normalize(variant["resume"]):
                        raise ValueError(f"Bad variant evidence: {variant['variant_id']}/{gold_id}")
    return data, cases


def build_jobs(cases: list[dict], selected: set[str] | None, include_variants: bool) -> list[dict]:
    jobs = []
    for case in cases:
        if selected and case["case_id"] not in selected:
            continue
        jobs.append({"run_id": case["case_id"], "case": case, "resume": case["resume"], "gold": case["expected_requirements"]})
        if include_variants:
            for variant in case.get("input_variants", []):
                gold = []
                for original in case["expected_requirements"]:
                    g = dict(original)
                    g["expected_status"] = variant.get("expected_status_overrides", {}).get(g["label_id"], g["expected_status"])
                    g["acceptable_evidence"] = variant.get("acceptable_evidence_overrides", {}).get(g["label_id"], g.get("acceptable_evidence", []))
                    gold.append(g)
                jobs.append({"run_id": variant["variant_id"], "case": case, "resume": variant["resume"], "gold": gold})
    return jobs

def canonicalize_requirement(text: str) -> str:
    text = text.casefold()

    replacements = [
        (r"\brest(?:ful)?(?:[- ]style)?(?:[- ]http)?\b", "rest api"),
        (r"\bcrud operations?\b", "crud"),
        (r"\b(building|built)\b", "build"),
        (r"\b(troubleshoot|troubleshooting|diagnosing)\b", "diagnose"),
        (r"\bslow (?:database )?queries\b", "database performance"),
        (r"\bdatabase performance issues?\b", "database performance"),
    ]

    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)

    return text

def similarity(gold: dict, predicted: dict) -> float:
    desc = canonicalize_requirement(gold["description"])
    pdesc = canonicalize_requirement(predicted["description"])
    dt, pt = tokens(desc), tokens(pdesc)
    terms = tokens(" ".join(gold.get("alignment_terms", [])))
    # Category disagreement is a meaningful model error, but can also signal
    # an ambiguous mapping. Never silently align across categories.
    if tokens(desc) == tokens(pdesc) and tokens(desc):
        return 1.0
    if gold["category"] != predicted["category"]:
        return 0.0
    overlap = len(dt & pt) / len(dt) if dt else 0.0
    term_overlap = len(terms & pt) / len(terms) if terms else 0.0
    seq = SequenceMatcher(None, normalize(desc), normalize(pdesc)).ratio()
    return max(overlap, term_overlap, seq)


def align(gold: list[dict], predicted: list[dict]) -> tuple[dict[str, str], list[dict]]:
    """Only accept unambiguous one-to-one textual/category mappings."""
    candidate_scores = {
        g["label_id"]: sorted(
            [(similarity(g, p), p["requirement_id"]) for p in predicted], reverse=True
        ) for g in gold
    }
    best = {}
    reasons = []
    for g in gold:
        gid = g["label_id"]
        opts = candidate_scores[gid]
        if not opts or opts[0][0] < 0.72:
            reasons.append({"gold_id": gid, "issue": "No confident textual/category alignment", "candidates": opts[:2]})
            continue
        if len(opts) > 1 and opts[0][0] - opts[1][0] < 0.12:
            reasons.append({"gold_id": gid, "issue": "Ambiguous model requirement candidates", "candidates": opts[:2]})
            continue
        best[gid] = opts[0][1]
    counts = Counter(best.values())
    for gid, pid in list(best.items()):
        if counts[pid] > 1:
            reasons.append({"gold_id": gid, "issue": "Model merged multiple gold requirements", "model_id": pid})
            del best[gid]
    assigned = set(best.values())
    for p in predicted:
        if p["requirement_id"] not in assigned:
            reasons.append({"model_id": p["requirement_id"], "issue": "Unaligned model requirement; possible split, extra, or category mismatch"})
    return best, reasons


def assess_evidence(match: dict, g: dict, resume: str) -> tuple[str, str]:
    status = match["status"]
    quote = match.get("evidence")
    if status in {"not_met", "unknown"}:
        return ("PASS", "No quote needed") if not quote else ("REVIEW", "Quote present on missing/unknown judgment")
    if not quote:
        return "FAIL", "Positive judgment has no evidence"
    if normalize(quote) not in normalize(resume):
        return "FAIL", "Quote is absent from original resume"
    if any(normalize(bad) in normalize(quote) or normalize(quote) in normalize(bad) for bad in g.get("disallowed_evidence", []) if bad):
        return "FAIL", "Disallowed evidence used"
    allowed = g.get("acceptable_evidence", [])
    if not allowed:
        return "REVIEW", "Positive judgment without labeled acceptable evidence"
    if any(normalize(quote) in normalize(good) or normalize(good) in normalize(quote) for good in allowed):
        return "PASS", "Quote agrees with an acceptable span"
    return "REVIEW", "Resume quote is genuine but differs from labeled spans; human review needed"


def evaluate_state(job: dict, state: dict) -> dict:
    gold = job["gold"]
    predicted = [to_dict(x) for x in to_dict(state["jd_requirements"])["requirements"]]
    matches = [to_dict(x) for x in state["requirement_matches"]]
    verifications = [to_dict(x) for x in state.get("verification_results", [])]
    match_by_id = {x["requirement_id"]: x for x in matches}
    pred_ids = [p["requirement_id"] for p in predicted]
    match_ids = [m["requirement_id"] for m in matches]
    verify_ids = [v["requirement_id"] for v in verifications]
    integrity = {
        "unique_model_requirement_ids": len(set(pred_ids)) == len(pred_ids),
        "every_model_requirement_has_one_match": Counter(pred_ids) == Counter(match_ids),
        "every_model_requirement_has_one_verification": Counter(pred_ids) == Counter(verify_ids),
    }
    alignment, reviews = align(gold, predicted)
    comparisons = []
    for g in gold:
        pid = alignment.get(g["label_id"])
        if not pid or pid not in match_by_id:
            comparisons.append({"gold_id": g["label_id"], "gold_description": g["description"], "expected": g["expected_status"], "result": "REVIEW", "reason": "Not aligned to exactly one predicted requirement"})
            continue
        m = match_by_id[pid]
        evidence_result, evidence_note = assess_evidence(m, g, job["resume"])
        p = next(p for p in predicted if p["requirement_id"] == pid)
        comparisons.append({
            "gold_id": g["label_id"], "model_id": pid, "gold_description": g["description"],
            "expected": g["expected_status"], "actual": m["status"],
            "classification_correct": g["expected_status"] == m["status"],
            "evidence_check": evidence_result, "evidence_note": evidence_note,
            "importance_correct": g["importance"] == p["importance"],
            "hard_flag_correct": g["is_hard_requirement"] == p["is_hard_requirement"],
            "result": "COMPARED",
        })
    compared = [x for x in comparisons if x["result"] == "COMPARED"]
    total = len(compared)
    accuracy = sum(x["classification_correct"] for x in compared) / total if total else None
    # Class-wise precision/recall/F1 for 'met'. Other statuses appear in confusion matrix.
    tp = sum(x["expected"] == "met" and x["actual"] == "met" for x in compared)
    fp = sum(x["expected"] != "met" and x["actual"] == "met" for x in compared)
    fn = sum(x["expected"] == "met" and x["actual"] != "met" for x in compared)
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = 2 * precision * recall / (precision + recall) if precision is not None and recall is not None and precision + recall else None
    expected_gold = weighted_score(gold, "expected_status")
    actual_output = state.get("match_score")
    expected_internal = weighted_score([
        dict(importance=p["importance"], status=match_by_id[p["requirement_id"]]["status"])
        for p in predicted
    ], "status") if all(pid in match_by_id for pid in pred_ids) and integrity["unique_model_requirement_ids"] else None
    hard_gaps_expected = [p["description"] for p in predicted if p["is_hard_requirement"] and match_by_id.get(p["requirement_id"], {}).get("status") == "not_met"]
    return {
        "run_id": job["run_id"], "predicted_requirements": predicted, "result": "COMPLETE_WITH_REVIEWS" if reviews else "COMPLETE",
        "gold_count": len(gold), "model_count": len(predicted), "aligned_count": total,
        "integrity": integrity, "alignment_reviews": reviews, "comparisons": comparisons,
        "metrics_on_aligned_only": {"accuracy": accuracy, "met_precision": precision, "met_recall": recall, "met_f1": f1,
             "confusion_counts": dict(Counter(f"{x['expected']} -> {x['actual']}" for x in compared))},
        "scores": {"gold_reference_score": expected_gold, "model_reported_score": actual_output,
                   "independently_recomputed_model_score": expected_internal,
                   "internal_score_consistent": actual_output == expected_internal,
                   "gold_score_directly_comparable": len(alignment) == len(gold) == len(predicted) and not reviews and all(x["importance_correct"] for x in compared)},
        "hard_gaps": {"reported": state.get("hard_gaps", []), "expected_from_model_classifications": hard_gaps_expected,
                      "internally_consistent": state.get("hard_gaps", []) == hard_gaps_expected,
                      "gold_unmet_hard_thresholds": [g["description"] for g in gold if g.get("unmet_hard_threshold")]},
    }


def print_summary(reports: list[dict]) -> None:
    print("\n=== STAGE 3B EVALUATION ===")
    for r in reports:
        if "error" in r:
            print(f"{r['run_id']}: ERROR | {r['error']}")
            continue
        m = r["metrics_on_aligned_only"]
        accuracy = f"{m['accuracy']:.1%}" if m["accuracy"] is not None else "n/a"
        print(f"{r['run_id']}: {r['aligned_count']}/{r['gold_count']} aligned | "
              f"accuracy on aligned={accuracy} | reviews={len(r['alignment_reviews'])} | "
              f"internal score={'PASS' if r['scores']['internal_score_consistent'] else 'FAIL'} | "
              f"hard gaps={'PASS' if r['hard_gaps']['internally_consistent'] else 'FAIL'}")
    done = [r for r in reports if "error" not in r]
    aligned = sum(r["aligned_count"] for r in done)
    total = sum(r["gold_count"] for r in done)
    correct = sum(sum(c["classification_correct"] for c in r["comparisons"] if c["result"] == "COMPARED") for r in done)
    print(f"TOTAL: {len(done)}/{len(reports)} runs finished | gold coverage {aligned}/{total} | "
          f"classification accuracy on aligned {correct/aligned:.1%}" if aligned else "TOTAL: no comparable labels")
    print("CAUTION: Metrics exclude unaligned requirements. Label provenance is AI-assisted pending human review.")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Stage 3B Resume Analyzer evaluation")
    ap.add_argument("--dataset", type=Path, default=Path(__file__).with_name("evaluation_dataset.json"))
    ap.add_argument("--case", action="append", metavar="TC01", help="Run only specified case (repeatable)")
    ap.add_argument("--all", action="store_true", help="Run all 10 primary cases")
    ap.add_argument("--include-variants", action="store_true", help="Include dataset input variants")
    ap.add_argument("--dry-run", action="store_true", help="Validate dataset without Groq requests")
    ap.add_argument("--output", type=Path, default=Path(__file__).with_name("evaluation_report.json"))
    args = ap.parse_args(argv)
    dataset, cases = load_cases(args.dataset)
    selected = set(args.case) if args.case else None
    if selected and not selected <= {c["case_id"] for c in cases}:
        ap.error(f"Unknown case(s): {selected - {c['case_id'] for c in cases}}")
    if not args.dry_run and not args.all and not selected:
        ap.error("Choose --case TC01 or --all (or --dry-run); live execution is opt-in")
    jobs = build_jobs(cases, selected, args.include_variants)
    print(f"Dataset {dataset['dataset_version']}: {len(cases)} primary cases; {len(jobs)} selected runs")
    if args.dry_run:
        for job in jobs:
            print(f"{job['run_id']}: {len(job['gold'])} gold labels | gold score {weighted_score(job['gold'], 'expected_status')}%")
        print("PASS: Dataset structure and evidence spans verified. No API calls made.")
        return 0
    # Import only for live runs to avoid creating network clients in dry-run.
    from resume_analyzer.graph import workflow_graph
    reports = []
    for job in jobs:
        print(f"Running {job['run_id']}...", flush=True)
        try:
            state = workflow_graph.invoke({"resume": job["resume"], "job_description": job["case"]["job_description"]})
            reports.append(evaluate_state(job, state))
        except Exception as exc:
            reports.append({"run_id": job["run_id"], "error": f"{type(exc).__name__}: {exc}"})
        # Preserve completed results after each case so a later API failure can't erase earlier cases.
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "dataset_version": dataset["dataset_version"],
            "provenance": dataset.get("provenance"),
            "results": reports,
        }, indent=2, ensure_ascii=False), encoding="utf-8")
    print_summary(reports)
    print(f"Detailed report: {args.output}")
    return 1 if any("error" in r for r in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
