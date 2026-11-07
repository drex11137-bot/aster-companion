# VERIFY MEMORY SYSTEM — Independent Verification & Reproduction Runbook
**Authority:** `instruction.md` Section 120  
**Target Audience:** Autonomous Agents, Reliability Engineers, Independent Verifiers  
**Environment:** Linux x86_64 (Ubuntu 24.04 / Codespaces)  

---

## 1. Overview

This guide enables any independent engineer or incoming autonomous subagent to completely reproduce the verification of the Antigravity 8-Tier Memory Operating System using concrete, runnable CLI commands. 

Every verification step produces deterministic outputs, explicit return codes, and structured logs without reliance on simulated or mock environments.

---

## 2. Step-by-Step Verification Runbook

### Step 1: Run Unified Memory Doctor Diagnostic
Verify all six diagnostic dimensions (Canonical Integrity, Secret Hygiene, Coherence, Vector Index, Ingestion Queue, Telemetry Quality):
```bash
# Run complete diagnostic with formatted CLI summary
tools/bin/agy-memory-doctor

# Or run with structured JSON output for automated pipelines
tools/bin/agy-memory-doctor --json
```
**Expected Outcome:**
- Overall Status: `HEALTHY` (`is_healthy: true`)
- All 6 diagnostic predicates evaluate to `PASS` (scores $\ge 0.95$).

---

### Step 2: Run Full Automated Test Suites
Execute all unit, integration, and lifecycle test suites across the memory subsystem:
```bash
# 1. Run Core Ingestion, Reconciler & Index Queue Test Suites (Wave B)
pytest tests/test_candidate_bus.py \
       tests/test_lifecycle_hooks.py \
       tests/test_memory_compiler.py \
       tests/test_memory_reconciler.py \
       tests/test_memory_index_queue.py -v

# 2. Run Feedback, Learning Loop & Procedural Test Suites (Wave C)
pytest tests/test_memory_feedback.py \
       tests/test_learning_loop.py \
       tests/test_procedural_engine.py -v

# 3. Run Query Router & Scoped Search Suites
pytest scripts/test_query_router.py \
       tests/test_memory_search.py -v
```
**Expected Outcome:**
- All tests pass with exit code 0 (112/112 tests passing).

---

### Step 3: Run Acceptance Matrix Benchmark (A001–A030)
Execute the formal 30-point acceptance matrix directly against the live Milvus Lite database:
```bash
python3 scripts/memory_benchmark.py --acceptance-matrix
```
**Expected Outcome:**
- Total Assertions: 30, Passed: 30, Failed: 0.
- Pass Rate: `100.0%`.
- Results saved to `.agent/memory-audit/verification/evidence/acceptance_matrix_results.json`.

---

### Step 4: Test Derived Index Destruction & Deterministic Rebuild
Verify Invariants 1, 2, and 12 (derived state is disposable and completely rebuildable from Markdown):
```bash
# 1. Inspect existing synchronized chunk count
python3 -c "from scripts.memsearch_backend import MemSearchBackend; print('Before chunks:', len(MemSearchBackend().manifest.get('indexed_files', {})))"

# 2. Force rebuild of the Milvus Lite vector collection from canonical Markdown
python3 scripts/memsearch_backend.py --rebuild

# 3. Confirm all 17 chunks are re-embedded and synchronized
python3 -c "from scripts.memsearch_backend import MemSearchBackend; print('After chunks:', len(MemSearchBackend().manifest.get('indexed_files', {})))"
```
**Expected Outcome:**
- `milvus.db` collection purged and re-populated with 17 canonical chunks. Zero data loss in `.agents/memory/`.

---

### Step 5: Execute Retrieval Probes (Hybrid RRF & Abstention)
Test both semantic generalization and explicit out-of-domain abstention:
```bash
# 1. Semantic Paraphrase Probe (Dense ONNX + Lexical BM25 Hybrid)
python3 scripts/search_memory.py "Gradle daemon memory limit" --scope gotchas --hybrid

# 2. Out-of-Domain Abstention Probe (Invariant 9 & Section 29)
python3 scripts/query_router.py --query "What is the recipe for chocolate cake?"
```
**Expected Outcome:**
- Probe 1 returns `GOTCHA-GRADLE-01` with rank 1 and composite RRF score.
- Probe 2 returns `abstained: true` and message `"No sufficiently trustworthy memory found"` (0 false recalls).

---

### Step 6: Execute Failure & Corruption Probe
Test Invariant 2 and 17 (resilience under corrupted vector databases):
```bash
pytest tests/test_memory_os_adversarial.py -k test_09_direct_milvus_database_file_corruption_recovery -v
```
**Expected Outcome:**
- Substrate detects corrupt database file, marks health as `DEGRADED`, isolates failure, and recovers cleanly from canonical Markdown without corrupting any source documents.

---

### Step 7: Execute Security & Secret Injection Probe
Test PreToolUse gatekeeper, entropy scanning, and Invariant 16 quarantine:
```bash
# 1. Run live secret hygiene audit across all memory files
tools/bin/agy-memory-doctor --check-secrets

# 2. Verify Invariant 16 procedural quarantine
python3 scripts/procedural_engine.py verify-isolation

# 3. Run full adversarial red-team suite (20 attack scenarios)
pytest tests/test_adversarial_attacks.py tests/test_memory_os_adversarial.py -v
```
**Expected Outcome:**
- 0 secrets detected.
- 0 quarantined procedures admitted to skills.
- 24/24 adversarial attack tests pass.

---

## 3. End-to-End Live Lifecycle Demonstration (Section 128)
To replay the full 20-step end-to-end lifecycle demonstration:
```bash
python3 scripts/run_section128_demo.py
```
**Expected Outcome:**
- All 20 steps execute sequentially and output `[STEP XX: PASSED]`.
- Execution summary outputs: `Total Steps: 20 | Passed: 20 | Failed: 0`.
