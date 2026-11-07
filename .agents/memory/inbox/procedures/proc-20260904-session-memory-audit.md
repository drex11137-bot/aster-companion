---
id: proc-20260904-session-memory-audit
title: "Episodic Session Lifecycle & Memory Verification"
domain: memory-governance
type: PROCEDURE
status: CANDIDATE_STAGED
admitted: false
recurrence_count: 2
confidence: 0.85
created_at: 2026-09-04T07:42:32.670132+00:00
source_sessions:
  - 2026-09-01-1546
  - 2026-09-01-1617
tags:
  - memory-governance
  - session-lifecycle
  - distilled-procedure
---

# Candidate Procedure: Episodic Session Lifecycle & Memory Verification

> **Invariant 16 Notice**: This procedure is a generated candidate currently staged in the inbox.
> It remains INERT and is NOT installed into active `.agents/skills/` or `~/.gemini/antigravity-cli/skills/`.

## 1. Summary & Objective
Recurring procedure for validating memory integrity and session lifecycle compliance.

## 2. Provenance & Evidence
- **Discovery Mechanism**: Episodic session sequence clustering (N=2)
- **Confidence Score**: `0.85`
- **Source Sessions**: 2026-09-01-1546, 2026-09-01-1617
- **Distillation Date**: `2026-09-04T07:42:32.670132+00:00`

## 3. Step Breakdown (Section 46 Distinction)
| Step | Distinction Type | Name | Verifiable Command | Working Directory |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **`[INFERRED_STEP]`** | Inspect INDEX.md and Working State | *None (Reasoning/Advisory)* | `/workspaces/codespaces-blank` |
| 2 | **`[VERIFIED_STEP]`** | Run Memory Structure Validation | `python3 scripts/validate_memory.py` | `/workspaces/codespaces-blank` |
| 3 | **`[RECOMMENDED_STEP]`** | Recommend Zero-Secret Gatekeeper Audit | `python3 scripts/secret_scanner.py --dir .agents/memory` | `/workspaces/codespaces-blank` |
| 4 | **`[OPTIONAL_STEP]`** | Optional Memory Compaction | `python3 scripts/compact_memory.py` | `/workspaces/codespaces-blank` |

## 4. Execution Workflow Details

### Step 1: `[INFERRED_STEP]` Inspect INDEX.md and Working State
**Description**: Verify active working state in .agents/memory/CURRENT.md before session start.
- **Working Directory**: `/workspaces/codespaces-blank`

### Step 2: `[VERIFIED_STEP]` Run Memory Structure Validation
**Description**: Execute deterministic memory validator to guarantee structural coherence.
- **Working Directory**: `/workspaces/codespaces-blank`
- **Command**:
```bash
python3 scripts/validate_memory.py
```
- **Verification Criteria**: Exit code 0 and 'VALIDATION PASSED'

### Step 3: `[RECOMMENDED_STEP]` Recommend Zero-Secret Gatekeeper Audit
**Description**: Audit candidate memory entries for zero secrets prior to promotion.
- **Working Directory**: `/workspaces/codespaces-blank`
- **Command**:
```bash
python3 scripts/secret_scanner.py --dir .agents/memory
```
- **Verification Criteria**: Zero secret violations reported

### Step 4: `[OPTIONAL_STEP]` Optional Memory Compaction
**Description**: If CURRENT.md exceeds 30 lines, run compaction routine.
- **Working Directory**: `/workspaces/codespaces-blank`
- **Command**:
```bash
python3 scripts/compact_memory.py
```

## 5. Review & Admission Checklist (Invariant 16)
- [ ] Observed commands verified against authentic environment requirements
- [ ] Inferred steps reviewed for correctness and necessity
- [ ] Recommended steps verified against repository architecture guidelines
- [ ] Zero-secrets scan verified clean
- [ ] Gatekeeper approval obtained prior to promotion to active `.agents/skills/`
