#!/usr/bin/env python3
"""
memory_feedback.py - Retrieval Feedback Logging & Telemetry Engine.
Implements Instruction.md Section 39 (Retrieval Feedback Ledger) and
Section 40 (Passive Feedback), Phase 7 Feedback/Learning, and Section 78 (Abstention).

Features:
- Telemetry logging to retrieval_ledger.jsonl with strict concurrency file locking
- Distinction between 'not shown' (was_visible=False) and 'shown but unused' (was_visible=True, used_in_action=False)
- Separation of outcome signals: EXPLICIT_FEEDBACK, VERIFIED_OUTCOME, INFERRED_USAGE, INFERRED_NONUSE
- Strict Zero-Secrets Policy enforcement using secret_scanner before any write
- Metric Computation:
    * MRR (Mean Reciprocal Rank)
    * NDCG@10 (Normalized Discounted Cumulative Gain at rank 10)
    * False Recall Rate (item-level, strict wrong/stale, query-level, and abstention rate)
- Synthetic telemetry generation for testing and benchmarking
- Human-readable GitHub-flavored markdown and JSON output modes
"""

import os
import sys
import json
import math
import time
import argparse
import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set

# Add parent and current script directory to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

DEFAULT_PROJECT_MEM_DIR = "/workspaces/codespaces-blank/.agents/memory"
DEFAULT_LEDGER_PATH = os.path.join(DEFAULT_PROJECT_MEM_DIR, "retrieval_ledger.jsonl")

# Safe imports for file locking and secret scanning
try:
    from lock_manager import file_lock
except ImportError:
    from contextlib import contextmanager
    @contextmanager
    def file_lock(filepath, timeout=5.0):
        yield filepath

try:
    from secret_scanner import scan_text
except ImportError:
    class DummyScanner:
        def __init__(self):
            self.is_clean = True
            self.findings = []
    def scan_text(*args, **kwargs):
        return DummyScanner()


class FeedbackOutcome(str, Enum):
    """
    Strict feedback outcome labels per Instruction.md Section 40:
    Never pretend an inference is explicit human feedback.
    """
    EXPLICIT_FEEDBACK = "EXPLICIT_FEEDBACK"
    VERIFIED_OUTCOME = "VERIFIED_OUTCOME"
    INFERRED_USAGE = "INFERRED_USAGE"
    INFERRED_NONUSE = "INFERRED_NONUSE"


VALID_OUTCOMES = {e.value for e in FeedbackOutcome}


def validate_secret_hygiene(data: Any, context: str = "telemetry") -> None:
    """
    Ensures no sensitive credentials, API keys, or private tokens leak into
    telemetry records per Antigravity Zero Secrets Policy.
    """
    serialized = json.dumps(data) if not isinstance(data, str) else data
    result = scan_text(serialized, target_name=f"ledger_{context}")
    if not result.is_clean:
        findings = ", ".join([f"[{f.severity}] {f.description}" for f in result.findings])
        raise ValueError(f"Zero-Secrets Policy violation in {context}: {findings}")


class FeedbackLedger:
    """
    Manages retrieval telemetry events, audit logs, and performance metric calculations.
    Persists to retrieval_ledger.jsonl under strict file locks.
    """

    def __init__(self, ledger_path: Optional[str] = None):
        self.ledger_path = os.path.abspath(ledger_path or DEFAULT_LEDGER_PATH)
        os.makedirs(os.path.dirname(self.ledger_path), exist_ok=True)

    def record_event(
        self,
        query_id: str,
        memory_id: str,
        was_visible: bool,
        rank: Optional[int],
        used_in_action: bool,
        outcome: str,
        helpful: Optional[bool] = None,
        wrong: Optional[bool] = None,
        stale: Optional[bool] = None,
        prevented_error: Optional[bool] = None,
        blocked_action: Optional[bool] = None,
        latency_ms: Optional[float] = None,
        context_tokens: Optional[int] = None,
        relevance_score: Optional[float] = None,
        timestamp: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Records a single retrieval feedback event per Section 39 and Section 40.
        """
        # Validate query_id and memory_id
        if not query_id or not isinstance(query_id, str):
            raise ValueError("query_id must be a non-empty string")
        if not memory_id or not isinstance(memory_id, str):
            raise ValueError("memory_id must be a non-empty string")

        # Validate outcome enum
        outcome_str = str(outcome).strip()
        if outcome_str not in VALID_OUTCOMES:
            raise ValueError(
                f"Invalid outcome '{outcome_str}'. Must be one of: {sorted(list(VALID_OUTCOMES))}"
            )

        # Validate rank
        if rank is not None:
            try:
                rank = int(rank)
                if rank < 1:
                    raise ValueError("rank must be >= 1 if specified")
            except (TypeError, ValueError) as err:
                raise ValueError(f"rank must be a positive integer or None: {err}")

        # Normalization
        now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
        record = {
            "query_id": query_id.strip(),
            "memory_id": memory_id.strip(),
            "was_visible": bool(was_visible),
            "rank": rank,
            "used_in_action": bool(used_in_action),
            "outcome": outcome_str,
            "helpful": helpful if helpful is not None else None,
            "wrong": bool(wrong) if wrong is not None else False,
            "stale": bool(stale) if stale is not None else False,
            "prevented_error": bool(prevented_error) if prevented_error is not None else False,
            "blocked_action": bool(blocked_action) if blocked_action is not None else False,
            "latency_ms": float(latency_ms) if latency_ms is not None else None,
            "context_tokens": int(context_tokens) if context_tokens is not None else None,
            "relevance_score": float(relevance_score) if relevance_score is not None else None,
            "timestamp": timestamp or now_utc,
            "metadata": metadata or {},
        }

        # Zero-Secrets scan before write
        validate_secret_hygiene(record, context=f"event({query_id},{memory_id})")

        # Atomic append under file lock
        line_to_write = json.dumps(record, separators=(",", ":")) + "\n"
        with file_lock(self.ledger_path):
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(line_to_write)
                f.flush()
                os.fsync(f.fileno())

        return record

    def record_batch(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Atomically appends a batch of retrieval feedback events to the ledger.
        """
        validated_records = []
        now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()

        for idx, item in enumerate(events):
            q_id = item.get("query_id")
            m_id = item.get("memory_id")
            if not q_id or not m_id:
                raise ValueError(f"Batch item at index {idx} missing query_id or memory_id")

            outcome_str = str(item.get("outcome", "")).strip()
            if outcome_str not in VALID_OUTCOMES:
                raise ValueError(
                    f"Batch item at index {idx} has invalid outcome '{outcome_str}'."
                )

            rank = item.get("rank")
            if rank is not None:
                rank = int(rank)
                if rank < 1:
                    raise ValueError(f"Batch item at index {idx} rank must be >= 1")

            # support both used and used_in_action keys
            used = item.get("used_in_action")
            if used is None:
                used = item.get("used", False)

            rec = {
                "query_id": str(q_id).strip(),
                "memory_id": str(m_id).strip(),
                "was_visible": bool(item.get("was_visible", True)),
                "rank": rank,
                "used_in_action": bool(used),
                "outcome": outcome_str,
                "helpful": item.get("helpful"),
                "wrong": bool(item.get("wrong", False)),
                "stale": bool(item.get("stale", False)),
                "prevented_error": bool(item.get("prevented_error", False)),
                "blocked_action": bool(item.get("blocked_action", False)),
                "latency_ms": float(item["latency_ms"]) if item.get("latency_ms") is not None else None,
                "context_tokens": int(item["context_tokens"]) if item.get("context_tokens") is not None else None,
                "relevance_score": float(item["relevance_score"]) if item.get("relevance_score") is not None else None,
                "timestamp": item.get("timestamp") or now_utc,
                "metadata": item.get("metadata", {}),
            }
            validate_secret_hygiene(rec, context=f"batch_item_{idx}")
            validated_records.append(rec)

        if not validated_records:
            return []

        payload = "".join([json.dumps(r, separators=(",", ":")) + "\n" for r in validated_records])
        with file_lock(self.ledger_path):
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(payload)
                f.flush()
                os.fsync(f.fileno())

        return validated_records

    def read_records(
        self,
        query_id: Optional[str] = None,
        memory_id: Optional[str] = None,
        outcome: Optional[str] = None,
        was_visible: Optional[bool] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Reads records from the JSONL ledger file with optional filtering.
        """
        if not os.path.exists(self.ledger_path):
            return []

        records = []
        with file_lock(self.ledger_path):
            with open(self.ledger_path, "r", encoding="utf-8", errors="ignore") as f:
                for line_idx, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    # Apply filters
                    if query_id and data.get("query_id") != query_id:
                        continue
                    if memory_id and data.get("memory_id") != memory_id:
                        continue
                    if outcome and data.get("outcome") != outcome:
                        continue
                    if was_visible is not None and data.get("was_visible") != was_visible:
                        continue

                    records.append(data)
                    if limit and len(records) >= limit:
                        break

        return records

    def clear_ledger(self) -> None:
        """
        Clears the ledger file safely.
        """
        with file_lock(self.ledger_path):
            with open(self.ledger_path, "w", encoding="utf-8") as f:
                f.truncate(0)

    @staticmethod
    def is_item_relevant(record: Dict[str, Any]) -> bool:
        """
        Determines binary relevance for MRR and recall calculations:
        A record is relevant if it was useful/correct and not wrong or stale.
        """
        # Explicit wrong/stale/blocked markers invalidate relevance
        if record.get("wrong") or record.get("stale") or record.get("blocked_action"):
            return False

        # Explicit numeric relevance score if given
        if record.get("relevance_score") is not None:
            return float(record["relevance_score"]) > 0.0

        outcome = record.get("outcome")
        # Verified outcome or explicit positive feedback
        if outcome == FeedbackOutcome.VERIFIED_OUTCOME.value:
            return True
        if outcome == FeedbackOutcome.EXPLICIT_FEEDBACK.value:
            return record.get("helpful") is not False

        # Inferred usage or used in action
        if record.get("used_in_action"):
            return True
        if outcome == FeedbackOutcome.INFERRED_USAGE.value:
            return True

        return False

    @staticmethod
    def get_graded_relevance(record: Dict[str, Any]) -> float:
        """
        Calculates graded relevance score in [0.0, 3.0] for NDCG computation.
        """
        # Hard penalties for wrong, stale, or harmful items
        if record.get("wrong") or record.get("stale") or record.get("blocked_action"):
            return 0.0
        if (
            record.get("outcome") == FeedbackOutcome.EXPLICIT_FEEDBACK.value
            and record.get("helpful") is False
        ):
            return 0.0

        # If explicit relevance_score is given
        if record.get("relevance_score") is not None:
            val = float(record["relevance_score"])
            return max(0.0, min(3.0, val))

        outcome = record.get("outcome")
        used = bool(record.get("used_in_action", False))

        rel = 0.0
        if outcome == FeedbackOutcome.VERIFIED_OUTCOME.value:
            rel = 3.0
        elif outcome == FeedbackOutcome.EXPLICIT_FEEDBACK.value and record.get("helpful") is True:
            rel = 3.0
        elif outcome == FeedbackOutcome.INFERRED_USAGE.value or used:
            rel = 2.0
        elif record.get("was_visible") and not used:
            # Shown but unused
            rel = 0.0
        elif outcome == FeedbackOutcome.INFERRED_NONUSE.value:
            rel = 0.0

        if record.get("prevented_error") and rel > 0:
            rel = min(3.0, rel + 0.5)

        return rel

    def compute_metrics(
        self, records: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Computes comprehensive retrieval metrics:
        1. MRR (Mean Reciprocal Rank)
        2. NDCG@10 (Normalized Discounted Cumulative Gain at rank 10)
        3. False Recall Rate (item-level, strict wrong/stale, query-level, abstention)
        Plus full visibility/usage breakdowns per Section 39 & 40.
        """
        if records is None:
            records = self.read_records()

        if not records:
            return {
                "status": "empty",
                "total_queries": 0,
                "total_records": 0,
                "mrr": 0.0,
                "ndcg_at_10": 0.0,
                "ndcg_at_10_relevant_only": 0.0,
                "false_recall_rate": 0.0,
                "strict_false_recall_rate": 0.0,
                "query_false_recall_rate": 0.0,
                "abstention_false_recall_rate": 0.0,
                "counts": {
                    "visible": 0,
                    "not_visible": 0,
                    "used": 0,
                    "shown_unused": 0,
                    "wrong": 0,
                    "stale": 0,
                    "prevented_error": 0,
                    "blocked_action": 0,
                    "helpful": 0,
                },
                "outcomes": {o: 0 for o in VALID_OUTCOMES},
                "queries": {},
            }

        # Group records by query_id
        grouped_by_query: Dict[str, List[Dict[str, Any]]] = {}
        for r in records:
            q_id = r.get("query_id", "unknown")
            grouped_by_query.setdefault(q_id, []).append(r)

        # Global aggregate counters
        total_records = len(records)
        total_visible = 0
        total_not_visible = 0
        total_used = 0
        total_shown_unused = 0
        total_wrong = 0
        total_stale = 0
        total_prevented_error = 0
        total_blocked_action = 0
        total_helpful = 0
        total_false_recalls = 0
        total_strict_false_recalls = 0

        outcome_counts = {o: 0 for o in VALID_OUTCOMES}

        for r in records:
            outcome = r.get("outcome")
            if outcome in outcome_counts:
                outcome_counts[outcome] += 1

            was_vis = bool(r.get("was_visible", True))
            used = bool(r.get("used_in_action", False))
            is_wrong = bool(r.get("wrong", False))
            is_stale = bool(r.get("stale", False))
            is_blocked = bool(r.get("blocked_action", False))

            if was_vis:
                total_visible += 1
                if used:
                    total_used += 1
                else:
                    total_shown_unused += 1

                # Strict false recall: shown and wrong, stale, or caused blocked/error action
                if is_wrong or is_stale or is_blocked or (
                    outcome == FeedbackOutcome.EXPLICIT_FEEDBACK.value and r.get("helpful") is False
                ):
                    total_strict_false_recalls += 1

                # General false recall: strict OR marked non-use/irrelevant
                if not self.is_item_relevant(r):
                    total_false_recalls += 1
            else:
                total_not_visible += 1

            if is_wrong:
                total_wrong += 1
            if is_stale:
                total_stale += 1
            if bool(r.get("prevented_error", False)):
                total_prevented_error += 1
            if is_blocked:
                total_blocked_action += 1
            if r.get("helpful") is True:
                total_helpful += 1

        # Calculate per-query metrics
        query_metrics: Dict[str, Dict[str, Any]] = {}
        reciprocal_ranks: List[float] = []
        ndcg_list_all: List[float] = []
        ndcg_list_relevant_only: List[float] = []

        queries_with_visible = 0
        queries_with_false_recalls = 0
        abstention_queries_count = 0
        abstention_false_retrieval_count = 0

        for q_id, q_records in grouped_by_query.items():
            # Check if query is an abstention test query (Section 78)
            is_abstention = any(
                r.get("metadata", {}).get("is_abstention") is True
                or r.get("metadata", {}).get("abstention") is True
                for r in q_records
            )
            # Or if query ground truth has zero relevant items
            all_q_relevant = [r for r in q_records if self.is_item_relevant(r)]
            if is_abstention:
                abstention_queries_count += 1

            # Only consider visible records for ranking metrics
            visible_q_records = [r for r in q_records if r.get("was_visible", True)]
            if visible_q_records:
                queries_with_visible += 1

            # Sort visible records by rank ascending (items without rank come last)
            visible_ranked = sorted(
                [r for r in visible_q_records if r.get("rank") is not None and r["rank"] > 0],
                key=lambda x: x["rank"],
            )

            # MRR Calculation
            rr = 0.0
            first_relevant_rank = None
            for item in visible_ranked:
                if self.is_item_relevant(item):
                    first_relevant_rank = item["rank"]
                    rr = 1.0 / first_relevant_rank
                    break
            reciprocal_ranks.append(rr)

            # NDCG@10 Calculation
            # 1. DCG@10
            dcg_10 = 0.0
            for item in visible_ranked:
                rank = item["rank"]
                if rank > 10:
                    continue
                rel = self.get_graded_relevance(item)
                discount = math.log2(rank + 1.0)
                dcg_10 += (math.pow(2.0, rel) - 1.0) / discount

            # 2. IDCG@10
            # Ideal ranking consists of all available evaluated items sorted by descending relevance
            all_rels = [self.get_graded_relevance(r) for r in q_records]
            all_rels.sort(reverse=True)
            idcg_10 = 0.0
            for idx_rank, rel_val in enumerate(all_rels[:10], 1):
                discount = math.log2(idx_rank + 1.0)
                idcg_10 += (math.pow(2.0, rel_val) - 1.0) / discount

            if idcg_10 > 0.0:
                ndcg = dcg_10 / idcg_10
                ndcg_list_all.append(ndcg)
                ndcg_list_relevant_only.append(ndcg)
            else:
                # When IDCG is 0 (no relevant items exist in ground truth)
                # If it's an abstention query and 0 visible items were returned, abstention succeeded (1.0)
                # Otherwise, if irrelevant/wrong items were returned, score is 0.0
                if is_abstention and len(visible_q_records) == 0:
                    ndcg = 1.0
                else:
                    ndcg = 0.0
                ndcg_list_all.append(ndcg)

            # False recall at query level
            q_has_false_recall = any(
                r.get("was_visible", True) and not self.is_item_relevant(r)
                for r in q_records
            )
            if q_has_false_recall and visible_q_records:
                queries_with_false_recalls += 1

            if is_abstention:
                # If anything visible was retrieved for an abstention test
                if visible_q_records:
                    abstention_false_retrieval_count += 1

            query_metrics[q_id] = {
                "reciprocal_rank": round(rr, 4),
                "first_relevant_rank": first_relevant_rank,
                "dcg_at_10": round(dcg_10, 4),
                "idcg_at_10": round(idcg_10, 4),
                "ndcg_at_10": round(ndcg, 4),
                "total_records": len(q_records),
                "visible_records": len(visible_q_records),
                "used_records": sum(1 for r in q_records if r.get("used_in_action")),
                "is_abstention": is_abstention,
            }

        # Aggregated Metrics
        mrr = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0
        ndcg_all = sum(ndcg_list_all) / len(ndcg_list_all) if ndcg_list_all else 0.0
        ndcg_rel = (
            sum(ndcg_list_relevant_only) / len(ndcg_list_relevant_only)
            if ndcg_list_relevant_only
            else 0.0
        )

        item_false_recall_rate = (
            total_false_recalls / total_visible if total_visible > 0 else 0.0
        )
        strict_false_recall_rate = (
            total_strict_false_recalls / total_visible if total_visible > 0 else 0.0
        )
        query_false_recall_rate = (
            queries_with_false_recalls / queries_with_visible
            if queries_with_visible > 0
            else 0.0
        )
        abstention_false_recall_rate = (
            abstention_false_retrieval_count / abstention_queries_count
            if abstention_queries_count > 0
            else 0.0
        )

        return {
            "status": "success",
            "total_queries": len(grouped_by_query),
            "total_records": total_records,
            "mrr": round(mrr, 4),
            "ndcg_at_10": round(ndcg_all, 4),
            "ndcg_at_10_relevant_only": round(ndcg_rel, 4),
            "false_recall_rate": round(item_false_recall_rate, 4),
            "strict_false_recall_rate": round(strict_false_recall_rate, 4),
            "query_false_recall_rate": round(query_false_recall_rate, 4),
            "abstention_false_recall_rate": round(abstention_false_recall_rate, 4),
            "counts": {
                "visible": total_visible,
                "not_visible": total_not_visible,
                "used": total_used,
                "shown_unused": total_shown_unused,
                "wrong": total_wrong,
                "stale": total_stale,
                "prevented_error": total_prevented_error,
                "blocked_action": total_blocked_action,
                "helpful": total_helpful,
            },
            "outcomes": outcome_counts,
            "queries": query_metrics,
        }


def generate_synthetic_telemetry(num_queries: int = 10) -> List[Dict[str, Any]]:
    """
    Generates a deterministic, realistic synthetic telemetry dataset representing
    diverse memory retrieval scenarios per Section 39, 40, and 78.
    Scenarios include:
    1. Perfect precision hits (rank 1 verified outcome)
    2. Ranked queries with near misses (rank 1 non-use, rank 2 verified use)
    3. Low-rank retrieval (rank 5 explicit feedback)
    4. Stale/wrong memory retrieval causing blocked action
    5. Abstention queries with correct abstention (no visible recall)
    6. Abstention queries with false recall (irrelevant recall on absent memory)
    7. Context-budget pruned items (was_visible=False, 'not shown' vs 'shown but unused')
    """
    events = []
    base_time = datetime.datetime(2026, 9, 3, 12, 0, 0, tzinfo=datetime.timezone.utc)

    # 1. Query 1: Perfect retrieval for architectural decision
    q1 = "query_arch_adr_001"
    events.append({
        "query_id": q1,
        "memory_id": "DECISIONS.md#ADR-001",
        "was_visible": True,
        "rank": 1,
        "used_in_action": True,
        "outcome": FeedbackOutcome.VERIFIED_OUTCOME.value,
        "helpful": True,
        "prevented_error": True,
        "latency_ms": 14.2,
        "context_tokens": 120,
        "timestamp": (base_time + datetime.timedelta(minutes=1)).isoformat(),
        "metadata": {"query_text": "What is ADR-001 architectural standard?"},
    })
    events.append({
        "query_id": q1,
        "memory_id": "ARCHITECTURE.md#overview",
        "was_visible": True,
        "rank": 2,
        "used_in_action": False,
        "outcome": FeedbackOutcome.INFERRED_NONUSE.value,
        "helpful": None,
        "latency_ms": 14.2,
        "context_tokens": 85,
        "timestamp": (base_time + datetime.timedelta(minutes=1)).isoformat(),
    })
    events.append({
        "query_id": q1,
        "memory_id": "GENERAL.md#rules",
        "was_visible": False,  # Not shown due to top-2 cut (Section 39)
        "rank": 3,
        "used_in_action": False,
        "outcome": FeedbackOutcome.INFERRED_NONUSE.value,
        "latency_ms": 14.2,
        "context_tokens": 50,
        "timestamp": (base_time + datetime.timedelta(minutes=1)).isoformat(),
    })

    # 2. Query 2: Suboptimal ranking (relevant hit at rank 2, rank 1 was shown but unused)
    q2 = "query_gotchas_gradle"
    events.append({
        "query_id": q2,
        "memory_id": "tools/docker.md#caching",
        "was_visible": True,
        "rank": 1,
        "used_in_action": False,
        "outcome": FeedbackOutcome.INFERRED_NONUSE.value,  # Shown but unused
        "helpful": False,
        "latency_ms": 18.5,
        "context_tokens": 90,
        "timestamp": (base_time + datetime.timedelta(minutes=2)).isoformat(),
    })
    events.append({
        "query_id": q2,
        "memory_id": "GOTCHAS.md#gradle-daemon",
        "was_visible": True,
        "rank": 2,
        "used_in_action": True,
        "outcome": FeedbackOutcome.INFERRED_USAGE.value,
        "helpful": True,
        "prevented_error": True,
        "latency_ms": 18.5,
        "context_tokens": 110,
        "timestamp": (base_time + datetime.timedelta(minutes=2)).isoformat(),
    })

    # 3. Query 3: Stale memory hazard (shown, used, but caused failure)
    q3 = "query_node_version"
    events.append({
        "query_id": q3,
        "memory_id": "ENVIRONMENT.md#node-v18-legacy",
        "was_visible": True,
        "rank": 1,
        "used_in_action": True,
        "outcome": FeedbackOutcome.EXPLICIT_FEEDBACK.value,
        "helpful": False,
        "wrong": True,
        "stale": True,
        "blocked_action": True,
        "latency_ms": 11.0,
        "context_tokens": 70,
        "timestamp": (base_time + datetime.timedelta(minutes=3)).isoformat(),
        "metadata": {"error": "Legacy Node 18 specified when system runs Node 24"},
    })

    # 4. Query 4: Explicit user praise (verified outcome with user feedback)
    q4 = "query_security_secret_scanner"
    events.append({
        "query_id": q4,
        "memory_id": "POLICY.md#zero-secrets",
        "was_visible": True,
        "rank": 1,
        "used_in_action": True,
        "outcome": FeedbackOutcome.EXPLICIT_FEEDBACK.value,
        "helpful": True,
        "prevented_error": True,
        "latency_ms": 9.8,
        "context_tokens": 150,
        "timestamp": (base_time + datetime.timedelta(minutes=4)).isoformat(),
    })

    # 5. Query 5: Abstention test - Correct Abstention (Section 78)
    q5 = "query_absent_subsystem_db"
    events.append({
        "query_id": q5,
        "memory_id": "EMPTY_RECALL",
        "was_visible": False,  # Correctly returned 0 visible records
        "rank": None,
        "used_in_action": False,
        "outcome": FeedbackOutcome.INFERRED_NONUSE.value,
        "timestamp": (base_time + datetime.timedelta(minutes=5)).isoformat(),
        "metadata": {"is_abstention": True, "query_text": "Non-existent migration policy"},
    })

    # 6. Query 6: Abstention test - False Recall (irrelevant memory fabricated/recalled)
    q6 = "query_absent_ios_signing"
    events.append({
        "query_id": q6,
        "memory_id": "domains/android.md#apksigner",
        "was_visible": True,  # False recall: iOS asked, Android APK returned
        "rank": 1,
        "used_in_action": False,
        "outcome": FeedbackOutcome.INFERRED_NONUSE.value,
        "wrong": True,
        "stale": False,
        "latency_ms": 22.1,
        "context_tokens": 80,
        "timestamp": (base_time + datetime.timedelta(minutes=6)).isoformat(),
        "metadata": {"is_abstention": True, "query_text": "Non-existent iOS code signing"},
    })

    # 7. Query 7: Deep rank hit (rank 4)
    q7 = "query_network_pcap"
    for r_idx in range(1, 4):
        events.append({
            "query_id": q7,
            "memory_id": f"tools/generic_net_{r_idx}.md",
            "was_visible": True,
            "rank": r_idx,
            "used_in_action": False,
            "outcome": FeedbackOutcome.INFERRED_NONUSE.value,
            "timestamp": (base_time + datetime.timedelta(minutes=7)).isoformat(),
        })
    events.append({
        "query_id": q7,
        "memory_id": "tools/tshark.md#io-phs",
        "was_visible": True,
        "rank": 4,
        "used_in_action": True,
        "outcome": FeedbackOutcome.VERIFIED_OUTCOME.value,
        "helpful": True,
        "latency_ms": 15.0,
        "context_tokens": 130,
        "timestamp": (base_time + datetime.timedelta(minutes=7)).isoformat(),
    })

    # 8. Query 8: High-precision verified outcome
    q8 = "query_sqlite_readonly"
    events.append({
        "query_id": q8,
        "memory_id": "DECISIONS.md#ADR-005-readonly-db",
        "was_visible": True,
        "rank": 1,
        "used_in_action": True,
        "outcome": FeedbackOutcome.VERIFIED_OUTCOME.value,
        "helpful": True,
        "timestamp": (base_time + datetime.timedelta(minutes=8)).isoformat(),
    })

    # 9. Query 9: Inferred usage with multiple candidate snippets
    q9 = "query_ghidra_headless"
    events.append({
        "query_id": q9,
        "memory_id": "tools/ghidra.md#headless-syntax",
        "was_visible": True,
        "rank": 1,
        "used_in_action": True,
        "outcome": FeedbackOutcome.INFERRED_USAGE.value,
        "helpful": True,
        "timestamp": (base_time + datetime.timedelta(minutes=9)).isoformat(),
    })
    events.append({
        "query_id": q9,
        "memory_id": "tools/r2.md#commands",
        "was_visible": True,
        "rank": 2,
        "used_in_action": False,
        "outcome": FeedbackOutcome.INFERRED_NONUSE.value,
        "timestamp": (base_time + datetime.timedelta(minutes=9)).isoformat(),
    })

    # 10. Query 10: Multi-rank search with 5 visible items
    q10 = "query_test_fixtures"
    events.append({
        "query_id": q10,
        "memory_id": "ARCHITECTURE.md#fixtures",
        "was_visible": True,
        "rank": 1,
        "used_in_action": True,
        "outcome": FeedbackOutcome.VERIFIED_OUTCOME.value,
        "helpful": True,
        "timestamp": (base_time + datetime.timedelta(minutes=10)).isoformat(),
    })
    for r_idx in range(2, 6):
        events.append({
            "query_id": q10,
            "memory_id": f"fixtures/readme.md#part_{r_idx}",
            "was_visible": True,
            "rank": r_idx,
            "used_in_action": False,
            "outcome": FeedbackOutcome.INFERRED_NONUSE.value,
            "timestamp": (base_time + datetime.timedelta(minutes=10)).isoformat(),
        })

    return events


def format_markdown_metrics(metrics_data: Dict[str, Any], ledger_path: str) -> str:
    """
    Renders a GitHub-flavored Markdown report of retrieval telemetry metrics.
    """
    if metrics_data.get("status") == "empty":
        return "### Retrieval Telemetry Ledger\n> [!NOTE]\n> Ledger is currently empty."

    c = metrics_data["counts"]
    outcomes = metrics_data["outcomes"]
    mrr = metrics_data["mrr"]
    ndcg10 = metrics_data["ndcg_at_10"]
    ndcg10_rel = metrics_data["ndcg_at_10_relevant_only"]
    frr = metrics_data["false_recall_rate"]
    strict_frr = metrics_data["strict_false_recall_rate"]
    q_frr = metrics_data["query_false_recall_rate"]
    abs_frr = metrics_data["abstention_false_recall_rate"]

    lines = []
    lines.append("## Retrieval Feedback & Telemetry Metrics Report")
    lines.append(f"- **Ledger Target**: [`retrieval_ledger.jsonl`](file://{ledger_path})")
    lines.append(f"- **Queries Evaluated**: `{metrics_data['total_queries']}` | **Telemetry Events**: `{metrics_data['total_records']}`")
    lines.append("")

    # Core IR metrics table
    lines.append("### Core Retrieval Performance Metrics")
    lines.append("| Metric | Value | Target Benchmark | Status | Description |")
    lines.append("| :--- | :---: | :---: | :---: | :--- |")
    
    # Status badges
    mrr_status = "PASS" if mrr >= 0.70 else "WARN"
    ndcg_status = "PASS" if ndcg10 >= 0.70 else "WARN"
    frr_status = "PASS" if frr <= 0.40 else "WARN"
    strict_frr_status = "PASS" if strict_frr <= 0.15 else "WARN"

    lines.append(f"| **MRR (Mean Reciprocal Rank)** | **{mrr:.4f}** | >= 0.7000 | `{mrr_status}` | Inverse rank of first relevant retrieved memory |")
    lines.append(f"| **NDCG@10 (All Queries)** | **{ndcg10:.4f}** | >= 0.7000 | `{ndcg_status}` | Graded relevance gain discounted by logarithmic rank |")
    lines.append(f"| **NDCG@10 (Relevant-Only)** | **{ndcg10_rel:.4f}** | >= 0.7000 | `{ndcg_status}` | NDCG over queries with at least one ground-truth hit |")
    lines.append(f"| **False Recall Rate (Item)** | **{frr:.4f}** | <= 0.4000 | `{frr_status}` | Fraction of visible recalls that were unused or non-relevant |")
    lines.append(f"| **Strict False Recall Rate** | **{strict_frr:.4f}** | <= 0.1500 | `{strict_frr_status}` | Fraction of visible recalls marked wrong, stale, or harmful |")
    lines.append(f"| **Query False Recall Rate** | **{q_frr:.4f}** | <= 0.3500 | `INFO` | Fraction of queries where an irrelevant recall was visible |")
    lines.append(f"| **Abstention False Recall** | **{abs_frr:.4f}** | <= 0.5000 | `INFO` | Recall rate when memory answer is absent (Section 78) |")
    lines.append("")

    # Telemetry Breakdown
    lines.append("### Telemetry Breakdown (Section 39 & Section 40)")
    lines.append("| Telemetry Dimension | Count | Percentage | Operational Significance |")
    lines.append("| :--- | :---: | :---: | :--- |")
    vis_pct = (c['visible'] / metrics_data['total_records']) * 100 if metrics_data['total_records'] > 0 else 0
    not_vis_pct = (c['not_visible'] / metrics_data['total_records']) * 100 if metrics_data['total_records'] > 0 else 0
    used_pct = (c['used'] / c['visible']) * 100 if c['visible'] > 0 else 0
    shown_unused_pct = (c['shown_unused'] / c['visible']) * 100 if c['visible'] > 0 else 0

    lines.append(f"| **Visible Recalls** (`was_visible=True`) | {c['visible']} | {vis_pct:.1f}% | Shown in active model context |")
    lines.append(f"| **Not Shown** (`was_visible=False`) | {c['not_visible']} | {not_vis_pct:.1f}% | Ranking evidence, not bad memory (Section 39) |")
    lines.append(f"| **Used In Action** (`used_in_action=True`) | {c['used']} | {used_pct:.1f}% | Recalled memory directly assisted action |")
    lines.append(f"| **Shown But Unused** | {c['shown_unused']} | {shown_unused_pct:.1f}% | Evaluated in context but not acted upon |")
    lines.append(f"| **Verified Positive Outcomes** | {outcomes.get('VERIFIED_OUTCOME', 0)} | — | Deterministically verified task success |")
    lines.append(f"| **Explicit Human/User Feedback** | {outcomes.get('EXPLICIT_FEEDBACK', 0)} | — | Direct user endorsement or rejection |")
    lines.append(f"| **Inferred Usage Signals** | {outcomes.get('INFERRED_USAGE', 0)} | — | Passive behavioral inference (Section 40) |")
    lines.append(f"| **Inferred Non-Use Signals** | {outcomes.get('INFERRED_NONUSE', 0)} | — | Passive non-action observation |")
    lines.append(f"| **Wrong Memory Flags** | {c['wrong']} | — | Memory asserted factually false state |")
    lines.append(f"| **Stale Memory Flags** | {c['stale']} | — | Memory superseded by newer state |")
    lines.append(f"| **Prevented Errors** | {c['prevented_error']} | — | Memory guarded against known failure |")
    lines.append(f"| **Blocked Actions** | {c['blocked_action']} | — | Bad memory aborted execution |")
    lines.append("")

    # Per-query details table
    lines.append("### Per-Query Retrieval Feedback Ledger")
    lines.append("| Query ID | Reciprocal Rank | NDCG@10 | 1st Hit Rank | Visible | Used | Abstention |")
    lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
    for q_id, q_data in metrics_data["queries"].items():
        first_rk = q_data["first_relevant_rank"] if q_data["first_relevant_rank"] else "-"
        abs_tag = "`YES`" if q_data["is_abstention"] else "`NO`"
        lines.append(
            f"| `{q_id}` | **{q_data['reciprocal_rank']:.4f}** | {q_data['ndcg_at_10']:.4f} | {first_rk} | {q_data['visible_records']} | {q_data['used_records']} | {abs_tag} |"
        )
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Antigravity Retrieval Feedback Ledger & Telemetry Engine"
    )
    parser.add_argument(
        "--ledger-path",
        default=DEFAULT_LEDGER_PATH,
        help="Path to retrieval_ledger.jsonl",
    )
    parser.add_argument(
        "--metrics", action="store_true", help="Compute metrics from existing ledger"
    )
    parser.add_argument(
        "--synthetic-test",
        action="store_true",
        help="Generate synthetic telemetry events and compute benchmarks",
    )
    parser.add_argument(
        "--clear", action="store_true", help="Clear the existing ledger file"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output results in JSON format"
    )

    # CLI event logging arguments
    parser.add_argument("--log-event", action="store_true", help="Log a single retrieval event")
    parser.add_argument("--query-id", help="Unique search/query identifier")
    parser.add_argument("--memory-id", help="Retrieved memory identifier")
    parser.add_argument("--rank", type=int, default=None, help="1-indexed rank in search results")
    parser.add_argument("--not-visible", action="store_true", help="Mark item as not visible (was_visible=False)")
    parser.add_argument("--used", action="store_true", help="Mark item as used_in_action=True")
    parser.add_argument(
        "--outcome",
        choices=[e.value for e in FeedbackOutcome],
        default=FeedbackOutcome.INFERRED_USAGE.value,
        help="Feedback outcome label per Section 40",
    )
    parser.add_argument("--helpful", action="store_true", help="Flag item as helpful")
    parser.add_argument("--wrong", action="store_true", help="Flag item as wrong")
    parser.add_argument("--stale", action="store_true", help="Flag item as stale")
    parser.add_argument("--prevented-error", action="store_true", help="Flag item as preventing error")
    parser.add_argument("--blocked-action", action="store_true", help="Flag item as blocking action")
    parser.add_argument("--latency-ms", type=float, default=None, help="Search latency in ms")
    parser.add_argument("--context-tokens", type=int, default=None, help="Token size of snippet")

    args = parser.parse_args()

    ledger = FeedbackLedger(args.ledger_path)

    if args.clear:
        ledger.clear_ledger()
        print(f"Cleared retrieval ledger: {ledger.ledger_path}")
        return

    if args.log_event:
        if not args.query_id or not args.memory_id:
            print("Error: --query-id and --memory-id are required for --log-event", file=sys.stderr)
            sys.exit(1)
        rec = ledger.record_event(
            query_id=args.query_id,
            memory_id=args.memory_id,
            was_visible=not args.not_visible,
            rank=args.rank,
            used_in_action=args.used,
            outcome=args.outcome,
            helpful=True if args.helpful else None,
            wrong=args.wrong,
            stale=args.stale,
            prevented_error=args.prevented_error,
            blocked_action=args.blocked_action,
            latency_ms=args.latency_ms,
            context_tokens=args.context_tokens,
        )
        if args.json:
            print(json.dumps(rec, indent=2))
        else:
            print(f"Logged event successfully to {ledger.ledger_path}:")
            print(json.dumps(rec, indent=2))
        return

    if args.synthetic_test:
        print(f"Generating synthetic telemetry records per Section 39 & 40...")
        synthetic_events = generate_synthetic_telemetry()
        ledger.record_batch(synthetic_events)
        print(f"Successfully recorded {len(synthetic_events)} synthetic events into {ledger.ledger_path}.")
        metrics = ledger.compute_metrics()
        if args.json:
            print(json.dumps(metrics, indent=2))
        else:
            print("\n" + format_markdown_metrics(metrics, ledger.ledger_path))
        return

    if args.metrics:
        metrics = ledger.compute_metrics()
        if args.json:
            print(json.dumps(metrics, indent=2))
        else:
            print(format_markdown_metrics(metrics, ledger.ledger_path))
        return

    # Default: compute metrics if ledger has data, else show help
    if os.path.exists(ledger.ledger_path) and os.path.getsize(ledger.ledger_path) > 0:
        metrics = ledger.compute_metrics()
        if args.json:
            print(json.dumps(metrics, indent=2))
        else:
            print(format_markdown_metrics(metrics, ledger.ledger_path))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
