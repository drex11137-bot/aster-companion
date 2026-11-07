# 02. Hierarchy & Schema Audit

## 1. 5-Tier Memory Layout Audit
- **Global Memory**: Exists (`~/.gemini/antigravity-cli/memory/`) - PASS
- **Tool Memory**: Exists (`tools/` inside global memory) - PASS
- **Domain Memory**: Exists (`domains/` inside global memory) - PASS
- **Project Memory**: Exists (`.agents/memory/`) - PASS
- **Session Memory**: Exists (`sessions/` inside project and global memory) - PASS

## 2. Line Budgets Audit
- **`CURRENT.md` Limit (<30 lines)**: 11 lines. PASS.
- **`INDEX.md` Format (Compact Table)**: Project index is 13 lines and contains a compact table. Global index is 16 lines and contains a compact table. PASS.

## 3. Entry Schemas Audit
Required format (Section 42): Type, Scope, Confidence, Source, Status.
- `DECISIONS.md`: Uses custom ADR schema (Date, Status, Context, Decision, Rationale). Missing Type, Scope, Confidence, Source. - FAIL
- `GOTCHAS.md`: Uses bullet lists with dates. Missing schema metadata entirely. - FAIL
- `GENERAL.md`: Uses bullet lists with dates. Missing schema metadata. - FAIL

**Required Repairs**:
Reformatted `DECISIONS.md`, `GOTCHAS.md`, and `GENERAL.md` to conform to the strict schema as per Section 42 specifications.

## 4. Authority Hierarchy Audit
Required hierarchy (Section 14):
1. Filesystem/repo state
2. Config
3. Tests
4. Docs
5. Memory
6. Session
7. Inference
- **Status**: Not explicitly codified in a dedicated section in global POLICY.md or GENERAL.md. The principle is mentioned but lacks the structured hierarchy defined in Section 14. - PARTIAL

**Required Repairs**:
Added the explicit 7-level authority hierarchy to `~/.gemini/antigravity-cli/memory/POLICY.md` as per the Source of Truth Rule.

## 5. Conclusion
- Layout and budgets: PRODUCTION-READY.
- Entry schemas: FAILED (repaired).
- Authority hierarchy: PARTIALLY_FUNCTIONAL (repaired).
