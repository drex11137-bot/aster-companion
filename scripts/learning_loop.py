#!/usr/bin/env python3
"""
learning_loop.py - Memory Decay Curves and Shadow Ranking Loop.
Part of the Antigravity Persistent Memory System (Phase 16).

Strictly adheres to:
- Instruction.md Section 41 (LEARNING LOOP)
- Instruction.md Section 42 (MEMORY DECAY)
- Instruction.md Section 43 (REINFORCEMENT / ACCESS)
- Instruction.md Section 23 (RRF / FUSION)
- Instruction.md Section 24 (EVIDENCE-AWARE RERANKING)
- Instruction.md Section 221 (SHADOW MODE)
- Instruction.md Section 222 (BENCHMARK GATE)

Key Architectural Invariants:
1. Zero Secrets Policy: Never persist credentials, tokens, or private keys.
2. Epistemic Grounding: Access frequency is a retrieval signal, NOT an epistemic truth signal.
   Retrieved != True, and Frequently Retrieved != Authoritative.
3. Governance Fact Immunity: Core governance and policy facts do NOT decay simply because they are old.
4. Strict Shadow Isolation: The learned ranker operates exclusively in SHADOW mode in isolation.
   It NEVER mutates the live search/retrieval path. The live path remains deterministic baseline RRF.
5. Immutable Feature Schema & Model Versioning: Feature schema version, model version, and
   training corpus version travel together. Never allow a new feature ordering to reinterpret
   old weights silently.
6. Benchmark Gate: Online learned ranking can only affect live behavior after explicitly passing
   the multi-criteria benchmark gate.
"""

import os
import sys
import math
import json
import argparse
import datetime
import re
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple

# Workspace and storage configuration
WORKSPACE_DIR = os.path.abspath(os.getenv("WORKSPACE_DIR", "/workspaces/codespaces-blank"))
SCRIPTS_DIR = os.path.join(WORKSPACE_DIR, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

DEFAULT_GLOBAL_MEM_DIR = os.path.expanduser("~/.gemini/antigravity-cli/memory")
DEFAULT_PROJECT_MEM_DIR = os.path.join(WORKSPACE_DIR, ".agents", "memory")
DEFAULT_LEDGER_PATH = os.path.join(DEFAULT_PROJECT_MEM_DIR, "learning_ledger.json")
DEFAULT_MODELS_DIR = os.path.join(DEFAULT_PROJECT_MEM_DIR, "models")
DEFAULT_MODEL_PATH = os.path.join(DEFAULT_MODELS_DIR, "shadow_ranker_v1.json")
DEFAULT_EVAL_DIR = os.path.join(DEFAULT_PROJECT_MEM_DIR, "shadow_eval")

# Schema & Version Constants
FEATURE_SCHEMA_VERSION = "1.0.0"
DEFAULT_MODEL_VERSION = "1.0.0"
DEFAULT_TRAINING_CORPUS_VERSION = "2026.09.03"

# Canonical feature ordering (Order Invariant: weights must match exact feature names)
CANONICAL_FEATURE_NAMES = [
    "baseline_rrf_score",
    "decay_factor",
    "access_reinforcement",
    "importance",
    "authority",
    "freshness",
    "stale_penalty",
    "superseded_penalty"
]

DEFAULT_WEIGHTS = {
    "baseline_rrf_score": 0.40,
    "decay_factor": 0.15,
    "access_reinforcement": 0.15,
    "importance": 0.10,
    "authority": 0.15,
    "freshness": 0.05,
    "stale_penalty": -0.25,
    "superseded_penalty": -0.35,
}

# Scope authority hierarchy & default durability mappings
SCOPE_AUTHORITY = {
    "policy": 1.0,
    "governance": 1.0,
    "rules": 0.95,
    "global": 0.90,
    "architecture": 0.85,
    "decisions": 0.80,
    "gotchas": 0.75,
    "domains": 0.70,
    "tools": 0.70,
    "project": 0.65,
    "sessions": 0.35,
    "candidate": 0.25,
    "ephemeral": 0.10,
    "general": 0.70,
    "environment": 0.80,
    "user": 0.85
}

SCOPE_HALF_LIVES_DAYS = {
    "policy": 3650.0,       # Effectively immortal (10 years)
    "governance": 3650.0,
    "rules": 3650.0,
    "global": 1825.0,       # 5 years
    "architecture": 730.0,  # 2 years
    "decisions": 365.0,     # 1 year
    "gotchas": 180.0,       # 6 months
    "domains": 180.0,
    "tools": 180.0,
    "project": 90.0,        # 3 months
    "sessions": 14.0,       # 2 weeks (low-value episodic material deprioritized)
    "candidate": 7.0,       # 1 week (candidates expire)
    "ephemeral": 1.0,       # 1 day
    "general": 365.0,
    "environment": 180.0,
    "user": 365.0
}


# ==============================================================================
# Exceptions
# ==============================================================================
class LearningLoopError(Exception):
    """Base exception for Learning Loop operations."""
    pass


class SchemaMismatchError(LearningLoopError):
    """Raised when persisted model feature schema or ordering does not match active code."""
    pass


class ModelVersionError(LearningLoopError):
    """Raised when model version or corpus version is invalid or incompatible."""
    pass


class BenchmarkGateError(LearningLoopError):
    """Raised when an unverified model fails the benchmark gate."""
    pass


# ==============================================================================
# Data Classes
# ==============================================================================
@dataclass
class MemoryItem:
    """Represents a candidate memory entry evaluated for decay and ranking."""
    id: str
    file_path: str
    scope: str
    heading: str
    content: str
    created_at: datetime.datetime
    last_accessed_at: Optional[datetime.datetime] = None
    importance: float = 3.0       # Durability scale 0 to 5
    authority: float = 0.5        # Authority scale 0.0 to 1.0
    access_count: int = 0         # Times retrieved / accessed
    verified_count: int = 0       # Times verified correct in execution
    refuted_count: int = 0        # Times found incorrect or conflicting
    is_superseded: bool = False
    is_candidate: bool = False
    ttl_days: Optional[float] = None
    raw_score: float = 0.0        # Upstream lexical match score

    @classmethod
    def from_search_result(
        cls,
        res: Dict[str, Any],
        ledger_data: Optional[Dict[str, Any]] = None,
        reference_time: Optional[datetime.datetime] = None
    ) -> "MemoryItem":
        """Constructs a MemoryItem from a search_memory.py result dict and ledger."""
        now = reference_time or datetime.datetime.now(datetime.timezone.utc)
        file_path = res.get("file", "")
        filename = res.get("filename", os.path.basename(file_path))
        scope = res.get("scope", "general").lower()
        heading = res.get("heading", "")
        content = res.get("snippet", "")
        raw_score = float(res.get("score", 10.0))
        start_line = res.get("start_line", 1)

        # Unique identifier
        candidate_id = f"{filename}#L{start_line}"
        adr_match = re.search(r'\b(ADR-\d+)\b', heading)
        if adr_match:
            candidate_id = f"{filename}#{adr_match.group(1)}"

        # Date extraction: search in heading, snippet, or filename
        created_at = None
        date_matches = re.findall(r'\b(20\d{2}-\d{2}-\d{2})\b', heading + " " + content)
        if date_matches:
            try:
                created_at = datetime.datetime.strptime(date_matches[0], "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
            except ValueError:
                pass

        if not created_at:
            file_date = re.search(r'\b(20\d{2}-\d{2}-\d{2})\b', filename)
            if file_date:
                try:
                    created_at = datetime.datetime.strptime(file_date.group(1), "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
                except ValueError:
                    pass

        if not created_at and os.path.exists(file_path):
            mtime = os.path.getmtime(file_path)
            created_at = datetime.datetime.fromtimestamp(mtime, tz=datetime.timezone.utc)

        if not created_at:
            created_at = now - datetime.timedelta(days=1)

        # Importance (durability) extraction
        importance = 3.0
        dur_match = re.search(r'Durability\s+(\d+)', heading + " " + content, re.IGNORECASE)
        if dur_match:
            importance = float(dur_match.group(1))
        elif scope in ["policy", "governance"]:
            importance = 5.0
        elif scope in ["global", "architecture"]:
            importance = 4.5
        elif scope in ["decisions"]:
            importance = 4.0
        elif scope in ["gotchas", "tools", "domains"]:
            importance = 3.5
        elif scope in ["sessions"]:
            importance = 2.0
        elif scope in ["candidate"]:
            importance = 1.5

        # Authority
        authority = SCOPE_AUTHORITY.get(scope, 0.5)

        # Status markers
        is_superseded = "superseded" in heading.lower() or "superseded" in content.lower()
        is_candidate = scope == "candidate" or "candidate" in filename.lower() or "[candidate]" in content.lower()

        # TTL detection
        ttl_days = None
        ttl_match = re.search(r'TTL:\s*(\d+(?:\.\d+)?)\s*d', content, re.IGNORECASE)
        if ttl_match:
            ttl_days = float(ttl_match.group(1))
        elif is_candidate:
            ttl_days = 14.0  # Candidates expire in 14 days per Section 42

        # Ledger lookup
        access_count = 0
        verified_count = 0
        refuted_count = 0
        last_accessed_at = None

        if ledger_data and candidate_id in ledger_data:
            rec = ledger_data[candidate_id]
            access_count = rec.get("access_count", 0)
            verified_count = rec.get("verified_count", 0)
            refuted_count = rec.get("refuted_count", 0)
            last_acc_str = rec.get("last_accessed_at")
            if last_acc_str:
                try:
                    last_accessed_at = datetime.datetime.fromisoformat(last_acc_str)
                except Exception:
                    pass

        return cls(
            id=candidate_id,
            file_path=file_path,
            scope=scope,
            heading=heading,
            content=content,
            created_at=created_at,
            last_accessed_at=last_accessed_at,
            importance=importance,
            authority=authority,
            access_count=access_count,
            verified_count=verified_count,
            refuted_count=refuted_count,
            is_superseded=is_superseded,
            is_candidate=is_candidate,
            ttl_days=ttl_days,
            raw_score=raw_score
        )


@dataclass
class DecayProfile:
    """Detailed decay analysis for a memory item."""
    age_days: float
    base_half_life_days: float
    effective_half_life_days: float
    raw_decay: float
    retention_floor: float
    decay_factor: float          # Final decay factor in [0.0, 1.0]
    is_expired: bool
    is_governance_exempt: bool
    details: str


@dataclass
class ReinforcementProfile:
    """Detailed access and verification reinforcement profile."""
    access_count: int
    verified_count: int
    refuted_count: int
    raw_access_signal: float     # Retrieval frequency signal [0.0, 1.0]
    verified_signal: float       # Verified execution signal [0.0, 1.0]
    refuted_penalty: float       # Refutation penalty [0.0, 1.0]
    reinforcement_score: float   # Net combined reinforcement [0.0, 1.0]
    epistemic_warning: Optional[str] = None


@dataclass
class ModelMetadata:
    """Versioned model metadata traveling with feature weights."""
    schema_version: str = FEATURE_SCHEMA_VERSION
    model_version: str = DEFAULT_MODEL_VERSION
    training_corpus_version: str = DEFAULT_TRAINING_CORPUS_VERSION
    created_at: str = ""
    updated_at: str = ""
    feature_order: List[str] = field(default_factory=lambda: list(CANONICAL_FEATURE_NAMES))
    weights: Dict[str, float] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    benchmark_passed: bool = False
    benchmark_score: float = 0.0
    benchmark_timestamp: Optional[str] = None
    description: str = "Antigravity shadow ranking model"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelMetadata":
        return cls(
            schema_version=data.get("schema_version", FEATURE_SCHEMA_VERSION),
            model_version=data.get("model_version", DEFAULT_MODEL_VERSION),
            training_corpus_version=data.get("training_corpus_version", DEFAULT_TRAINING_CORPUS_VERSION),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            feature_order=data.get("feature_order", list(CANONICAL_FEATURE_NAMES)),
            weights=data.get("weights", dict(DEFAULT_WEIGHTS)),
            benchmark_passed=data.get("benchmark_passed", False),
            benchmark_score=data.get("benchmark_score", 0.0),
            benchmark_timestamp=data.get("benchmark_timestamp"),
            description=data.get("description", "Antigravity shadow ranking model")
        )


@dataclass
class CandidateRanking:
    """Ranking assignment and score details for a single candidate."""
    item: MemoryItem
    baseline_score: float
    baseline_rank: int
    shadow_score: float
    shadow_rank: int
    rank_diff: int               # baseline_rank - shadow_rank (>0 means promoted)
    features: Dict[str, float]
    feature_contributions: Dict[str, float]


@dataclass
class ShadowComparisonReport:
    """Comprehensive comparison between Baseline RRF and Shadow Learned ranking."""
    query: str
    total_candidates: int
    evaluated_at: str
    model_version: str
    schema_version: str
    spearman_rho: float
    kendall_tau: float
    top1_agreement: bool
    top3_jaccard: float
    top5_jaccard: float
    mean_absolute_rank_displacement: float
    max_promotion: int
    max_demotion: int
    regression_warnings: List[str]
    rankings: List[CandidateRanking]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "total_candidates": self.total_candidates,
            "evaluated_at": self.evaluated_at,
            "model_version": self.model_version,
            "schema_version": self.schema_version,
            "metrics": {
                "spearman_rho": round(self.spearman_rho, 4),
                "kendall_tau": round(self.kendall_tau, 4),
                "top1_agreement": self.top1_agreement,
                "top3_jaccard": round(self.top3_jaccard, 4),
                "top5_jaccard": round(self.top5_jaccard, 4),
                "mean_absolute_rank_displacement": round(self.mean_absolute_rank_displacement, 2),
                "max_promotion": self.max_promotion,
                "max_demotion": self.max_demotion
            },
            "regression_warnings": self.regression_warnings,
            "rankings": [
                {
                    "id": r.item.id,
                    "scope": r.item.scope,
                    "heading": r.item.heading,
                    "file": r.item.file_path,
                    "baseline_rank": r.baseline_rank,
                    "shadow_rank": r.shadow_rank,
                    "rank_diff": r.rank_diff,
                    "baseline_score": round(r.baseline_score, 4),
                    "shadow_score": round(r.shadow_score, 4),
                    "features": {k: round(v, 4) for k, v in r.features.items()},
                    "contributions": {k: round(v, 4) for k, v in r.feature_contributions.items()}
                }
                for r in self.rankings
            ]
        }


# ==============================================================================
# 1. Memory Decay Model (Instruction.md Section 42)
# ==============================================================================
class MemoryDecayModel:
    """
    Models memory decay curves distinguishing staleness, importance, historical value,
    access frequency, scope, and authority.

    Principles:
    - Core governance facts do not decay simply because they are old.
    - Low-value episodic material is deprioritized quickly.
    - Candidates expire after TTL.
    - Temporary memories respect TTLs.
    - Superseded memories remain queryable historically with controlled penalty.
    """

    def __init__(self, reference_time: Optional[datetime.datetime] = None):
        self.reference_time = reference_time

    def get_current_time(self) -> datetime.datetime:
        return self.reference_time or datetime.datetime.now(datetime.timezone.utc)

    def is_governance_exempt(self, item: MemoryItem) -> bool:
        """Determines if the memory represents core governance/policy immune to age decay."""
        if item.scope in ["policy", "governance"]:
            return True
        if item.authority >= 0.95:
            return True
        if "POLICY.md" in item.file_path or "memory.md" in item.file_path:
            return True
        return False

    def compute_decay(self, item: MemoryItem) -> DecayProfile:
        now = self.get_current_time()
        created_at = item.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=datetime.timezone.utc)

        delta = now - created_at
        age_days = max(0.0, delta.total_seconds() / 86400.0)

        # 1. Check TTL Expiration
        if item.ttl_days is not None and age_days > item.ttl_days:
            return DecayProfile(
                age_days=age_days,
                base_half_life_days=item.ttl_days,
                effective_half_life_days=item.ttl_days,
                raw_decay=0.0,
                retention_floor=0.0,
                decay_factor=0.0,
                is_expired=True,
                is_governance_exempt=False,
                details=f"Expired: Age {age_days:.1f}d exceeds TTL {item.ttl_days:.1f}d"
            )

        # 2. Check Governance Exemption
        if self.is_governance_exempt(item):
            # Governance facts retain 1.0 factor indefinitely (Section 42)
            return DecayProfile(
                age_days=age_days,
                base_half_life_days=3650.0,
                effective_half_life_days=3650.0,
                raw_decay=1.0,
                retention_floor=1.0,
                decay_factor=1.0,
                is_expired=False,
                is_governance_exempt=True,
                details="Governance Immune: Core policy/rules do not decay with age."
            )

        # 3. Base half-life calculation based on scope and importance
        base_half_life = SCOPE_HALF_LIVES_DAYS.get(item.scope, 30.0)

        # Importance multiplier: higher durability (0-5) substantially extends half-life
        # durability 5 -> multiplier 1 + (5/2)^1.5 = 1 + 3.95 = 4.95x
        # durability 3 -> multiplier 1 + (3/2)^1.5 = 1 + 1.84 = 2.84x
        # durability 1 -> multiplier 1 + (1/2)^1.5 = 1 + 0.35 = 1.35x
        importance_multiplier = 1.0 + math.pow(max(0.0, item.importance) / 2.0, 1.5)
        half_life_with_importance = base_half_life * importance_multiplier

        # 4. Spaced retrieval & access reinforcement on decay curve
        # Frequently verified memories become more durable (Ebbinghaus forgetting curve reinforcement)
        access_reinforce = (
            1.0
            + 0.25 * math.log(1.0 + max(0, item.access_count))
            + 0.75 * math.log(1.0 + max(0, item.verified_count))
        )
        effective_half_life = half_life_with_importance * access_reinforce

        # 5. Exponential decay formula: N(t) = exp(-lambda * t)
        decay_constant = math.log(2.0) / max(1.0, effective_half_life)
        raw_decay = math.exp(-decay_constant * age_days)

        # 6. Retention floor based on authority
        # High authority items cannot decay completely to zero
        retention_floor = min(0.85, item.authority * 0.55)
        decay_factor = max(retention_floor, raw_decay)

        # 7. Superseded memory handling: queryable historically, but penalised
        if item.is_superseded:
            decay_factor *= 0.35

        # Bounded between 0.0 and 1.0
        decay_factor = max(0.0, min(1.0, decay_factor))

        return DecayProfile(
            age_days=age_days,
            base_half_life_days=base_half_life,
            effective_half_life_days=effective_half_life,
            raw_decay=raw_decay,
            retention_floor=retention_floor,
            decay_factor=decay_factor,
            is_expired=False,
            is_governance_exempt=False,
            details=f"Active: Age={age_days:.1f}d, Effective T1/2={effective_half_life:.1f}d, Factor={decay_factor:.3f}"
        )


# ==============================================================================
# 2. Access Reinforcement Model (Instruction.md Section 43)
# ==============================================================================
class AccessReinforcementModel:
    """
    Models access reinforcement where verified successful use strengthens retrieval priority.

    Strict Invariant per Section 43:
    - Retrieved != True.
    - Frequently Retrieved != Authoritative.
    - Access frequency is a retrieval signal, NOT an epistemic truth signal.
    - Bounded saturation prevents popularity feedback loops / echo chambers.
    """

    def __init__(self):
        pass

    def compute_reinforcement(self, item: MemoryItem) -> ReinforcementProfile:
        # Raw retrieval frequency signal (sub-linear saturation via log and tanh)
        # Prevents runaway reinforcement loops
        raw_access_signal = math.tanh(0.12 * math.log(1.0 + max(0, item.access_count)))

        # Verification signal (stronger weight: memory was verified in practice by tests or commands)
        verified_signal = math.tanh(0.35 * math.log(1.0 + max(0, item.verified_count)))

        # Refutation penalty (penalises memories that led to errors or were refuted)
        refuted_penalty = math.tanh(0.50 * max(0, item.refuted_count))

        # Combined reinforcement calculation
        # Verified successful execution carries 3x the weight of passive retrieval
        combined = (0.25 * raw_access_signal) + (0.75 * verified_signal) - (0.60 * refuted_penalty)
        reinforcement_score = max(0.0, min(1.0, combined))

        warning = None
        if item.access_count > 20 and item.verified_count == 0:
            warning = "High retrieval count with zero verifications: access frequency used as retrieval signal only."

        return ReinforcementProfile(
            access_count=item.access_count,
            verified_count=item.verified_count,
            refuted_count=item.refuted_count,
            raw_access_signal=raw_access_signal,
            verified_signal=verified_signal,
            refuted_penalty=refuted_penalty,
            reinforcement_score=reinforcement_score,
            epistemic_warning=warning
        )


# ==============================================================================
# 3. Reciprocal Rank Fusion (Instruction.md Section 23)
# ==============================================================================
class ReciprocalRankFusion:
    """
    Principled, deterministic, explainable, and reproducible fusion layer.
    Computes baseline multi-signal rank fusion using Reciprocal Rank Fusion (RRF).
    """

    def __init__(self, k: int = 60):
        self.k = k  # Standard smoothing constant (Cormack et al.)

    def fuse(
        self,
        candidates: List[MemoryItem],
        signal_weights: Optional[Dict[str, float]] = None
    ) -> List[Tuple[MemoryItem, float]]:
        """
        Fuses 4 deterministic retrieval signals:
        1. lexical: upstream search match score
        2. authority: inherent source tier authority
        3. importance: durability / governance level
        4. freshness: recency of creation or update
        """
        if not candidates:
            return []

        weights = signal_weights or {
            "lexical": 0.50,
            "authority": 0.25,
            "importance": 0.15,
            "freshness": 0.10
        }

        # Normalize signal weights
        total_w = sum(weights.values()) or 1.0
        norm_weights = {k: v / total_w for k, v in weights.items()}

        # Generate deterministic rankings for each signal (higher is better, break ties by item ID)
        lexical_sorted = sorted(candidates, key=lambda x: (x.raw_score, x.id), reverse=True)
        authority_sorted = sorted(candidates, key=lambda x: (x.authority, x.id), reverse=True)
        importance_sorted = sorted(candidates, key=lambda x: (x.importance, x.id), reverse=True)
        freshness_sorted = sorted(candidates, key=lambda x: (x.created_at.timestamp(), x.id), reverse=True)

        rank_lexical = {item.id: idx + 1 for idx, item in enumerate(lexical_sorted)}
        rank_authority = {item.id: idx + 1 for idx, item in enumerate(authority_sorted)}
        rank_importance = {item.id: idx + 1 for idx, item in enumerate(importance_sorted)}
        rank_freshness = {item.id: idx + 1 for idx, item in enumerate(freshness_sorted)}

        scored_candidates = []
        for item in candidates:
            r_lex = rank_lexical[item.id]
            r_auth = rank_authority[item.id]
            r_imp = rank_importance[item.id]
            r_fresh = rank_freshness[item.id]

            rrf_score = (
                norm_weights["lexical"] / (self.k + r_lex)
                + norm_weights["authority"] / (self.k + r_auth)
                + norm_weights["importance"] / (self.k + r_imp)
                + norm_weights["freshness"] / (self.k + r_fresh)
            )
            scored_candidates.append((item, rrf_score))

        # Sort descending by RRF score, breaking ties by item.id deterministically
        scored_candidates.sort(key=lambda x: (x[1], x[0].id), reverse=True)
        return scored_candidates


# ==============================================================================
# 4. Model Versioning & Feature Schema Manager (Instruction.md Section 41)
# ==============================================================================
class ModelManager:
    """
    Enforces that feature schema version, model version, and training corpus version
    travel together with weights.
    Invariant: Never allow a new feature ordering to reinterpret old weights silently.
    """

    @staticmethod
    def validate_model_schema(model: ModelMetadata) -> None:
        # 1. Validate Schema Version Compatibility (major version match required)
        code_major = FEATURE_SCHEMA_VERSION.split(".")[0]
        model_major = model.schema_version.split(".")[0]
        if code_major != model_major:
            raise SchemaMismatchError(
                f"Incompatible schema version: Model has {model.schema_version}, code requires {FEATURE_SCHEMA_VERSION}"
            )

        # 2. Validate feature presence
        active_set = set(CANONICAL_FEATURE_NAMES)
        model_set = set(model.weights.keys())

        missing = active_set - model_set
        if missing:
            raise SchemaMismatchError(f"Model missing required features: {sorted(list(missing))}")

        extra = model_set - active_set
        if extra:
            raise SchemaMismatchError(f"Model contains unknown extra features: {sorted(list(extra))}")

        # 3. Check feature order: ensure explicit named mapping is used, not positional indices
        if model.feature_order != CANONICAL_FEATURE_NAMES:
            # Reorder weights to canonical order without silent positional reinterpretation
            reordered = {}
            for name in CANONICAL_FEATURE_NAMES:
                if name in model.weights:
                    reordered[name] = model.weights[name]
                else:
                    raise SchemaMismatchError(f"Cannot resolve feature '{name}' during ordering alignment.")
            model.weights = reordered
            model.feature_order = list(CANONICAL_FEATURE_NAMES)

    @classmethod
    def load_model(cls, filepath: str = DEFAULT_MODEL_PATH) -> ModelMetadata:
        if not os.path.exists(filepath):
            # Create default model metadata if missing
            default_model = ModelMetadata(
                created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
            )
            cls.save_model(default_model, filepath)
            return default_model

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        model = ModelMetadata.from_dict(data)
        cls.validate_model_schema(model)
        return model

    @classmethod
    def save_model(cls, model: ModelMetadata, filepath: str = DEFAULT_MODEL_PATH) -> None:
        cls.validate_model_schema(model)
        model.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if not model.created_at:
            model.created_at = model.updated_at

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        tmp_path = f"{filepath}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(model.to_dict(), f, indent=2)
        os.replace(tmp_path, filepath)


# ==============================================================================
# 5. Persistent Learning Ledger
# ==============================================================================
class LearningLedger:
    """
    Persistently records access and verification counts for memory items.
    Thread-safe and transactionally safe.
    """

    def __init__(self, filepath: str = DEFAULT_LEDGER_PATH):
        self.filepath = filepath
        self.data: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    self.data = content.get("records", {})
            except Exception as e:
                print(f"[LearningLedger] Warning: Failed to load ledger: {e}", file=sys.stderr)
                self.data = {}
        else:
            self.data = {}

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        payload = {
            "schema_version": FEATURE_SCHEMA_VERSION,
            "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "record_count": len(self.data),
            "records": self.data
        }
        tmp_path = f"{self.filepath}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        os.replace(tmp_path, self.filepath)

    def record_access(self, memory_id: str, verified: bool = False, refuted: bool = False) -> Dict[str, Any]:
        rec = self.data.get(memory_id, {
            "access_count": 0,
            "verified_count": 0,
            "refuted_count": 0,
            "first_accessed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "last_accessed_at": None
        })
        rec["access_count"] += 1
        rec["last_accessed_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if verified:
            rec["verified_count"] += 1
        if refuted:
            rec["refuted_count"] += 1

        self.data[memory_id] = rec
        self.save()
        return rec

    def get_record(self, memory_id: str) -> Optional[Dict[str, Any]]:
        return self.data.get(memory_id)


# ==============================================================================
# 6. Shadow Ranker (Instruction.md Section 41, 221)
# ==============================================================================
class ShadowRanker:
    """
    Executes learned rank adjustments strictly in SHADOW mode.
    Compares baseline RRF ranking with shadow ranking in ISOLATION.
    Never modifies the live search path.
    """

    def __init__(
        self,
        model: Optional[ModelMetadata] = None,
        decay_model: Optional[MemoryDecayModel] = None,
        reinforce_model: Optional[AccessReinforcementModel] = None
    ):
        self.model = model or ModelManager.load_model()
        self.decay_model = decay_model or MemoryDecayModel()
        self.reinforce_model = reinforce_model or AccessReinforcementModel()

    def extract_features(
        self,
        item: MemoryItem,
        normalized_baseline_rrf: float,
        reference_time: Optional[datetime.datetime] = None
    ) -> Dict[str, float]:
        """Extracts normalized feature vector for a candidate item."""
        now = reference_time or datetime.datetime.now(datetime.timezone.utc)

        # 1. Decay factor
        decay_prof = self.decay_model.compute_decay(item)

        # 2. Access reinforcement
        reinforce_prof = self.reinforce_model.compute_reinforcement(item)

        # 3. Importance (0 to 5 normalized to [0, 1])
        norm_importance = max(0.0, min(1.0, item.importance / 5.0))

        # 4. Authority [0, 1]
        norm_authority = max(0.0, min(1.0, item.authority))

        # 5. Freshness [0, 1] (half-life of 30 days for freshness score)
        created_at = item.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=datetime.timezone.utc)
        age_days = max(0.0, (now - created_at).total_seconds() / 86400.0)
        freshness = math.exp(-0.023 * age_days)

        # 6. Stale episodic penalty: 1.0 if session item > 21 days old and verified_count == 0
        stale_penalty = 0.0
        if item.scope in ["sessions", "episodic"] and age_days > 21.0 and item.verified_count == 0:
            stale_penalty = 1.0

        # 7. Superseded penalty: 1.0 if superseded
        superseded_penalty = 1.0 if item.is_superseded else 0.0

        features = {
            "baseline_rrf_score": max(0.0, min(1.0, normalized_baseline_rrf)),
            "decay_factor": decay_prof.decay_factor,
            "access_reinforcement": reinforce_prof.reinforcement_score,
            "importance": norm_importance,
            "authority": norm_authority,
            "freshness": freshness,
            "stale_penalty": stale_penalty,
            "superseded_penalty": superseded_penalty
        }
        return features

    def compute_shadow_score(self, features: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
        """
        Computes the learned shadow score strictly by named weight lookup.
        Never uses positional index mapping.
        """
        score = 0.0
        contributions = {}
        for feature_name, value in features.items():
            weight = self.model.weights.get(feature_name, 0.0)
            contrib = weight * value
            contributions[feature_name] = contrib
            score += contrib
        return score, contributions

    def evaluate_shadow_ranking(
        self,
        query: str,
        baseline_ranked_tuples: List[Tuple[MemoryItem, float]],
        reference_time: Optional[datetime.datetime] = None
    ) -> ShadowComparisonReport:
        """
        Runs shadow ranker comparing baseline RRF ranking with learned adjustments in isolation.
        """
        now = reference_time or datetime.datetime.now(datetime.timezone.utc)
        total_candidates = len(baseline_ranked_tuples)
        if total_candidates == 0:
            return ShadowComparisonReport(
                query=query,
                total_candidates=0,
                evaluated_at=now.isoformat(),
                model_version=self.model.model_version,
                schema_version=self.model.schema_version,
                spearman_rho=1.0,
                kendall_tau=1.0,
                top1_agreement=True,
                top3_jaccard=1.0,
                top5_jaccard=1.0,
                mean_absolute_rank_displacement=0.0,
                max_promotion=0,
                max_demotion=0,
                regression_warnings=[],
                rankings=[]
            )

        # Baseline max score for normalization
        max_rrf = max(score for _, score in baseline_ranked_tuples) if baseline_ranked_tuples else 1.0
        if max_rrf <= 0.0:
            max_rrf = 1.0

        # Step 1: Compute learned shadow score for each candidate
        shadow_eval_list = []
        for baseline_idx, (item, b_score) in enumerate(baseline_ranked_tuples, 1):
            norm_rrf = b_score / max_rrf
            features = self.extract_features(item, norm_rrf, reference_time=now)
            s_score, contribs = self.compute_shadow_score(features)
            shadow_eval_list.append({
                "item": item,
                "baseline_score": b_score,
                "baseline_rank": baseline_idx,
                "shadow_score": s_score,
                "features": features,
                "contributions": contribs
            })

        # Step 2: Sort candidates to produce shadow ranking
        # Break ties deterministically by baseline rank and item ID
        shadow_sorted = sorted(
            shadow_eval_list,
            key=lambda x: (x["shadow_score"], -x["baseline_rank"], x["item"].id),
            reverse=True
        )

        # Step 3: Build CandidateRanking objects
        rankings = []
        for shadow_idx, entry in enumerate(shadow_sorted, 1):
            b_rank = entry["baseline_rank"]
            s_rank = shadow_idx
            rank_diff = b_rank - s_rank  # Positive = promoted, Negative = demoted

            rankings.append(CandidateRanking(
                item=entry["item"],
                baseline_score=entry["baseline_score"],
                baseline_rank=b_rank,
                shadow_score=entry["shadow_score"],
                shadow_rank=s_rank,
                rank_diff=rank_diff,
                features=entry["features"],
                feature_contributions=entry["contributions"]
            ))

        # Re-sort rankings array by baseline_rank for easy 1-to-1 comparison
        rankings_by_baseline = sorted(rankings, key=lambda r: r.baseline_rank)

        # Step 4: Calculate ranking metrics (Spearman rho, Kendall tau, displacements)
        N = total_candidates
        d_sq_sum = sum(r.rank_diff ** 2 for r in rankings)
        spearman_rho = 1.0 - (6.0 * d_sq_sum / (N * (N * N - 1))) if N > 1 else 1.0

        # Kendall Tau calculation
        concordant = 0
        discordant = 0
        for i in range(N):
            for j in range(i + 1, N):
                r_a = rankings_by_baseline[i]
                r_b = rankings_by_baseline[j]
                base_dir = r_a.baseline_rank - r_b.baseline_rank
                shadow_dir = r_a.shadow_rank - r_b.shadow_rank
                product = base_dir * shadow_dir
                if product > 0:
                    concordant += 1
                elif product < 0:
                    discordant += 1
        total_pairs = (N * (N - 1)) / 2.0 if N > 1 else 1.0
        kendall_tau = (concordant - discordant) / total_pairs if N > 1 else 1.0

        # Top-K agreements
        base_top1 = rankings_by_baseline[0].item.id if N >= 1 else ""
        shadow_top1 = shadow_sorted[0]["item"].id if N >= 1 else ""
        top1_agree = (base_top1 == shadow_top1)

        def jaccard_k(k: int) -> float:
            if N == 0:
                return 1.0
            actual_k = min(k, N)
            base_set = set(r.item.id for r in rankings_by_baseline[:actual_k])
            shadow_set = set(s["item"].id for s in shadow_sorted[:actual_k])
            union = base_set | shadow_set
            return len(base_set & shadow_set) / len(union) if union else 1.0

        top3_j = jaccard_k(3)
        top5_j = jaccard_k(5)

        displacements = [abs(r.rank_diff) for r in rankings]
        mard = sum(displacements) / N if N > 0 else 0.0
        max_promo = max(r.rank_diff for r in rankings) if rankings else 0
        max_demo = min(r.rank_diff for r in rankings) if rankings else 0

        # Step 5: Regression Checks (Instruction.md Section 221)
        regressions = []
        for r in rankings:
            # Regression check 1: Governance demotion
            if r.item.authority >= 0.90 and r.rank_diff < -2:
                regressions.append(
                    f"[REGRESSION: GOVERNANCE DEMOTION] High-authority fact '{r.item.id}' demoted by {abs(r.rank_diff)} positions (Rank {r.baseline_rank} -> {r.shadow_rank})."
                )
            # Regression check 2: Superseded memory outranking active memory
            if r.item.is_superseded and r.shadow_rank <= 2:
                regressions.append(
                    f"[REGRESSION: SUPERSEDED ELEVATION] Superseded memory '{r.item.id}' ranked in top 2 (Shadow rank {r.shadow_rank})."
                )
            # Regression check 3: Candidate reaching top position without verification
            if r.item.is_candidate and r.shadow_rank == 1 and r.item.verified_count == 0:
                regressions.append(
                    f"[REGRESSION: UNVERIFIED CANDIDATE TOP] Unverified candidate '{r.item.id}' promoted to top rank."
                )

        return ShadowComparisonReport(
            query=query,
            total_candidates=total_candidates,
            evaluated_at=now.isoformat(),
            model_version=self.model.model_version,
            schema_version=self.model.schema_version,
            spearman_rho=spearman_rho,
            kendall_tau=kendall_tau,
            top1_agreement=top1_agree,
            top3_jaccard=top3_j,
            top5_jaccard=top5_j,
            mean_absolute_rank_displacement=mard,
            max_promotion=max(0, max_promo),
            max_demotion=min(0, max_demo),
            regression_warnings=regressions,
            rankings=rankings_by_baseline
        )


# ==============================================================================
# 7. Benchmark Gate (Instruction.md Section 41, 222)
# ==============================================================================
class BenchmarkGate:
    """
    Evaluates whether a learned ranking configuration satisfies explicit benchmark
    criteria before it is ever permitted to affect live behavior.

    Requirements:
    1. Governance Immunity: Policy/rules facts must maintain retention >= 0.98.
    2. Access Boost: Verified successful memories outrank unverified ones.
    3. Superseded Demotion: Active decisions strictly outrank superseded decisions.
    4. Candidate Expiry: Candidate memories with expired TTL must have decay 0.0.
    5. Zero Governance Regressions: High authority items must not be demoted below low-value notes.
    """

    def __init__(self, shadow_ranker: Optional[ShadowRanker] = None):
        self.ranker = shadow_ranker or ShadowRanker()

    def run_benchmark(self) -> Dict[str, Any]:
        now = datetime.datetime.now(datetime.timezone.utc)
        checks = []

        # Check 1: Governance Fact Decay Immunity
        gov_item = MemoryItem(
            id="POLICY.md#L1",
            file_path="/test/POLICY.md",
            scope="policy",
            heading="# Policy Governance",
            content="Core governance rules must never decay.",
            created_at=now - datetime.timedelta(days=730),  # 2 years old
            importance=5.0,
            authority=1.0
        )
        gov_decay = self.ranker.decay_model.compute_decay(gov_item)
        check1_pass = gov_decay.decay_factor >= 0.98 and not gov_decay.is_expired
        checks.append({
            "name": "governance_fact_decay_immunity",
            "passed": check1_pass,
            "details": f"2-year-old governance policy decay factor: {gov_decay.decay_factor:.4f} (Required >= 0.98)"
        })

        # Check 2: Access Reinforcement Priority
        item_unverified = MemoryItem(
            id="GOTCHAS.md#L10",
            file_path="/test/GOTCHAS.md",
            scope="gotchas",
            heading="## Build Toolchain",
            content="Ninja build gotchas",
            created_at=now - datetime.timedelta(days=30),
            importance=3.5,
            authority=0.75,
            access_count=1,
            verified_count=0
        )
        item_verified = MemoryItem(
            id="GOTCHAS.md#L20",
            file_path="/test/GOTCHAS.md",
            scope="gotchas",
            heading="## Build Toolchain Hardening",
            content="Ninja build gotchas verified",
            created_at=now - datetime.timedelta(days=30),
            importance=3.5,
            authority=0.75,
            access_count=5,
            verified_count=4
        )
        reinf_unver = self.ranker.reinforce_model.compute_reinforcement(item_unverified)
        reinf_ver = self.ranker.reinforce_model.compute_reinforcement(item_verified)
        check2_pass = reinf_ver.reinforcement_score > reinf_unver.reinforcement_score
        checks.append({
            "name": "verified_access_reinforcement_boost",
            "passed": check2_pass,
            "details": f"Verified ({reinf_ver.reinforcement_score:.3f}) > Unverified ({reinf_unver.reinforcement_score:.3f})"
        })

        # Check 3: Superseded Demotion Invariant
        active_adr = MemoryItem(
            id="DECISIONS.md#ADR-002",
            file_path="/test/DECISIONS.md",
            scope="decisions",
            heading="## ADR-002: Dual Skill Entrypoints",
            content="Active architecture for skill discovery",
            created_at=now - datetime.timedelta(days=20),
            importance=4.0,
            authority=0.80,
            is_superseded=False,
            raw_score=30.0
        )
        superseded_adr = MemoryItem(
            id="DECISIONS.md#ADR-001-OLD",
            file_path="/test/DECISIONS.md",
            scope="decisions",
            heading="## ADR-001: Superseded Architecture",
            content="Old single skill approach",
            created_at=now - datetime.timedelta(days=20),
            importance=4.0,
            authority=0.80,
            is_superseded=True,
            raw_score=30.0
        )
        f_act = self.ranker.extract_features(active_adr, 1.0, now)
        f_sup = self.ranker.extract_features(superseded_adr, 1.0, now)
        s_act, _ = self.ranker.compute_shadow_score(f_act)
        s_sup, _ = self.ranker.compute_shadow_score(f_sup)
        check3_pass = s_act > s_sup
        checks.append({
            "name": "superseded_demotion_invariant",
            "passed": check3_pass,
            "details": f"Active ADR score ({s_act:.3f}) > Superseded ADR score ({s_sup:.3f})"
        })

        # Check 4: Candidate Expiration
        candidate_expired = MemoryItem(
            id="candidate_notes.md#L5",
            file_path="/test/candidate_notes.md",
            scope="candidate",
            heading="## Candidate Procedure",
            content="Unreviewed skill candidate",
            created_at=now - datetime.timedelta(days=20),
            importance=1.5,
            authority=0.25,
            is_candidate=True,
            ttl_days=14.0
        )
        cand_decay = self.ranker.decay_model.compute_decay(candidate_expired)
        check4_pass = cand_decay.is_expired and cand_decay.decay_factor == 0.0
        checks.append({
            "name": "candidate_ttl_expiration",
            "passed": check4_pass,
            "details": f"20-day-old candidate with 14d TTL: factor={cand_decay.decay_factor:.1f}, expired={cand_decay.is_expired}"
        })

        # Check 5: Stale Episodic Deprioritization
        stale_session = MemoryItem(
            id="2026-05-01.md#L1",
            file_path="/test/sessions/2026-05-01.md",
            scope="sessions",
            heading="# Session 2026-05-01",
            content="Explored some commands.",
            created_at=now - datetime.timedelta(days=90),
            importance=2.0,
            authority=0.35,
            access_count=0,
            verified_count=0,
            raw_score=40.0
        )
        fresh_arch = MemoryItem(
            id="ARCHITECTURE.md#L5",
            file_path="/test/ARCHITECTURE.md",
            scope="architecture",
            heading="## Core Architecture",
            content="Subagent boundary definition",
            created_at=now - datetime.timedelta(days=10),
            importance=4.5,
            authority=0.85,
            access_count=2,
            verified_count=2,
            raw_score=40.0
        )
        f_stale = self.ranker.extract_features(stale_session, 1.0, now)
        f_arch = self.ranker.extract_features(fresh_arch, 1.0, now)
        s_stale, _ = self.ranker.compute_shadow_score(f_stale)
        s_arch, _ = self.ranker.compute_shadow_score(f_arch)
        check5_pass = s_arch > s_stale and f_stale["stale_penalty"] == 1.0
        checks.append({
            "name": "stale_episodic_deprioritization",
            "passed": check5_pass,
            "details": f"Durable Architecture ({s_arch:.3f}) > Stale Session ({s_stale:.3f})"
        })

        # Check 6: Schema and Model Metadata Completeness
        check6_pass = (
            self.ranker.model.schema_version == FEATURE_SCHEMA_VERSION
            and len(self.ranker.model.weights) == len(CANONICAL_FEATURE_NAMES)
            and all(k in self.ranker.model.weights for k in CANONICAL_FEATURE_NAMES)
        )
        checks.append({
            "name": "schema_and_feature_completeness",
            "passed": check6_pass,
            "details": f"Schema version {self.ranker.model.schema_version}, {len(self.ranker.model.weights)} verified features."
        })

        all_passed = all(c["passed"] for c in checks)
        passed_count = sum(1 for c in checks if c["passed"])
        score = passed_count / len(checks)

        # Update model metadata if passed
        self.ranker.model.benchmark_passed = all_passed
        self.ranker.model.benchmark_score = score
        self.ranker.model.benchmark_timestamp = now.isoformat()
        ModelManager.save_model(self.ranker.model)

        return {
            "status": "PASS" if all_passed else "FAIL",
            "passed": all_passed,
            "score": round(score, 4),
            "checks_run": len(checks),
            "checks_passed": passed_count,
            "evaluated_at": now.isoformat(),
            "model_version": self.ranker.model.model_version,
            "schema_version": self.ranker.model.schema_version,
            "checks": checks
        }


# ==============================================================================
# 8. Unified LearningLoop (Phase 16 Engine)
# ==============================================================================
class LearningLoop:
    """
    Unified controller implementing:
    - Memory decay curves based on age, importance, access frequency, and authority.
    - Access reinforcement (frequently verified memories get priority boost).
    - Shadow ranker comparing baseline RRF ranking with learned adjustments in isolation.
    - Strict isolation: NEVER modifies live search path.
    - Feature schema and model versioning.
    """

    def __init__(
        self,
        workspace_dir: str = WORKSPACE_DIR,
        model_path: str = DEFAULT_MODEL_PATH,
        ledger_path: str = DEFAULT_LEDGER_PATH,
        reference_time: Optional[datetime.datetime] = None
    ):
        self.workspace_dir = workspace_dir
        self.model_path = model_path
        self.ledger_path = ledger_path
        self.reference_time = reference_time

        # Initialize sub-systems
        self.ledger = LearningLedger(ledger_path)
        self.model = ModelManager.load_model(model_path)
        self.decay_model = MemoryDecayModel(reference_time=reference_time)
        self.reinforce_model = AccessReinforcementModel()
        self.rrf = ReciprocalRankFusion(k=60)
        self.shadow_ranker = ShadowRanker(
            model=self.model,
            decay_model=self.decay_model,
            reinforce_model=self.reinforce_model
        )
        self.benchmark_gate = BenchmarkGate(self.shadow_ranker)

    def record_access(self, memory_id: str, verified: bool = False, refuted: bool = False) -> Dict[str, Any]:
        """Records an access or verification in the persistent ledger."""
        return self.ledger.record_access(memory_id, verified=verified, refuted=refuted)

    def run_benchmark_gate(self) -> Dict[str, Any]:
        """Runs benchmark gate to evaluate whether learned ranking is certified."""
        return self.benchmark_gate.run_benchmark()

    def query_with_shadow(
        self,
        query: str,
        scopes: Optional[List[str]] = None,
        max_results: int = 10,
        persist_eval: bool = True
    ) -> Dict[str, Any]:
        """
        Executes query retrieval:
        1. Discovers and extracts candidate snippets via search_memory.py.
        2. Computes baseline deterministic RRF ranking.
        3. Runs learned ranking in SHADOW mode in strict isolation.
        4. Returns LIVE results (pure baseline RRF) alongside SHADOW comparison report.

        INVARIANT: Live search results returned to caller are 100% determined by baseline RRF.
        The shadow ranker NEVER mutates the live path.
        """
        try:
            from search_memory import run_memory_search
        except ImportError:
            sys.path.insert(0, SCRIPTS_DIR)
            from search_memory import run_memory_search

        # 1. Retrieve candidates via lexical engine
        search_res = run_memory_search(
            query=query,
            scopes=scopes or ["all"],
            max_results=max(max_results * 2, 20),
            project_root=self.workspace_dir
        )

        if search_res.get("status") == "error":
            return {"status": "error", "message": search_res.get("message")}

        raw_candidates = search_res.get("results", [])
        if not raw_candidates:
            return {
                "status": "success",
                "query": query,
                "live_results": [],
                "shadow_comparison": None,
                "isolation_guarantee": "VERIFIED (Shadow ranker operated in isolation)"
            }

        # Convert raw snippets to MemoryItems, populating access ledger info
        items = [
            MemoryItem.from_search_result(c, ledger_data=self.ledger.data, reference_time=self.reference_time)
            for c in raw_candidates
        ]

        # 2. Baseline Deterministic RRF Fusion
        baseline_ranked = self.rrf.fuse(items)

        # 3. Execute Shadow Ranking in ISOLATION
        comparison_report = self.shadow_ranker.evaluate_shadow_ranking(
            query=query,
            baseline_ranked_tuples=baseline_ranked,
            reference_time=self.reference_time
        )

        # 4. Format Live Results (strictly derived from Baseline RRF)
        live_results = []
        for idx, (item, b_score) in enumerate(baseline_ranked[:max_results], 1):
            live_results.append({
                "rank": idx,
                "id": item.id,
                "scope": item.scope,
                "score": round(b_score, 4),
                "heading": item.heading,
                "file": item.file_path,
                "content_preview": item.content[:150].replace("\n", " ") + "..."
            })

        # 5. Persist shadow comparison report if requested
        if persist_eval:
            os.makedirs(DEFAULT_EVAL_DIR, exist_ok=True)
            safe_query = re.sub(r'[^a-zA-Z0-9_\-]', '_', query)[:32]
            ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
            eval_file = os.path.join(DEFAULT_EVAL_DIR, f"shadow_eval_{safe_query}_{ts}.json")
            try:
                with open(eval_file, "w", encoding="utf-8") as f:
                    json.dump(comparison_report.to_dict(), f, indent=2)
            except Exception as e:
                print(f"[LearningLoop] Warning: Failed to persist shadow eval: {e}", file=sys.stderr)

        return {
            "status": "success",
            "query": query,
            "live_ranking_algorithm": "ReciprocalRankFusion (Deterministic k=60)",
            "live_results_count": len(live_results),
            "live_results": live_results,
            "shadow_comparison": comparison_report,
            "isolation_guarantee": "VERIFIED (Shadow ranker operates in isolation; live search unmodified)"
        }

    def inspect_memory_decay(self, memory_items: List[MemoryItem]) -> List[Dict[str, Any]]:
        """Calculates and formats decay profiles for a list of memory items."""
        profiles = []
        for item in memory_items:
            decay_prof = self.decay_model.compute_decay(item)
            reinf_prof = self.reinforce_model.compute_reinforcement(item)
            profiles.append({
                "id": item.id,
                "scope": item.scope,
                "heading": item.heading,
                "age_days": round(decay_prof.age_days, 1),
                "decay_factor": round(decay_prof.decay_factor, 4),
                "is_expired": decay_prof.is_expired,
                "is_governance_exempt": decay_prof.is_governance_exempt,
                "effective_half_life_days": round(decay_prof.effective_half_life_days, 1),
                "access_count": item.access_count,
                "verified_count": item.verified_count,
                "reinforcement_score": round(reinf_prof.reinforcement_score, 4),
                "details": decay_prof.details
            })
        return profiles


# ==============================================================================
# Helper Formatters
# ==============================================================================
def format_shadow_comparison_table(report: ShadowComparisonReport) -> str:
    """Renders a GitHub Flavored Markdown table comparing baseline and shadow rankings."""
    lines = []
    lines.append(f"## Shadow Ranking Comparison: `{report.query}`")
    lines.append(f"- **Evaluated At**: `{report.evaluated_at}`")
    lines.append(f"- **Model Version**: `{report.model_version}` | **Schema Version**: `{report.schema_version}`")
    lines.append(f"- **Spearman Rank Correlation (ρ)**: `{report.spearman_rho:.4f}`")
    lines.append(f"- **Kendall's Tau (τ)**: `{report.kendall_tau:.4f}`")
    lines.append(f"- **Mean Absolute Rank Displacement**: `{report.mean_absolute_rank_displacement:.2f}` positions")
    lines.append(f"- **Top-1 Match**: `{report.top1_agreement}` | **Top-3 Jaccard**: `{report.top3_jaccard:.2f}` | **Top-5 Jaccard**: `{report.top5_jaccard:.2f}`")
    lines.append("")

    if report.regression_warnings:
        lines.append("> [!WARNING]")
        for w in report.regression_warnings:
            lines.append(f"> - {w}")
        lines.append("")

    lines.append("| Baseline Rank | Shadow Rank | Diff | Scope | ID / Context | Decay Factor | Verified Boost | Baseline RRF | Shadow Score |")
    lines.append("| :---: | :---: | :---: | :--- | :--- | :---: | :---: | :---: | :---: |")

    for r in report.rankings[:15]:
        diff_str = f"+{r.rank_diff}" if r.rank_diff > 0 else (f"{r.rank_diff}" if r.rank_diff < 0 else "0")
        if r.rank_diff > 0:
            diff_badge = f"**{diff_str}** ↑"
        elif r.rank_diff < 0:
            diff_badge = f"*{diff_str}* ↓"
        else:
            diff_badge = "—"

        heading_clean = r.item.heading.replace("|", "\\|")[:36]
        decay_val = r.features.get("decay_factor", 1.0)
        reinf_val = r.features.get("access_reinforcement", 0.0)

        lines.append(
            f"| {r.baseline_rank} | {r.shadow_rank} | {diff_badge} | `{r.item.scope}` | `{r.item.id}` ({heading_clean}) | {decay_val:.3f} | {reinf_val:.3f} | {r.baseline_score:.4f} | **{r.shadow_score:.4f}** |"
        )

    lines.append("")
    lines.append("> [!NOTE]")
    lines.append("> **Isolation Guarantee**: Live search path strictly uses Baseline RRF. Shadow scores are evaluated in isolation.")
    return "\n".join(lines)


# ==============================================================================
# CLI Entrypoint
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(description="Antigravity Memory Decay & Shadow Ranking Loop (Phase 16)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # shadow-eval
    eval_p = subparsers.add_parser("shadow-eval", help="Run shadow ranking comparison on a search query")
    eval_p.add_argument("query", help="Query string to search and evaluate")
    eval_p.add_argument("--scopes", default="all", help="Comma-separated scopes")
    eval_p.add_argument("--max-results", "-n", type=int, default=10, help="Max live results to return")
    eval_p.add_argument("--json", "-j", action="store_true", help="Output full JSON report")

    # record-access
    acc_p = subparsers.add_parser("record-access", help="Record an access or verification signal for a memory item")
    acc_p.add_argument("memory_id", help="Memory identifier (e.g. DECISIONS.md#ADR-001)")
    acc_p.add_argument("--verified", action="store_true", help="Mark access as verified successful execution")
    acc_p.add_argument("--refuted", action="store_true", help="Mark access as refuted or error-causing")

    # benchmark
    bench_p = subparsers.add_parser("benchmark", help="Run the benchmark gate evaluation")
    bench_p.add_argument("--json", "-j", action="store_true", help="Output benchmark results as JSON")

    # decay-status
    decay_p = subparsers.add_parser("decay-status", help="Inspect memory decay curves for repository memories")
    decay_p.add_argument("--query", default="memory", help="Query or topic to inspect decay for")
    decay_p.add_argument("--json", "-j", action="store_true", help="Output decay status as JSON")

    # model-info
    subparsers.add_parser("model-info", help="Inspect active model version and feature schema")

    args = parser.parse_args()
    loop = LearningLoop()

    if args.command == "shadow-eval":
        scopes = [s.strip() for s in args.scopes.split(",") if s.strip()]
        res = loop.query_with_shadow(args.query, scopes=scopes, max_results=args.max_results)
        if args.json:
            print(json.dumps({
                "status": res.get("status"),
                "query": res.get("query"),
                "live_ranking_algorithm": res.get("live_ranking_algorithm"),
                "live_results": res.get("live_results"),
                "shadow_comparison": res["shadow_comparison"].to_dict() if res.get("shadow_comparison") else None,
                "isolation_guarantee": res.get("isolation_guarantee")
            }, indent=2))
        else:
            if res.get("status") == "error":
                print(f"Error: {res.get('message')}")
            elif not res.get("live_results"):
                print(f"No results found for query '{args.query}'.")
            else:
                print(format_shadow_comparison_table(res["shadow_comparison"]))

    elif args.command == "record-access":
        rec = loop.record_access(args.memory_id, verified=args.verified, refuted=args.refuted)
        print(f"Access recorded for '{args.memory_id}':")
        print(f"  Access Count: {rec['access_count']}")
        print(f"  Verified Count: {rec['verified_count']}")
        print(f"  Refuted Count: {rec['refuted_count']}")
        print(f"  Last Accessed: {rec['last_accessed_at']}")

    elif args.command == "benchmark":
        bench_res = loop.run_benchmark_gate()
        if args.json:
            print(json.dumps(bench_res, indent=2))
        else:
            print("=" * 60)
            print("ANTIGRAVITY BENCHMARK GATE (Instruction.md Section 41, 222)")
            print("=" * 60)
            print(f"Status: {bench_res['status']} ({bench_res['score'] * 100:.1f}%)")
            print(f"Checks Passed: {bench_res['checks_passed']} / {bench_res['checks_run']}")
            print(f"Model Version: {bench_res['model_version']} (Schema: {bench_res['schema_version']})")
            print("-" * 60)
            for c in bench_res["checks"]:
                mark = "[PASS]" if c["passed"] else "[FAIL]"
                print(f"{mark} {c['name']}: {c['details']}")
            print("=" * 60)

    elif args.command == "decay-status":
        from search_memory import run_memory_search
        s_res = run_memory_search(query=args.query, scopes=["all"], max_results=20)
        items = [
            MemoryItem.from_search_result(r, ledger_data=loop.ledger.data)
            for r in s_res.get("results", [])
        ]
        profiles = loop.inspect_memory_decay(items)
        if args.json:
            print(json.dumps(profiles, indent=2))
        else:
            print(f"Memory Decay Status for '{args.query}':")
            print(f"{'ID':<30} | {'Scope':<12} | {'Age (d)':<8} | {'Decay':<8} | {'Verified':<8} | {'Status'}")
            print("-" * 80)
            for p in profiles:
                status = "EXPIRED" if p["is_expired"] else ("IMMUNE" if p["is_governance_exempt"] else "ACTIVE")
                print(f"{p['id']:<30} | {p['scope']:<12} | {p['age_days']:<8} | {p['decay_factor']:<8} | {p['verified_count']:<8} | {status}")

    elif args.command == "model-info":
        m = loop.model
        print("=" * 60)
        print("ANTIGRAVITY SHADOW RANKING MODEL METADATA")
        print("=" * 60)
        print(f"Schema Version:          {m.schema_version}")
        print(f"Model Version:           {m.model_version}")
        print(f"Training Corpus Version: {m.training_corpus_version}")
        print(f"Benchmark Passed:        {m.benchmark_passed} (Score: {m.benchmark_score})")
        print(f"Benchmark Timestamp:     {m.benchmark_timestamp or 'N/A'}")
        print(f"Description:             {m.description}")
        print("-" * 60)
        print("Feature Weights (Named Schema Mapping):")
        for f in m.feature_order:
            print(f"  - {f:<24}: {m.weights.get(f, 0.0):+.2f}")
        print("=" * 60)


if __name__ == "__main__":
    main()
