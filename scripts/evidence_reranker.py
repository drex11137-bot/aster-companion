#!/usr/bin/env python3
"""
evidence_reranker.py - Multi-Signal Evidence Reranker Engine.
Part of Antigravity Memory OS Phase 2 & Phase 7.

Strictly enforces:
- Instruction.md Section 17 (CONFIDENCE MUST NOT BE ONE NUMBER: Separates epistemic_confidence,
  source_authority, freshness/temporal_penalty, and retrieval_relevance).
- Instruction.md Section 22 (SOURCE AUTHORITY: USER_EXPLICIT > EXECUTED_TEST > REPOSITORY_SOURCE
  > AGENT_OBSERVATION > AGENT_INFERENCE > UNVERIFIED).
- Instruction.md Section 24 (TRUST VERDICTS: CERTIFY, ADVISORY, UNVERIFIED, SUPERSEDED, BLOCK).
- Core Principle: "Relevance != Truth: an unverified or superseded record never outranks an authoritative current fact."
"""

import os
import re
from dataclasses import dataclass, asdict
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple


class SourceTier(str, Enum):
    USER_EXPLICIT = "USER_EXPLICIT"
    EXECUTED_TEST = "EXECUTED_TEST"
    REPOSITORY_SOURCE = "REPOSITORY_SOURCE"
    COMMAND_OUTPUT = "COMMAND_OUTPUT"
    OFFICIAL_DOCUMENTATION = "OFFICIAL_DOCUMENTATION"
    TRUSTED_EXTERNAL_SOURCE = "TRUSTED_EXTERNAL_SOURCE"
    AGENT_OBSERVATION = "AGENT_OBSERVATION"
    DERIVED_SUMMARY = "DERIVED_SUMMARY"
    AGENT_INFERENCE = "AGENT_INFERENCE"
    UNVERIFIED = "UNVERIFIED"


# Source Tier Authority Weights per Instruction.md Section 22
SOURCE_TIER_WEIGHTS: Dict[str, float] = {
    SourceTier.USER_EXPLICIT.value: 1.0,
    SourceTier.EXECUTED_TEST.value: 0.95,
    SourceTier.REPOSITORY_SOURCE.value: 0.9,
    "REPO_SOURCE": 0.9,
    "AUTHORITATIVE_REPO": 0.9,
    SourceTier.COMMAND_OUTPUT.value: 0.9,
    SourceTier.OFFICIAL_DOCUMENTATION.value: 0.85,
    SourceTier.TRUSTED_EXTERNAL_SOURCE.value: 0.85,
    SourceTier.AGENT_OBSERVATION.value: 0.7,
    SourceTier.DERIVED_SUMMARY.value: 0.5,
    SourceTier.AGENT_INFERENCE.value: 0.4,
    SourceTier.UNVERIFIED.value: 0.2,
    "UNVERIFIED_CLAIM": 0.2,
}

# Epistemic Confidence Tier Weights per Instruction.md Section 17
CONFIDENCE_TIER_WEIGHTS: Dict[str, float] = {
    "VERIFIED": 1.0,
    "CERTAIN": 1.0,
    "HIGH": 0.9,
    "MEDIUM": 0.6,
    "PROBABLE": 0.6,
    "LOW": 0.4,
    "UNCERTAIN": 0.4,
    "UNVERIFIED": 0.2,
}

# Temporal Penalties per Instruction.md Section 17 & 22
SUPERSEDED_PENALTY: float = -0.5
STALE_PENALTY: float = -0.2


class TrustVerdict(str, Enum):
    CERTIFY = "CERTIFY"
    ADVISORY = "ADVISORY"
    UNVERIFIED = "UNVERIFIED"
    SUPERSEDED = "SUPERSEDED"
    BLOCK = "BLOCK"


@dataclass
class EvidenceSignals:
    source_tier: str
    source_authority: float
    epistemic_confidence: float
    temporal_status: str
    temporal_penalty: float
    is_superseded: bool
    is_stale: bool
    superseded_by: Optional[str] = None
    truth_score: float = 0.0
    trust_verdict: str = TrustVerdict.ADVISORY.value
    raw_lexical_score: float = 0.0
    normalized_relevance: float = 0.0
    rerank_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EvidenceReranker:
    """
    Multi-signal Evidence Reranker enforcing Relevance != Truth.
    """

    def __init__(self, project_root: str = "/workspaces/codespaces-blank"):
        self.project_root = os.path.abspath(project_root)

    def extract_signals(
        self,
        snippet_item: Dict[str, Any],
        section_meta_lines: Optional[List[str]] = None
    ) -> EvidenceSignals:
        """
        Extracts multi-signal evidence metadata (Source Authority, Epistemic Confidence,
        Temporal Validity / Supersession) from snippet, headings, and section metadata.
        """
        snippet_text = snippet_item.get("snippet", "")
        heading = snippet_item.get("heading", "")
        file_path = snippet_item.get("file", "")
        scope = snippet_item.get("scope", "general")
        raw_score = float(snippet_item.get("score", 0.0))

        combined_context = "\n".join(
            ([heading] if heading else []) +
            (section_meta_lines or []) +
            [snippet_text]
        )

        # 1. Temporal Validity & Freshness Check (-0.5 penalty if superseded)
        is_superseded = False
        superseded_by = None
        temporal_status = "ACTIVE"
        temporal_penalty = 0.0

        # Superseded tag patterns: [SUPERSEDED], [SUPERSEDED on YYYY-MM-DD by id:XYZ]
        sup_tag_match = re.search(r"\[SUPERSEDED(?:\s+on\s+([^\s\]]+)\s+by\s+id:([^\]]+))?\]", combined_context, re.IGNORECASE)
        if sup_tag_match:
            is_superseded = True
            if sup_tag_match.group(2):
                superseded_by = sup_tag_match.group(2)

        # Header check: "## Superseded"
        if re.search(r"^##\s*Superseded", combined_context, re.IGNORECASE | re.MULTILINE):
            is_superseded = True

        # Status check: **Status:** SUPERSEDED or Status: SUPERSEDED or status=SUPERSEDED
        status_match = re.search(
            r"(?:\*\*Status:\*\*|Status:|status[:=])\s*([A-Za-z0-9_-]+)",
            combined_context,
            re.IGNORECASE
        )
        if status_match:
            st = status_match.group(1).upper()
            if st in ("SUPERSEDED", "DEPRECATED"):
                is_superseded = True
                temporal_status = st
            elif st == "STALE":
                temporal_status = "STALE"
            elif st in ("ACTIVE", "VERIFIED", "REVIEW"):
                if not is_superseded:
                    temporal_status = st

        # Check bitemporal comment if present
        bitemp_match = re.search(r"<!--\s*bitemporal:(.*?)\s*-->", combined_context)
        if bitemp_match:
            bitemp_str = bitemp_match.group(1)
            if "superseded_by=" in bitemp_str:
                is_superseded = True
                m = re.search(r'superseded_by="?([^"\s]+)"?', bitemp_str)
                if m:
                    superseded_by = m.group(1)

        is_stale = False
        if is_superseded:
            temporal_status = "SUPERSEDED"
            temporal_penalty = SUPERSEDED_PENALTY  # -0.5
        elif temporal_status == "STALE" or "[STALE]" in combined_context.upper() or snippet_item.get("is_stale"):
            is_stale = True
            temporal_status = "STALE"
            temporal_penalty = STALE_PENALTY  # -0.2

        # 2. Source Tier Authority (USER_EXPLICIT: 1.0, REPOSITORY_SOURCE: 0.9, EXECUTED_TEST: 0.95, ...)
        source_tier = None
        source_match = re.search(
            r"(?:\*\*Source:\*\*|Source:|source_tier[:=]|source_authority[:=])\s*([^\s\*,\n]+)",
            combined_context,
            re.IGNORECASE
        )
        if source_match:
            raw_src = source_match.group(1).strip().upper()
            if raw_src in SOURCE_TIER_WEIGHTS:
                source_tier = raw_src
            else:
                # Analyze source identifier
                lower_src = raw_src.lower()
                if "user" in lower_src:
                    source_tier = SourceTier.USER_EXPLICIT.value
                elif "test" in lower_src:
                    source_tier = SourceTier.EXECUTED_TEST.value
                elif "agent_inference" in lower_src or "inference" in lower_src:
                    source_tier = SourceTier.AGENT_INFERENCE.value
                elif "unverified" in lower_src:
                    source_tier = SourceTier.UNVERIFIED.value
                elif "observation" in lower_src:
                    source_tier = SourceTier.AGENT_OBSERVATION.value
                elif any(ext in lower_src for ext in (".py", ".ts", ".js", ".md", "repo", "doc")):
                    source_tier = SourceTier.REPOSITORY_SOURCE.value

        # Infer source tier from path/scope if not explicitly declared in metadata
        if not source_tier:
            norm_path = file_path.replace("\\", "/")
            if "USER.md" in norm_path or scope == "user":
                source_tier = SourceTier.USER_EXPLICIT.value
            elif "tests/" in norm_path or "/test_" in norm_path or "test_" in os.path.basename(file_path):
                source_tier = SourceTier.EXECUTED_TEST.value
            elif any(f in norm_path for f in ("POLICY.md", "rules/", "ARCHITECTURE.md", "DECISIONS.md", "GOTCHAS.md", "ENVIRONMENT.md")):
                source_tier = SourceTier.REPOSITORY_SOURCE.value
            elif "sessions/" in norm_path or "inbox/" in norm_path:
                source_tier = SourceTier.AGENT_OBSERVATION.value
            elif "domains/" in norm_path or "tools/" in norm_path:
                source_tier = SourceTier.REPOSITORY_SOURCE.value
            else:
                source_tier = SourceTier.REPOSITORY_SOURCE.value if ".agents/memory" in norm_path else SourceTier.AGENT_OBSERVATION.value

        source_authority = SOURCE_TIER_WEIGHTS.get(source_tier, 0.7)

        # 3. Epistemic Confidence per Instruction.md Section 17
        epistemic_confidence = None
        conf_match = re.search(
            r"(?:\*\*Confidence:\*\*|Confidence:|confidence[:=])\s*([^\s\*,\n]+)",
            combined_context,
            re.IGNORECASE
        )
        if conf_match:
            raw_conf = conf_match.group(1).strip().upper()
            try:
                num_val = float(raw_conf)
                epistemic_confidence = max(0.0, min(1.0, num_val))
            except ValueError:
                epistemic_confidence = CONFIDENCE_TIER_WEIGHTS.get(raw_conf, None)

        if epistemic_confidence is None:
            # Epistemic confidence aligns with source tier authority unless explicitly declared
            epistemic_confidence = source_authority

        # 4. Normalized Relevance Signal [0.0, 1.0]
        # In hybrid mode, rrf_score is bounded by ~0.016393 (1 / (60 + 1)).
        if "rrf_score" in snippet_item and snippet_item["rrf_score"] is not None:
            normalized_relevance = min(1.0, max(0.0, float(snippet_item["rrf_score"]) / (1.0 / 61.0)))
        else:
            # Lexical scoring gives ~10-100+ points based on token matches, exact phrases, heading matches
            normalized_relevance = min(1.0, max(0.0, raw_score / 100.0))

        # 5. Composite Truth Score per Section 17 & 22
        # Truth separates source authority, epistemic confidence, and temporal validity
        truth_score = (0.6 * source_authority + 0.4 * epistemic_confidence) + temporal_penalty

        # 6. Rerank Score Calculation enforcing Relevance != Truth
        rerank_score, trust_verdict = self.calculate_rerank_score(
            source_tier=source_tier,
            source_authority=source_authority,
            epistemic_confidence=epistemic_confidence,
            temporal_status=temporal_status,
            temporal_penalty=temporal_penalty,
            is_superseded=is_superseded,
            normalized_relevance=normalized_relevance,
            truth_score=truth_score
        )

        return EvidenceSignals(
            source_tier=source_tier,
            source_authority=source_authority,
            epistemic_confidence=epistemic_confidence,
            temporal_status=temporal_status,
            temporal_penalty=temporal_penalty,
            is_superseded=is_superseded,
            is_stale=is_stale,
            superseded_by=superseded_by,
            truth_score=round(truth_score, 4),
            trust_verdict=trust_verdict,
            raw_lexical_score=raw_score,
            normalized_relevance=round(normalized_relevance, 4),
            rerank_score=round(rerank_score, 2)
        )

    def calculate_rerank_score(
        self,
        source_tier: str,
        source_authority: float,
        epistemic_confidence: float,
        temporal_status: str,
        temporal_penalty: float,
        is_superseded: bool,
        normalized_relevance: float,
        truth_score: float
    ) -> Tuple[float, str]:
        """
        Calculates final rerank score enforcing strict disjoint authority tiers:
        - Tier 4 (Authoritative Current Fact): 70.0 - 100.0 [CERTIFY]
        - Tier 3 (Agent Observation):           50.0 - 68.0  [ADVISORY]
        - Tier 2 (Agent Inference):             35.0 - 48.0  [ADVISORY]
        - Tier 1 (Unverified Claim):            15.0 - 28.0  [UNVERIFIED]
        - Tier 0 (Superseded / Invalidated):     0.0 - 15.0  [SUPERSEDED]

        Guarantees:
        An unverified or superseded record (max 28.0 and 15.0) can NEVER
        outrank an authoritative current fact (min 70.0), regardless of lexical relevance!
        """
        if is_superseded or temporal_status == "SUPERSEDED":
            # Superseded Record (Tier 0)
            base = 5.0
            relevance_bonus = normalized_relevance * 8.0
            score = base + relevance_bonus + (temporal_penalty * 4.0)
            return max(0.0, min(15.0, score)), TrustVerdict.SUPERSEDED.value

        if source_authority <= 0.2 or epistemic_confidence <= 0.2 or source_tier == SourceTier.UNVERIFIED.value:
            # Unverified Record (Tier 1)
            base = 18.0
            relevance_bonus = normalized_relevance * 8.0
            conf_bonus = epistemic_confidence * 2.0
            score = base + relevance_bonus + conf_bonus
            return max(15.0, min(28.0, score)), TrustVerdict.UNVERIFIED.value

        if source_authority <= 0.4 or source_tier == SourceTier.AGENT_INFERENCE.value:
            # Agent Inference (Tier 2) - Section 22: "I think this is true" never outranks repository tests
            base = 35.0
            relevance_bonus = normalized_relevance * 9.0
            conf_bonus = epistemic_confidence * 4.0
            score = base + relevance_bonus + conf_bonus
            return max(35.0, min(48.0, score)), TrustVerdict.ADVISORY.value

        if source_authority <= 0.7:
            # Agent Observation (Tier 3)
            base = 52.0
            relevance_bonus = normalized_relevance * 12.0
            conf_bonus = epistemic_confidence * 4.0
            score = base + relevance_bonus + conf_bonus
            return max(50.0, min(68.0, score)), TrustVerdict.ADVISORY.value

        # Tier 4: Authoritative Current Fact (USER_EXPLICIT: 1.0, EXECUTED_TEST: 0.95, REPOSITORY_SOURCE: 0.9)
        base = 72.0
        auth_bonus = (source_authority - 0.85) / 0.15 * 8.0  # 2.67 for 0.90, 5.33 for 0.95, 8.0 for 1.0
        conf_bonus = (epistemic_confidence - 0.7) / 0.3 * 5.0
        rel_bonus = normalized_relevance * 15.0
        stale_pen = temporal_penalty * 10.0  # e.g. -2.0 if stale
        score = base + auth_bonus + conf_bonus + rel_bonus + stale_pen
        return max(70.0, min(100.0, score)), TrustVerdict.CERTIFY.value

    def rerank_results(
        self,
        results: List[Dict[str, Any]],
        apply_reranker: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Reranks a list of candidate memory snippets using multi-signal evidence scoring.
        """
        if not results:
            return []

        for r in results:
            signals = self.extract_signals(
                snippet_item=r,
                section_meta_lines=r.get("section_meta", [])
            )
            r["signals"] = signals.to_dict()
            r["source_tier"] = signals.source_tier
            r["source_authority"] = signals.source_authority
            r["epistemic_confidence"] = signals.epistemic_confidence
            r["temporal_status"] = signals.temporal_status
            r["temporal_penalty"] = signals.temporal_penalty
            r["truth_score"] = signals.truth_score
            r["trust_verdict"] = signals.trust_verdict
            r["is_superseded"] = signals.is_superseded
            r["is_stale"] = signals.is_stale
            r["lexical_score"] = r.get("score", 0.0)
            r["normalized_relevance"] = signals.normalized_relevance
            r["rerank_score"] = signals.rerank_score

            if apply_reranker:
                r["score"] = signals.rerank_score

        if apply_reranker:
            # Sort descending by evidence rerank score, then by lexical score, then line
            results.sort(
                key=lambda x: (x.get("rerank_score", 0.0), x.get("lexical_score", 0.0), -x.get("start_line", 0)),
                reverse=True
            )
        else:
            # Baseline lexical sort
            results.sort(
                key=lambda x: (x.get("lexical_score", x.get("score", 0.0)), -x.get("start_line", 0)),
                reverse=True
            )

        return results
