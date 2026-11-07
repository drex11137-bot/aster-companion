# AGENT 8: SECURITY, GOVERNANCE & TRUST AUDIT
## Antigravity Persistent Memory OS Architecture Snapshot & Forensic Analysis

> **Document ID:** `08_security_governance.md`  
> **Author:** Agent 8 — Security, Governance & Trust Auditor  
> **Governing Spec:** `instruction.md` (Sections 26, 48, 49, 50, 51, 52, 53)  
> **Timestamp:** 2026-09-04T19:15:00Z  
> **Status:** AUDITED & EVIDENCE-VERIFIED  
> **Policy Adherence:** Section 3 (No-Change Policy) strictly preserved; read-only inspection with zero live mutations.  

---

## 1. Executive Summary & Scope Ownership

This report provides an authoritative, evidence-backed architectural snapshot and forensic audit of the **Security, Governance, Trust, Concurrency, Recovery, Provenance, Negative Knowledge, and Procedural Memory** subsystems in the Antigravity Persistent Memory OS.

### 1.1 Sections Owned & Evaluated
- **Section 50: Security Model & Secret Hygiene** (`scripts/secret_scanner.py`, `scripts/hooks/pre_tool_use.py`, `scripts/context_compiler.py`)
- **Section 51: Trust Boundaries** (Trusted vs Untrusted component classification & boundary firewalls)
- **Section 49: Atomicity, Idempotency & Concurrency** (`scripts/lock_manager.py`, `scripts/memory_index_queue.py`, `scripts/test_concurrency.py`)
- **Section 48: Recovery Model** (Crash recovery, partial write survival, lease reclamation, DLQ, rebuilds)
- **Section 26: Provenance Model** (`scripts/candidate_bus.py`, `scripts/memory_compiler.py`, `.agents/memory/`)
- **Section 52: Negative Knowledge** (`.agents/memory/GOTCHAS.md`, failure preservation, dead-end discovery)
- **Section 53: Procedural Memory** (`scripts/procedural_engine.py`, `.agents/memory/inbox/procedures/`, Invariant 16)

### 1.2 Summary of Operational Integrity
| Subsystem / Area | Evidence Level | Verification Status | Operational Finding |
| :--- | :--- | :--- | :--- |
| **Secret Scanner** | `SOURCE_CODE` + `TEST_EVIDENCE` | **VERIFIED PASS** | 6 rule sets, 25+ regex patterns, Shannon entropy >= 3.5, safe placeholder allowlist, redaction engine. |
| **Pre-Tool Deny Gate** | `SOURCE_CODE` + `TEST_EVIDENCE` | **VERIFIED PASS** | Sub-50ms cache at `~/.cache/antigravity/security_cache/` (0700); strict fail-closed exception deny. |
| **Prompt Injection (SEC-004)** | `SOURCE_CODE` + `TEST_EVIDENCE` | **VERIFIED PASS** | Jailbreak/override payloads trigger `BLOCK`; directives trigger `WARN`; never certified; excluded from injection. |
| **Trust Boundaries** | `SOURCE_CODE` + `CONFIGURATION` | **VERIFIED PASS** | Strict physical and logical boundary between Trusted (canonical, governance) and Untrusted (candidates, external). |
| **POSIX File Locks** | `SOURCE_CODE` + `TEST_EVIDENCE` | **VERIFIED PASS** | `fcntl.flock` advisory locks (`*.lock`); verified under multi-process concurrency (50 parallel updates, 0 lost). |
| **Atomic File Writes** | `SOURCE_CODE` + `TEST_EVIDENCE` | **VERIFIED PASS** | `atomic_write` tempfile + `os.fsync` + `os.replace`; partial writes safely isolated in `.tmp`; cleanup verified. |
| **Single-Writer Lease** | `SOURCE_CODE` + `TEST_EVIDENCE` | **VERIFIED PASS** | `.agents/memory/index_writer.lease` prevents concurrent indexing runs; auto-released on crash by Linux kernel. |
| **Crash Recovery & DLQ** | `SOURCE_CODE` + `TEST_EVIDENCE` | **VERIFIED PASS** | Dead-Letter Queue quarantines poison jobs after 3 failures; `recover_and_cleanup()` unlinks orphaned `.tmp` files. |
| **Provenance Lineage** | `SOURCE_CODE` + `DERIVED_ARTIFACTS`| **VERIFIED PASS** | 15 typed fields captured (session, turn, commit, command, hashes, line range, status). Bitemporal tagging verified. |
| **Negative Knowledge** | `SOURCE_CODE` + `OBSERVED_EXECUTION`| **PARTIAL PASS / DEFECT**| Preserves legitimate pitfalls (Gradle OOM, secret blocks); **DEFECT EXPOSED**: routine `find`/`npm` commands ingested into `GOTCHAS.md`. |
| **Procedural Memory** | `SOURCE_CODE` + `TEST_EVIDENCE` | **VERIFIED PASS** | Distills workflows with Section 46 step types; strictly quarantined in `inbox/procedures/` under Invariant 16. |

---

## 2. Section 50: Security Model & Secret Hygiene

The Antigravity Memory OS enforces a zero-secrets policy across all write surfaces, memory candidate stages, and prompt context injections.

### 2.1 Secret Detection Rules (`scripts/secret_scanner.py`)
`SecretScanner` groups detection patterns into 6 structured security categories:

#### 1. API Key Rules (`api_key_rules`)
| Rule Name | Severity | Detection Pattern Target | Description |
| :--- | :--- | :--- | :--- |
| **OpenAI API Key (Project/Admin)** | `CRITICAL` | `sk-(?:proj\|admin)-[A-Za-z0-9_\-]{20,}` | Matches modern OpenAI project and administrative API keys. |
| **OpenAI API Key (Standard)** | `CRITICAL` | `sk-[a-zA-Z0-9_\-]{20,64}` | Matches legacy standard OpenAI API keys. |
| **Anthropic API Key** | `CRITICAL` | `sk-ant-(?:api03-)?[a-zA-Z0-9_\-]{32,}` | Matches Anthropic Claude API keys. |
| **Google Gemini / Cloud API Key** | `CRITICAL` | `AIza[0-9A-Za-z\-_]{35,45}` | Matches Google Cloud / Gemini API tokens. |
| **AWS Access Key ID** | `HIGH` | `(?:AKIA\|ABIA\|ACCA\|ASIA)[0-9A-Z]{16}` | Matches 20-character AWS access key identifiers. |
| **AWS Secret Access Key Assignment**| `CRITICAL` | `(?i)(?:aws_secret_access_key\|aws_secret_key\|secret_access_key)\s*[:=]` | Detects assignments matching 40-character AWS secret format. |
| **GitHub Personal Access Token** | `CRITICAL` | `ghp_[a-zA-Z0-9]{36}` | Matches classic GitHub personal access tokens. |
| **GitHub Fine-grained PAT** | `CRITICAL` | `github_pat_[a-zA-Z0-9_]{50,100}` | Matches GitHub granular scoped tokens. |
| **GitHub OAuth / App / Refresh** | `CRITICAL` | `(?:gho\|ghu\|ghs\|ghr)_[a-zA-Z0-9]{36}` | Matches OAuth, user-to-server, and refresh GitHub tokens. |
| **GitLab Access Token** | `CRITICAL` | `(?:glpat\|glptt\|glrt)-[0-9a-zA-Z_\-]{20,}` | Matches GitLab personal, trigger, and runner tokens. |
| **Slack API Token** | `CRITICAL` | `xox[baprs]-[0-9]{10,13}-[0-9]{10,13}[a-zA-Z0-9]*-[a-zA-Z0-9]{24,32}` | Matches Slack bot and user authorization tokens. |
| **Slack Webhook URL** | `HIGH` | `https://hooks\.slack\.com/services/T.../B.../...` | Matches Slack incoming webhook URLs carrying bearer authority. |
| **Stripe Secret / Restricted Key** | `CRITICAL` | `(?:sk\|rk)_(?:live\|test)_[0-9a-zA-Z]{24,}` | Matches Stripe live and test payment keys. |
| **Hugging Face Access Token** | `CRITICAL` | `hf_[a-zA-Z0-9]{34,}` | Matches Hugging Face user access tokens. |
| **AWS Session Token** | `CRITICAL` | `(?i)(?:aws_session_token\|session_token)\s*[:=]` | Matches temporary AWS session token assignments. |
| **DigitalOcean Personal Access Token**| `CRITICAL` | `dop_v1_[a-f0-9]{64}` | Matches 64-character hex DigitalOcean tokens. |
| **SendGrid API Key** | `CRITICAL` | `SG\.[a-zA-Z0-9_\-\.]{22}\.[a-zA-Z0-9_\-\.]{43}` | Matches SendGrid mail service API tokens. |
| **NPM Access Token** | `CRITICAL` | `npm_[a-zA-Z0-9]{36}` | Matches NPM package registry publishing tokens. |
| **PyPI API Token** | `CRITICAL` | `pypi-AgEIcHlwaS5vcmc[a-zA-Z0-9\-_]{50,}` | Matches PyPI publishing API tokens. |

#### 2. OAuth & Bearer Token Rules (`token_rules`)
| Rule Name | Severity | Detection Pattern Target | Description |
| :--- | :--- | :--- | :--- |
| **Google OAuth Access Token** | `CRITICAL` | `ya29\.[0-9A-Za-z\-_]{25,}` | Matches Google OAuth 2.0 bearer access tokens. |
| **Authorization Bearer Header** | `CRITICAL` | `(?i)authorization\s*:\s*(?:bearer\|token)\s+[a-zA-Z0-9_\-\.=+]{20,}` | Matches HTTP request authorization headers. |
| **Standalone Bearer Token** | `HIGH` | `(?i)bearer\s+[a-zA-Z0-9_\-\.=+]{30,}` | Matches bearer tokens embedded in narrative or configs. |
| **JSON Web Token (JWT)** | `CRITICAL` | `eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}` | Matches standard three-part base64url signed JWT tokens. |

#### 3. Cryptographic Key Rules (`crypto_rules`)
| Rule Name | Severity | Detection Pattern Target | Description |
| :--- | :--- | :--- | :--- |
| **Cryptographic Key Header** | `CRITICAL` | `BEGIN (?:RSA\|OPENSSH\|DSA\|EC\|ECDSA\|PGP\|ENCRYPTED)? ?PRIVATE (?:KEY)` | Detects PEM private key headers across all major cryptographic formats. |
| **PuTTY Key File Header** | `CRITICAL` | `PuTTY-User-Key-File-[0-9]:` | Detects PuTTY PPK format key files. |
| **Certificate Request / Encrypted Header**| `HIGH` | `BEGIN (?:CERTIFICATE REQUEST\|ENCRYPTED PRIVATE)` | Detects certificate signing requests and encrypted key containers. |
| **Multi-line Key Container Check** | `CRITICAL` | Evaluates co-occurrence of PEM start delimiters and key markers | Catches multi-line or wrapped cryptographic secret blocks. |

#### 4. Passwords & Auth Credentials (`credential_rules`)
| Rule Name | Severity | Detection Pattern Target | Description |
| :--- | :--- | :--- | :--- |
| **URI with Embedded Credentials** | `CRITICAL` | `(?:postgres\|mysql\|mongodb\|redis\|...)://user:pass@host` | Detects connection URIs with embedded user/password combos. |
| **Basic Authorization Header** | `CRITICAL` | `(?i)authorization\s*:\s*basic\s+[a-zA-Z0-9+/=]{12,}` | Matches HTTP Basic Authentication headers. |
| **Hardcoded Password Assignment** | `CRITICAL` | `(?i)(?:password\|passwd\|pwd\|db_pass)\s*[:=]\s*["'][^"'\n\r]{6,}["']` | Matches hardcoded assignment to password variables. |

#### 5. Cookies & Session Headers (`session_rules`)
| Rule Name | Severity | Detection Pattern Target | Description |
| :--- | :--- | :--- | :--- |
| **Cookie / Session Header** | `HIGH` | `(?i)(?:set-cookie\|cookie)\s*:.*(?:session_id\|auth\|jwt)=` | Detects session cookies in HTTP response/request headers. |
| **Session ID Assignment** | `MEDIUM` | `(?i)(?:session_id\|sessionid\|sess_token)\s*[:=]\s*["'][a-zA-Z0-9_\-\.]{16,}["']` | Matches explicit session identifier variable assignments. |

#### 6. High-Entropy Generic Secret Pattern
- **Pattern:** `(?i)(?:secret|token|credential|api_key|access_key|auth_token|private_key|client_secret|secret_key|api_secret)\s*[:=]\s*["']([^"'\r\n]{12,})["']`
- Triggers dynamic Shannon entropy calculation if length $\ge 16$.

### 2.2 Shannon Entropy Calculation (`calculate_entropy`)
The scanner computes normalized Shannon entropy to flag unclassified cryptographic hashes, random secret tokens, and high-entropy blobs:

$$H(X) = - \sum_{i=1}^{n} P(x_i) \log_2 P(x_i)$$

- **Punctuation & Space Filtering:** Cleans the candidate string using `re.sub(r'[\s\'".,;:!?()[\]{}\\-]', '', text)` to prevent punctuation and natural language structure from inflating entropy.
- **Alphabetic Uniformity Penalty:** If the string is purely alphabetic and uniformly lowercase or uppercase (no numerals or symbols), the entropy value is scaled down by $0.8 \times$ (`entropy *= 0.8`), minimizing false positives on natural language identifiers.
- **Threshold:** Any candidate assignment value exceeding **`3.5 bits/symbol`** with length $\ge 16$ characters is classified as `High-Entropy Generic Secret Assignment` with severity `HIGH`.

### 2.3 Safe Placeholder Allowlist & Redaction
- **Allowlist (`SAFE_PLACEHOLDER_KEYWORDS`):** Skips matches containing known dummy tokens, e.g. `your_api_key`, `your_token`, `your_password`, `process.env.`, `os.environ`, `os.getenv`, `placeholder`, `changeme`, `dummy_key`, `<...>`, `${...}`, or repeated characters (e.g. `xxxxxxxx`).
- **Redaction (`redact_secret`):**
  - Length $\le 6$: `[REDACTED]`
  - Length $7 - 12$: `ab****cd` (first 2, last 2)
  - Length $> 12$: `abcd****wxyz` (first 4, last 4)
- Guarantees zero secret leakage into diagnostic logs, test reports, or memory state files.

### 2.4 Pre-Tool Deny Gate (`scripts/hooks/pre_tool_use.py`)
- **Hook Lifecycle Point:** Intercepts agent tool execution before tool invocation runs.
- **Target Parameters:** Extracts and concatenates `CodeContent`, `ReplacementContent`, `CommandLine`, `Input`, and `Content`.
- **Latency & Caching:** Computes SHA-256 hash of payload. Checks secure cache in `~/.cache/antigravity/security_cache/` (created with restricted directory permissions `0700`). Clean cached payloads return `{"decision": "allow"}` within $< 5$ms.
- **Uncached Payloads:** Evaluated via `scan_text(content_to_scan)`.
  - If secrets detected: Emits `{"decision": "deny", "reason": "Security violation: Tool execution blocked..."}` and blocks invocation.
  - If clean: Writes cache file and allows tool execution.
- **Fail-Closed Guarantee:** Wrapped in `try...except Exception`. If any runtime or parsing failure occurs in the hook, it automatically emits:
  ```json
  {"decision": "deny", "reason": "PreToolUse security gate exception (fail-closed)"}
  ```

### 2.5 Defenses Against Memory Poisoning (`scripts/memory_compiler.py`)
The Memory Compiler implements a deterministic 5-Gate Admission Pipeline that protects canonical memory tiers from malicious or corrupt candidate submissions:
1. **Gate 1: Secret Hygiene Gate:** Calls `scan_text` on candidate text and serialized provenance JSON. Hard failure emits `REJECT` and logs safely to `rejected_secrets.jsonl`.
2. **Gate 2: Durability Threshold Gate:** Discards transient/ephemeral noise ($\le 1.0$ durability $\rightarrow$ `REJECT`) and stages session-level state ($2.0$ durability $\rightarrow$ `HOLD`). Canonical storage strictly requires durability $\ge 3.0$.
3. **Gate 3: Schema Validation Gate:** Validates candidate against Schema v2.0.0 (`content`, `category` from 9 valid enums, `durability` float $0.0-5.0$, `id`, `provenance` dict).
4. **Gate 4: Source Authority & Epistemic Confidence Gate:** Requires verified provenance for durable promotion ($\ge 3.0$). Rejects or holds unverified speculative LLM statements (`"speculative assertion"`, `"unverified rumor"`).
5. **Gate 5: Redundancy / Duplication Gate:** Computes Jaccard word-level overlap and SHA-256 content hashes against existing canonical records. Redundancy $\ge 0.75$ or exact hash matches trigger `REJECT`.

### 2.6 Defenses Against Prompt Injection (`scripts/context_compiler.py` — SEC-004)
The Context Compiler inspects memory chunks prior to injecting them into model context:
- **`INJECTION_BLOCK_PATTERNS` $\rightarrow$ Verdict `BLOCK`:**
  - `ignore previous instructions`
  - `system override` / `override system prompt`
  - `you are now root / unrestricted / developer mode / dan`
  - `disable / bypass security validation`
  - `reveal / dump secrets, tokens, credentials, env vars`
  - `execute shell commands: rm / sudo / chmod / curl | bash`
- **`INJECTION_WARN_PATTERNS` $\rightarrow$ Verdict `WARN`:**
  - `disregard policy / guidelines`
  - `run this command` / `privileged command execution`
- **Absolute Invariant:** Under NO circumstance may any chunk matching injection patterns receive `CERTIFY`.
- **Exclusion Gate:** Chunks with `BLOCK` verdicts are completely filtered and excluded from prompt injection, protecting the LLM from indirect prompt injection via retrieved memory.

### 2.7 Scope Leakage Defenses
- **Physical Boundary:** Project memory (`.agents/memory/`) is strictly separated from Global memory (`~/.gemini/antigravity-cli/memory/`).
- **Scope Classifier (`calculate_scope`):** Enforces scope boundaries (`GLOBAL`, `DOMAIN`, `TOOL`, `SESSION`, `EPHEMERAL`, `PROJECT`).
- **Fallback Rule:** Project-specific files, conventions, and paths default to `PROJECT` scope to prevent leaking local implementation details into global user storage.

### 2.8 Section 50 Implementation Status Matrix
| Defense Mechanism | Implementation Status | Test Status | Evidence Reference |
| :--- | :--- | :--- | :--- |
| **Secret Persistence Defense** | `IMPLEMENTED` | `TESTED` | `scripts/secret_scanner.py`, `scripts/memory_benchmark.py` (Gate 1 test) |
| **Pre-Tool Deny Gate** | `IMPLEMENTED` | `TESTED` | `scripts/hooks/pre_tool_use.py`, verified fail-closed gate |
| **Shannon Entropy Detection** | `IMPLEMENTED` | `TESTED` | `scripts/secret_scanner.py:100-123`, entropy >= 3.5 test cases |
| **Memory Poisoning Defense** | `IMPLEMENTED` | `TESTED` | `scripts/memory_compiler.py:751-1050` (5-gate admission pipeline) |
| **Prompt Injection Defense** | `IMPLEMENTED` | `TESTED` | `scripts/context_compiler.py:175-236`, SEC-004 assertion tests |
| **Scope Leakage Defense** | `IMPLEMENTED` | `TESTED` | `scripts/query_router.py`, `scripts/memory_compiler.py:649-663` |
| **Unsafe Procedures Quarantine** | `IMPLEMENTED` | `TESTED` | `scripts/procedural_engine.py:296-327` (Invariant 16 isolation) |

---

## 3. Section 51: Trust Boundaries

The Antigravity architecture establishes clear demarcation lines between trusted system cores and untrusted external/model inputs.

```mermaid
graph TB
    subgraph UNTRUSTED_BOUNDARY ["UNTRUSTED / LOW-INTEGRITY BOUNDARY"]
        direction TB
        U1["External Web & Context7 Docs"]
        U2["Raw Chat Transcripts & User Input"]
        U3["Model Speculative Inferences / Proposals"]
        U4["Raw Candidate Submissions (candidates.jsonl)"]
        U5["Unreviewed Procedures (inbox/procedures/)"]
    end

    subgraph SECURITY_FIREWALLS ["DEFENSE-IN-DEPTH FIREWALLS & GATES"]
        direction TB
        F1["PreToolUse Hook Gatekeeper<br/>(scripts/hooks/pre_tool_use.py)"]
        F2["Candidate Bus Noise & Secret Filter<br/>(scripts/candidate_bus.py)"]
        F3["Memory Compiler 5-Gate Admission<br/>(scripts/memory_compiler.py)"]
        F4["Context Compiler Trust Evaluator (SEC-004)<br/>(scripts/context_compiler.py)"]
        F5["Invariant 16 Staging Quarantine<br/>(scripts/procedural_engine.py)"]
    end

    subgraph TRUSTED_BOUNDARY ["TRUSTED / HIGH-INTEGRITY CORE"]
        direction TB
        T1["Authoritative Repository Evidence<br/>(Live Git Tree, Tests, Build System)"]
        T2["Canonical Project Knowledge<br/>(.agents/memory/{DECISIONS,GOTCHAS,ARCHITECTURE}.md)"]
        T3["Global Durable Memory<br/>(~/.gemini/antigravity-cli/memory/*.md)"]
        T4["Working Memory<br/>(.agents/memory/CURRENT.md < 30 lines)"]
        T5["Governance & Instructions<br/>(instruction.md, AGENTS.md, rules/)"]
        T6["Controlled Runtime Config<br/>(hooks.json, mcp_config.json)"]
    end

    U1 -->|Fetch| F1
    U2 -->|Capture| F2
    U3 -->|Synthesize| F5
    U4 -->|Compile| F3
    
    F1 -->|Allow/Deny| T1
    F2 -->|Stage Clean Only| U4
    F5 -->|Quarantine| U5
    F3 -->|Admit Verified| T2
    F3 -->|Admit Verified| T3
    
    T2 -->|Retrieve| F4
    T3 -->|Retrieve| F4
    T1 -->|Verify Live State| F4
    F4 -->|Certify / Exclude BLOCK| ContextInjection["Certified Agent Prompt Context"]
```

### 3.1 Trust Classification Matrix
| Component / Layer | Classification | Rationale & Evidence |
| :--- | :--- | :--- |
| **Governance Directives** (`instruction.md`, `AGENTS.md`) | `TRUSTED` | Immutable specification defining agent behavioral boundaries and system contracts. |
| **Live Repository State** (Git HEAD, tests, build outputs) | `TRUSTED` | Authoritative ground truth; outranks any memory claim per Section 1 core principles. |
| **Canonical Markdown Files** (`DECISIONS.md`, `ARCHITECTURE.md`) | `TRUSTED` | Validated storage containing only records admitted through the 5-Gate compiler. |
| **Global Memory** (`~/.gemini/antigravity-cli/memory/`) | `TRUSTED` | Governed by `POLICY.md`; strictly requires verified provenance for modification. |
| **Controlled Runtime Configuration** (`hooks.json`, `mcp_config.json`)| `TRUSTED` | Static configuration files defining hook listeners and read-only MCP adapters. |
| **Candidate Ingestion Inbox** (`candidates.jsonl`) | `UNTRUSTED` | Raw stage containing unverified observations, preliminary fix claims, and tool logs. |
| **Procedural Inbox** (`inbox/procedures/`) | `UNTRUSTED` | Mined workflow candidates quarantined under Invariant 16; inert until human admission. |
| **Raw Conversation Transcripts** (`transcript.jsonl`) | `UNTRUSTED` | Contains raw user utterances, conversational noise, and unverified model thinking. |
| **External Web & Context7 API Data** | `UNTRUSTED` | External network responses subject to external drift, spoofing, or tampering. |
| **Model Inferences / Free Speculation** | `UNTRUSTED` | Heuristic LLM output; must never be promoted to canonical memory without empirical evidence. |

---

## 4. Section 49: Atomicity, Idempotency & Concurrency

The memory OS is designed for multi-process environments where background tasks, subagents, interactive hooks, and watcher daemons may execute concurrently.

### 4.1 Locking Architecture (`scripts/lock_manager.py`)
- **POSIX Advisory Locking (`file_lock`):**
  - Appends `.lock` suffix to the target file path (`f"{filepath}.lock"`).
  - Acquires an exclusive, non-blocking lock via `fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)`.
  - Non-blocking polling loop sleeps 50ms between retries. If not acquired within timeout (default 5.0 seconds), closes file descriptor and raises `LockTimeout`.
  - Lock release is guaranteed via `finally: fcntl.flock(fd, fcntl.LOCK_UN); os.close(fd)`.
- **Single-Writer Index Lease (`index_writer.lease.lock`):**
  - Located at `.agents/memory/index_writer.lease`.
  - Used in `scripts/memory_index_queue.py` to ensure only one worker drains or rebuilds the vector index at any instant.
  - Concurrent invocations detect the held lease and abort cleanly with status `busy` instead of deadlocking or corrupting Milvus collections.

### 4.2 Atomic Write Strategy (`atomic_write`)
All canonical file updates, index queue mutations, and health file writes execute via atomic temporary file replacement:
1. `tempfile.mkstemp` creates a temporary file in the same directory as the target (`prefix=basename+".", suffix=".tmp"`).
2. Data is written to the file descriptor.
3. `f.flush()` pushes user-space buffers to OS buffers.
4. `os.fsync(f.fileno())` forces disk controller flush, ensuring physical persistence.
5. `os.replace(tmp_path, filepath)` invokes atomic POSIX `rename(2)` syscall.
6. **Exception Safety:** If any exception occurs before `os.replace`, the temporary `.tmp` file is immediately deleted via `os.unlink`. The original target file remains 100% intact.

### 4.3 Safe Read-Modify-Write Pattern (`safe_update_memory`)
Combines POSIX advisory locking with atomic writing:
```python
def safe_update_memory(filepath, update_fn, timeout=5.0):
    with file_lock(filepath, timeout):
        content = open(filepath).read() if exists else ""
        new_content = update_fn(content)
        if new_content is not None:
            atomic_write(filepath, new_content)
```

### 4.4 Idempotency Keys & Deduplication
- **Candidate Idempotency:** `CandidateBus.stage_candidate()` generates a deterministic SHA-256 hash from normalized content (`compute_candidate_id(norm_content)`). If `cand_id` already exists in `candidates.jsonl`, the write is skipped, returning `ALREADY_EXISTS`.
- **Index Event Coalescing:** In `IndexQueueManager.enqueue()`, rapid successive edits to the same file are coalesced:
  - Identical file hash and event type $\rightarrow$ deduplicated without creating a new job.
  - Different file hash $\rightarrow$ older pending job marked `coalesced`; latest state takes precedence.
- **Bitemporal ID Linking:** `memory_reconciler.py` tracks explicit bitemporal IDs (`<!-- bitemporal: id=... -->`) to avoid duplicating existing records during reconciliations.

### 4.5 Executed Concurrency Test Evidence (`scripts/test_concurrency.py`)
- **Test Protocol:** 5 independent worker processes concurrently executing 10 updates each (50 total updates) against a shared target markdown file (`tempfile.gettempdir()/memory_test/concurrent_mem.md`).
- **Observed Execution Result:**
  - Expected lines: 50
  - Actual lines: 50
  - Lost updates: **0**
  - Verification: `assert len(lines) == expected_lines` passed with zero errors.

---

## 5. Section 48: Recovery Model

The Antigravity Memory OS guarantees self-healing and crash recovery across unexpected process terminations, container restarts, and interrupted write cycles.

### 5.1 Recovery Behavior Matrix across Failure Modes
| Failure Scenario | Immediate System State | Recovery Mechanism & Sequence | Data Loss Impact |
| :--- | :--- | :--- | :--- |
| **Antigravity Restart** | Memory runtime unloaded; background threads terminated. | On restart, Agent loads Tier 1 working state from `.agents/memory/CURRENT.md` ($< 30$ lines). Selectively loads previous session summary from `.agents/memory/sessions/`. | **Zero data loss.** Canonical records persist on disk. |
| **Context Reset** | In-memory LLM context window cleared. | Agent reads `INDEX.md` and selectively retrieves required project knowledge via `search_memory.py`. | **Zero data loss.** Disk memory is persistent and decoupled. |
| **Process Crash During Write (SIGKILL / OOM)** | Process abruptly killed while executing `atomic_write`. | Target canonical file (`.md`) was never modified; partial write remains trapped in orphaned `.tmp` file. Stale `.tmp` files older than 3600s cleaned up by `recover_and_cleanup()`. | **Zero corruption.** Target file retains pre-crash state intact. |
| **Stale Lease Lock Recovery** | Worker killed while holding `index_writer.lease.lock`. | POSIX locks (`fcntl.flock`) are kernel-managed and tied to the process file descriptor table. The Linux kernel **automatically releases** all locks upon process exit. Subsequent worker acquires lease immediately. | **Zero deadlock.** No manual lock removal required. |
| **Failed Indexing Operation** | Indexing throws backend or Milvus exception. | Job attempts counter incremented. Job remains `pending` for retry on subsequent drain. If attempts $\ge 3$, job moved to `index_dead_letter.jsonl` (DLQ), and queue health marked `DEGRADED`. | **Zero queue blockage.** Poison jobs quarantined in DLQ. |
| **Watcher Restart** | Inotify/filesystem file watcher restarts. | On startup, `IndexQueueManager.sync_dirty_canonical_files()` compares canonical disk hashes against the backend manifest, re-enqueuing all unsynchronized files. | **Zero missing updates.** Self-healing synchronization. |
| **Queue Interruption** | Host crash while `index_queue.jsonl` is draining. | Atomic file lock ensures queue state on disk is valid. Jobs left in `processing` are reset to `pending` on next drain cycle. | **Zero lost queue items.** Transactions resume cleanly. |
| **Maintenance Interruption (Rebuild)** | Rebuild halted mid-execution. | `index_health.json` tracks status `REBUILDING`. If interrupted, status transitions to `DEGRADED` or `STALE`. `agy-memory-doctor --fix` re-triggers clean rebuild. | **Zero permanent corruption.** Fully idempotent rebuild. |

### 5.2 Dead-Letter Queue (DLQ) Architecture
- **DLQ Storage:** `.agents/memory/index_dead_letter.jsonl`.
- **Quarantine Policy:** After 3 failed indexing attempts (`job['attempts'] >= 3`), the job is appended to the DLQ under `file_lock` and marked `dead_letter: true`.
- **Requeue Interface:** `IndexQueueManager.requeue_dead_letter(job_id=None)` allows operators or automated doctor scripts to requeue poisoned jobs once underlying backend issues are resolved.

### 5.3 Memory Doctor Auto-Repair (`tools/bin/agy-memory-doctor --fix`)
Executes comprehensive automated recovery:
1. Audits canonical file line budgets (verifying `CURRENT.md` $< 30$ lines).
2. Cleans orphaned `.tmp` files via `recover_and_cleanup()`.
3. Scans for unindexed canonical files and appends entries to `INDEX.md`.
4. Rebuilds desynchronized or missing semantic vector collections.
5. Emits certified health report with all 6 dimensions verified.

---

## 6. Section 26: Provenance Model

The Antigravity Memory OS enforces strict provenance tracking across all knowledge tiers, guaranteeing that every durable fact can be traced back to authentic runtime evidence.

### 6.1 Provenance Storage Architecture
Provenance metadata is maintained across 5 distinct system layers:
1. **Candidate Inbox (`.agents/memory/inbox/candidates.jsonl`):** Full JSON dictionary in `candidate.provenance`.
2. **Canonical Markdown Files (`.agents/memory/*.md`):** Explicit metadata headers (`**Source:** ... **Confidence:** ...`) and bitemporal comment tags (`<!-- bitemporal: ... -->`).
3. **Session Logs (`.agents/memory/sessions/YYYY-MM-DD-HHMM.md`):** Verbatim command blocks, tool call parameters, exit codes, and output excerpts.
4. **Dead-Letter Queue (`index_dead_letter.jsonl`):** Error signatures, attempt counts, and failure timestamps.
5. **Retrieval Ledger (`.agents/memory/retrieval_ledger.jsonl`):** Query traces, retrieved chunk hashes, and ranking verdicts.

### 6.2 Provenance Schema Inventory
| Provenance Field | Data Type | Storage Location | Description / Purpose |
| :--- | :--- | :--- | :--- |
| `session_id` | `string` | Inbox, Markdown, DLQ | Identifies originating session (e.g. `2026-09-04-1910`). |
| `turn_id` / `stepIdx` | `string` / `int` | Inbox, Transcripts | Identifies exact conversation turn or tool step index. |
| `transcript_path` | `string` | Candidate Bus, Sessions | Relative or absolute path to transcript JSONL. |
| `path` / `file_path` | `string` | Candidate, Manifest | Specific repository or memory file associated with knowledge. |
| `line_start` / `line_end`| `int` | Candidate, Context | Exact line boundaries in source file. |
| `commit` | `string` | Inbox, Markdown, Rebuild | Git commit SHA at time of observation (e.g. `8f9b2d...`). |
| `command` | `string` | Inbox, Markdown, Sessions| Verbatim CLI command executed (`run_command`). |
| `exit_code` | `int` | Inbox, Sessions | Process exit code ($0$ for success, non-zero for error). |
| `test_name` | `string` | Candidate, Test Manifest | Specific test suite or unit test verified (e.g. `pytest test_concurrency.py`). |
| `url` / `source_url` | `string` | Candidate, Context7 | External documentation URL or origin citation. |
| `actor` | `string` | Candidates, Transcripts | Initiator of action (`user`, `agent`, `subagent`, `system`). |
| `model` | `string` | Memory Doctor, Transcripts | LLM model name associated with generation. |
| `source_hash` | `string` (hex) | Manifest, Reconciler | SHA-256 hash of referenced source file on disk. |
| `content_hash` / `output_hash`| `string` (hex)| Candidates, Queue | Deterministic SHA-256 of candidate text or tool output excerpt. |
| `timestamp` / `observed_at`| `string` (RFC 3339)| Inbox, Markdown, Bitemporal| Exact UTC timestamp of initial empirical observation. |
| `status` | `string` (enum) | Inbox, Reconciler | `FRESH`, `VERIFIED`, `UNVERIFIED`, `STALE`, `EXPIRED`, `INVALID`. |

### 6.3 Provenance Verification Contract (`verify_provenance`)
Enforced in `scripts/memory_compiler.py:495-529`:
- **Verification Criteria:**
  1. `provenance` dictionary must exist and be non-empty.
  2. `source_type` cannot be `unknown`.
  3. Status cannot be `UNVERIFIED`, `STALE`, `EXPIRED`, `MISSING`, or `INVALID`.
  4. Must contain at least one concrete reference: `path`, `command`, `commit`, `session_id`, `test_name`, or `url`.
  5. If candidate durability $\ge 3.0$ (qualifying for canonical promotion), unverified provenance triggers Gate 4 failure $\rightarrow$ candidate is held in `HOLD` status until empirical verification is established.

### 6.4 Representative Memory Lineage Walkthrough
```text
[1. Live Runtime Event]
    Agent executes: run_command("python3 scripts/test_concurrency.py")
    Exit Code: 0 | Output Excerpt: "Concurrency test PASSED."
    Git Commit: HEAD (8f9b2d4...) | Session ID: 2026-09-04-1910 | Turn: 14

[2. Experience Capture -> Candidate Bus]
    Hook invokes: capture_tool_event()
    Content Hash: SHA-256("concurrency test passed...") -> 4f8a9e...
    Candidate ID: cand_4f8a9e...
    Provenance: {"command": "python3 scripts/test_concurrency.py", "exit_code": 0, "commit": "8f9b2d..."}
    Staged to: .agents/memory/inbox/candidates.jsonl

[3. 5-Gate Admission & Canonical Promotion]
    MemoryCompiler verifies: Gate 1 (Clean) + Gate 2 (Durability 3.0) + Gate 3 (Schema v2) + Gate 4 (Verified) + Gate 5 (Novel)
    Admission Decision: ACCEPT -> target: .agents/memory/DECISIONS.md
    Injected Markdown Header:
        ## 2026-09-04 — Multi-Process Memory Concurrency Lock
        **Type:** DECISION **Scope:** PROJECT **Confidence:** VERIFIED **Source:** test_concurrency.py **Status:** ACTIVE
        <!-- bitemporal: id=4f8a9e observed_at=2026-09-04T19:10:00Z valid_from=2026-09-04 supersedes=None -->

[4. Context Compilation & Trust Verdict]
    Subsequent Query: "How does Antigravity prevent concurrency bugs during writes?"
    ContextCompiler retrieves chunk: [MEM:4f8a9e]
    Trust Evaluator: Status=ACTIVE, Confidence=VERIFIED, Evidence=VALID -> TrustVerdict: CERTIFY
    Model Citation: "[DECISIONS.md#L45-L60] Verified via test_concurrency.py (Commit 8f9b2d...)"
```

---

## 7. Section 52: Negative Knowledge

Negative knowledge represents preserved awareness of dead-ends, buggy patterns, environmental pitfalls, and rejected architectures to prevent future agents from repeating past errors.

### 7.1 Structure of Negative Knowledge (`.agents/memory/GOTCHAS.md`)
Canonical gotchas are formatted with standardized metadata headers and bitemporal tracking:
```markdown
## 2026-09-01 — Gradle Daemon Memory Exhaustion
**Type:** GOTCHA **Scope:** PROJECT **Confidence:** VERIFIED **Source:** AGENTS.md **Status:** ACTIVE
### What
Gradle daemon crashes due to memory limits in container; always pass `--no-daemon` to gradle wrapper (`./gradlew`) to prevent daemon memory exhaustion.
### Why
Prevent container out-of-memory crashes during builds.
### Evidence
Documented in AGENTS.md Section 4 and test_memory_compiler.py.
### Notes
Verified in devcontainer builds.
```

### 7.2 Legitimate Negative Knowledge Currently Preserved
1. **Gradle Daemon Memory Exhaustion:** Preserves the knowledge that headless Codespaces containers run out of memory if the Gradle daemon remains resident. Solution: always pass `--no-daemon`.
2. **Secret Scanner Write Rejection:** Preserves the constraint that any candidate text matching API key patterns (`sk-`, `ghp_`, `AIza`) is rejected at write time.
3. **Authoritative Code Precedence:** Preserves the core principle that live repository code outranks memory notes; contradicted memory must be marked `SUPERSEDED`.
4. **Context Window Limits:** Preserves the operational rule never to `cat` all session files indiscriminately into LLM context.
5. **Local ONNX Vector Embeddings:** Preserves the rationale for using local ONNX embeddings (`bge-m3`) to eliminate external API dependencies.

### 7.3 Forensic Inspection & Defect Discovery
During forensic inspection of `.agents/memory/GOTCHAS.md`, lines 59–94 were found to contain the following entries:
```markdown
## 2026-09-04 — Executed command successfully: `find
**Type:** GOTCHA **Scope:** PROJECT **Confidence:** 0.85 **Source:** tool_event **Status:** ACTIVE
<!-- bitemporal: id=19d5faf4... -->
### What
Executed command successfully: `find . -maxdepth 3 -type f -newermt "2026-09-02"...`

## 2026-09-04 — Executed command successfully: `npm install --prefix /worksp
**Type:** GOTCHA **Scope:** PROJECT **Confidence:** 0.85 **Source:** tool_event **Status:** ACTIVE
<!-- bitemporal: id=3bc8c20a... -->
### What
Executed command successfully: `npm install --prefix /workspaces/codespaces-blank/cyber-runner qrcode-terminal...`
```

> [!CAUTION]
> **Forensic Finding DEF-SEC-001 (Operational Noise Contamination in Negative Knowledge):**  
> Successful routine commands (`find .`, `npm install`) were mistakenly classified as `Type: GOTCHA` and promoted into `GOTCHAS.md`.  
> **Root Cause:** PostToolUse hook captured successful command events, but the classification heuristic in `scripts/candidate_bus.py` / `scripts/memory_reconciler.py` misrouted these events into `GOTCHAS.md` instead of categorizing them as `PROCEDURE`, `PROJECT`, or filtering them as routine operational events.

### 7.4 Answering "Have we tried this approach before, and why did it fail?"
- **Current System Capability:** **PARTIALLY IMPLEMENTED (Heuristic / Semantic)**.
- **How it works:** An agent querying "Why does Gradle crash?" or "Have we tried running gradle without flags?" retrieves the `Gradle Daemon Memory Exhaustion` chunk from `GOTCHAS.md` via hybrid vector + BM25 search.
- **Architectural Limitation:** The system lacks a dedicated, machine-queryable "Dead-End Registry" with typed schema attributes:
  `{approach_tried: str, failure_signature: str, root_cause: str, rejected_at: timestamp, alternative: str}`.
  Instead, negative knowledge relies on semi-structured markdown entries in `GOTCHAS.md`. While human-readable and semantically retrievable, it cannot be queried with deterministic SQL/predicate filtering.

---

## 8. Section 53: Procedural Memory & Invariant 16 Quarantine

Procedural memory distills recurring operational sequences into reusable runbooks while preventing unverified AI-generated code from compromising the execution environment.

### 8.1 Procedural Distillation Architecture (`scripts/procedural_engine.py`)
The procedural engine mines episodic session logs (`.agents/memory/sessions/*.md`) to identify recurring command sequences:
1. **Parsing:** Extracts commands, code blocks, working directories, and explicit provenance markers (`Command:`, `Cwd:`, `Output:`, `Error:`, `Correction:`).
2. **Clustering:** Groups recurring subsequences across multiple sessions (minimum support $N \ge 2$).
3. **Enrichment:** Adds prerequisite checks and advisory verification steps.
4. **Synthesis:** Generates structured `CandidateProcedure` instances.

### 8.2 Procedural Schema Specification
```json
{
  "id": "proc-20260904-python3-01",
  "title": "Environment & Toolchain Verification Workflow",
  "domain": "environment",
  "description": "Automated distillation of recurring command sequence across 2 sessions.",
  "source_sessions": ["2026-09-04-1240", "2026-09-04-1800"],
  "recurrence_count": 2,
  "confidence": 1.0,
  "tags": ["environment", "distilled-procedure", "recurring-workflow"],
  "status": "CANDIDATE_STAGED",
  "admitted": false,
  "admission_policy": "Requires explicit human or gatekeeper policy admission (Invariant 16)",
  "created_at": "2026-09-04T12:43:00Z",
  "steps": [
    {
      "step_number": 1,
      "step_type": "INFERRED_STEP",
      "name": "Inspect Workspace Root & Path Isolation",
      "command": null,
      "cwd": "/workspaces/codespaces-blank"
    },
    {
      "step_number": 2,
      "step_type": "VERIFIED_STEP",
      "name": "Run Environment Doctor",
      "command": "python3 tools/bin/agy-env-doctor",
      "verification": "Exit code 0 and successful output"
    }
  ]
}
```

### 8.3 Section 46 Step Distinction Hierarchy
Every step within a procedural workflow is explicitly categorized to prevent treating heuristic recommendations as verified facts:
1. **`OBSERVED_COMMAND`:** Verbatim shell command executed during an authentic session turn.
2. **`VERIFIED_STEP`:** Observed command verified with a passing exit code ($0$) and verified output assertions.
3. **`INFERRED_STEP`:** Logical prerequisite inferred by analysis (e.g. confirming CMake exists before building).
4. **`RECOMMENDED_STEP`:** Advisory best-practice recommendation (e.g. running secret scan after build).
5. **`OPTIONAL_STEP`:** Conditional fallback or diagnostic step (e.g. running verbose test trace).

### 8.4 Invariant 16 Quarantine Enforcement
**Invariant 16 Rule:**  
> *Generated candidate procedures must NEVER be written directly to active `.agents/skills/` or `~/.gemini/antigravity-cli/skills/`. No generated procedure becomes active without explicit human or policy admission.*

#### Hardcoded Boundary Enforcement (`assert_staging_allowed`):
```python
def assert_staging_allowed(self, target_path: str) -> None:
    canonical_target = os.path.realpath(os.path.abspath(target_path))
    for forbidden in self.forbidden_skills_dirs:
        canonical_forbidden = os.path.realpath(forbidden)
        if canonical_target == canonical_forbidden or canonical_target.startswith(canonical_forbidden + os.sep):
            raise InvariantViolationError(
                f"INVARIANT 16 VIOLATION: Target '{target_path}' resolves to active skills directory '{forbidden}'."
            )
    canonical_inbox = os.path.realpath(self.inbox_dir)
    if not (canonical_target == canonical_inbox or canonical_target.startswith(canonical_inbox + os.sep)):
        raise InvariantViolationError(
            f"SECURITY BOUNDARY: Staging target must reside inside authorized inbox '{self.inbox_dir}'."
        )
```

#### Quarantine Characteristics in Active Repository:
- **Location:** Staged strictly in `.agents/memory/inbox/procedures/` as dual `.md` and `.json` artifacts.
- **Inert Status:** Every file specifies `admitted: false` and `status: "CANDIDATE_STAGED"`.
- **Security Check:** Staging method executes `scan_text` on both Markdown and JSON payloads, throwing an error if any secrets are detected.
- **Current Inventory:**
  - `proc-20260903-python3-01` (Environment verification)
  - `proc-20260903-session-memory-audit` (Session lifecycle audit)
  - `proc-20260904-python3-01` (Toolchain verification)
  - `proc-20260904-session-memory-audit` (Memory governance)
  All 4 candidate procedures are currently quarantined and inert in `inbox/procedures/`. None have been promoted to `.agents/skills/`.

---

## 9. Visual Map References & Companion Diagrams

The following authoritative Mermaid diagrams accompany this security and governance audit:

1. **End-to-End Provenance Flow Diagram:**  
   [`.agent/memory-state/diagrams/provenance-flow.mmd`](file:///workspaces/codespaces-blank/.agent/memory-state/diagrams/provenance-flow.mmd)  
   *Illustrates the complete trajectory from tool invocation and pre-tool security gating through candidate bus staging, 5-gate admission, bitemporal canonical storage, vector indexing, and context compilation with trust verdicts.*

2. **Crash Recovery & Lease Reclamation Flow Diagram:**  
   [`.agent/memory-state/diagrams/recovery-flow.mmd`](file:///workspaces/codespaces-blank/.agent/memory-state/diagrams/recovery-flow.mmd)  
   *Illustrates partial write survival via atomic temporary file renaming, kernel-driven POSIX lease reclamation on process crashes, Dead-Letter Queue (DLQ) retry mechanisms, and memory doctor automated rebuilds.*

---

## 10. Forensic Defect Ledger, Drift Analysis & Recommendations

### 10.1 Identified Defects & Technical Debt
| Defect ID | Severity | Component | Forensic Observation | Recommended Remediation |
| :--- | :--- | :--- | :--- | :--- |
| **DEF-SEC-001** | `MEDIUM` | `GOTCHAS.md` / `candidate_bus.py` | Routine successful commands (`find`, `npm install`) were ingested as `Type: GOTCHA` in `GOTCHAS.md:59-94`. | Update candidate categorization rules: commands with `exit_code == 0` must never be assigned `BUG_ROOT_CAUSE` or mapped to `GOTCHA` without explicit failure context. |
| **DEF-SEC-002** | `LOW` | Negative Knowledge Schema | `GOTCHAS.md` is semi-structured Markdown without a machine-queryable failed-approach registry. | Introduce structured schema fields (`approach_tried`, `failure_cause`, `preventative_rule`) to facilitate deterministic machine queries. |
| **DEF-SEC-003** | `LOW` | `scripts/lock_manager.py` | `recover_and_cleanup` only unlinks `.tmp` files older than 3600 seconds; stale `.lock` files are unlinked only if empty. | Enhance `recover_and_cleanup` to inspect PID / flock ownership of `.lock` files to safely reap abandoned advisory locks. |

### 10.2 Audit Verdict & Security Certification
- **Zero-Secret Guarantee:** **CERTIFIED CLEAN**. No plaintext API keys, private keys, JWTs, or passwords detected in canonical storage or staging artifacts.
- **Fail-Closed Security Gate:** **CERTIFIED ENFORCED**. PreToolUse hook denies execution on unhandled exceptions (verified empirically during audit execution).
- **Trust Demarcation:** **CERTIFIED INTACT**. Clear boundaries between untrusted candidates and trusted canonical cores.
- **Invariant 16 Quarantine:** **CERTIFIED COMPLIANT**. Procedural distillation is strictly isolated from active agent skills.
- **Concurrency & Atomicity:** **CERTIFIED SAFE**. 50 parallel updates verified with zero lost writes.

---
*Report certified by Agent 8 (Security, Governance & Trust Auditor) — Antigravity Memory OS Phase 2 Audit.*
