---
name: memory-promote
description: Rigorously classifies candidate memory items across 9 knowledge types and a 0–5 durability scale, enforces strict evidence thresholds, scans for secrets, performs contradiction detection, and routes validated durable facts to the correct project or global memory tier.
triggers:
  - "/promote-memory"
  - "promote memory"
  - "persist decision"
  - "save gotcha"
  - "promote knowledge"
tags:
  - memory
  - promotion
  - classification
  - durability
  - knowledge
---

# Workspace Skill: Memory Promotion & Classification (`/promote-memory`)

## 1. Purpose & Scope
This skill governs the systematic evaluation, classification, security verification, contradiction detection, and promotion of candidate memory items into durable workspace or global memory tiers. It enforces strict empirical evidence standards, a 0–5 durability scale, and a 9-type classification taxonomy.

## 2. Activation Triggers
Activate this skill when:
- Executing the `/promote-memory` command.
- An architectural decision is finalized (`.agents/memory/DECISIONS.md`).
- A non-obvious bug, trap, or gotcha with a verified workaround is discovered (`.agents/memory/GOTCHAS.md`).
- Reusable domain or tool patterns are established (`~/.gemini/antigravity-cli/memory/domains/` or `tools/`).
- Promoting end-of-session candidate memories to persistent storage.

## 3. Prerequisites & Environment Verification
Verify presence of memory structures and security scanners:
```bash
# Verify directory structure
test -d .agents/memory || mkdir -p .agents/memory
python3 --version
```

## 4. Decision Tree & Workflow Routing
```mermaid
flowchart TD
    Start([Memory Candidate]) --> SecretCheck{Contains Secrets?}
    SecretCheck -- Yes --> Reject[REJECT: Security Violation & Mask]
    SecretCheck -- No --> EvidenceCheck{Verified Evidence?}
    
    EvidenceCheck -- No / Speculative --> Discard01[Score 0-1: DISCARD]
    EvidenceCheck -- Yes --> ScoreScale{Evaluate Durability}
    
    ScoreScale -- "Score 0-1" --> Discard01
    ScoreScale -- "Score 2" --> SessionLog[Score 2: Session Log Only]
    ScoreScale -- "Score 3" --> ProjectMem[Score 3: Project Memory .agents/memory/]
    ScoreScale -- "Score 4" --> DomainToolMem[Score 4: Domain/Tool Memory ~/.gemini/.../domains|tools/]
    ScoreScale -- "Score 5" --> GlobalMem[Score 5: Global Memory ~/.gemini/.../memory/]
    
    ProjectMem --> ContraCheck[Check Contradictions & Superseded]
    DomainToolMem --> ContraCheck
    GlobalMem --> ContraCheck
    
    ContraCheck --> WriteMem[Format Entry & Write to Target File]
    WriteMem --> SyncIndex[Update Relevant INDEX.md]
    SyncIndex --> Done([Complete Promotion])
    Discard01 --> Done
    SessionLog --> Done
    Reject --> Done
```

## 5. Actionable Workflows & Procedures

### Workflow 1: The 9 Knowledge Types Taxonomy
Every candidate item must be classified into exactly one type:
1. `EPHEMERAL`: Transient debug output, calculations -> Discard immediately.
2. `SESSION`: Active task status -> Session log only.
3. `PROJECT`: Repository-specific architecture, patterns -> `.agents/memory/ARCHITECTURE.md`.
4. `DOMAIN`: Reusable tech-domain knowledge (React, K8s, Go) -> `memory/domains/<domain>.md`.
5. `TOOL`: CLI operational quirks, flags -> `memory/tools/<tool>.md`.
6. `GLOBAL`: Universal developer conventions, preferences -> `memory/GENERAL.md`, `USER.md`, `ENVIRONMENT.md`.
7. `DECISION`: Formal architectural choices -> `.agents/memory/DECISIONS.md`.
8. `GOTCHA`: Non-obvious bugs and verified fixes -> `.agents/memory/GOTCHAS.md`.
9. `PROCEDURE`: Repeatable step-by-step playbooks -> `.agents/memory/PROCEDURES.md`.

### Workflow 2: Secret Scanning & Truth Verification
1. **Secret Scan**: Inspect candidate text against credential patterns (API keys, private keys, auth headers).
2. **Truth Criteria**: Candidate must be:
   - Empirically observed and verified in live execution.
   - Or explicitly directed by the user.
   - Free from speculative hedging words ("maybe", "probably", "might be").

### Workflow 3: Contradiction Check & Superseded History
Before appending to a durable memory file:
1. Search target file for related historical assertions.
2. If contradicted by live codebase reality, preserve historical context via `## Superseded`:
```markdown
### Superseded Entry
- **Previous**: [Old Fact / Decision]
- **Current**: [New Fact / Decision]
- **Reason**: [Why the change occurred]
- **Date**: YYYY-MM-DD
```

### Workflow 4: Target Formatting Standards

#### Decision Format (`DECISION` -> `.agents/memory/DECISIONS.md`)
```markdown
## [YYYY-MM-DD] <Title of Decision>
- **Context**: <Problem or requirement necessitating decision>
- **Decision**: <Explicit technical choice made>
- **Rationale**: <Why this choice was made over alternatives>
- **Consequences**: <Impact on architecture or workflows>
- **Status**: Accepted
```

#### Gotcha Format (`GOTCHA` -> `.agents/memory/GOTCHAS.md`)
```markdown
## [YYYY-MM-DD] <Problem / Symptom Name>
- **Context**: <When this error or quirk occurs>
- **Root Cause**: <Verified underlying mechanism>
- **Resolution / Workaround**: <Exact steps or snippet to resolve>
- **Affected Components**: <Versions, tools, or files affected>
```

### Workflow 5: Index Synchronization
Whenever a durable memory file is created or updated, update the corresponding `INDEX.md` with:
- Relative file link
- Scope description
- Last updated date (`YYYY-MM-DD`)

## 6. Verification & Validation Steps
- **Target File Integrity**: Verify formatted block was appended cleanly to the correct markdown file.
- **Index Accuracy**: Confirm `INDEX.md` contains an accurate entry pointing to the modified file.
- **Secret Scanner Clean**: Confirm no credentials leaked into the target file.

## 7. Failure Recovery & Troubleshooting
- **Ambiguous Scope (Project vs Global)**:
  Always default to **Project Memory (Score 3)** to prevent workspace-specific contamination in global tiers.
- **Unverified Bug Workaround**:
  Assign score `2` (Session Only) until the workaround is confirmed by automated tests.
- **Contradiction Detected**:
  Do not silently overwrite previous entries. Always format as `## Superseded` to preserve historical lineage.

## 8. Security Boundaries & Operational Guardrails
- **Zero Secrets**: Absolute prohibition against writing credentials, tokens, or private keys.
- **Authoritative Repo State**: Live code in the repository strictly outranks memory records.
- **User Intent Supremacy**: Explicit user instructions outrank inferred preferences.
