# Aster Companion Research Dossier: Offline-First Architecture, Resumable Sync & Durable Buffers

**Domain Key**: `05_offline_sync_continuity`  
**Generated**: November 2026  
**Total Queries Executed**: 20  

## Executive Findings & Architectural Directives

This document compiles verified engineering research for Offline-First Architecture, Resumable Sync & Durable Buffers in the Aster Companion ecosystem. These findings directly inform our Supabase backend, Android Compose client, iOS SwiftUI app, laptop web client, and multimodal AI pipelines.

---

## Query Inventory & Verified Evidence

### Q1: Offline first mobile architecture Android Room iOS SwiftData durable outbox pattern

- **[Build an offline-first app  |  App architecture  |  Android Developers](https://developer.android.com/topic/architecture/data-layer/offline-first)** (Exa)
- **[Offline-First Mobile System Design: Android and iOS Model](https://mobiledesignrounds.com/guides/offline-first-hub/)** (Exa)
- **[Design a Chat App on Android and iOS: Outbox and Sync](https://mobiledesignrounds.com/mobile-system-design/chat-app/)** (Exa)
- **[skills/sota-mobile/rules/03-offline-background-push.md](https://github.com/martinholovsky/sota-skills/blob/main/skills/sota-mobile/rules/03-offline-background-push.md)** (Exa)

### Q2: Monotonic sequence numbers per device distributed event log reconciliation algorithm

- **[Deterministic Temporal Reconciliation for Effective-Dated Identity Lifecycle Events](https://arxiv.org/html/2609.14017v1)** (Tavily)
  > "The model assumes an authoritative source for each logical fact, immutable physical event records once emitted, exact replays preserving the same physical event identifier, and a source sequence that is unique or monotonically increasing within the ordering scope. The sequence is not claimed to be a"
- **[DDIA: Consistency and Consensus in Distributed Systems | Candost's Blog](https://candost.blog/books/consistency-and-consensus-in-distributed-systems)** (Tavily)
  > "The consensus algorithms we talked about above don’t guarantee that there will always be a single leader. However, they guarantee a single leader for each epoch (a round), a number defined by a protocol, and it’s monotonic and ever-increasing."
- **[Event-Time Telemetry For Unreliable Devices — Tech Interview Concept | PracHub](https://prachub.com/concepts/event-time-telemetry-for-unreliable-devices)** (Tavily)
  > "Here the same event-time and reconciliation concepts apply, but the system must treat commands as first-class, safety-critical state. Ask whether commands must be guaranteed delivered, executed exactly once, or only best-effort. Build a command ledger (append-only) with per-command idempotency keys"

### Q3: Chunked resumable file upload TUS protocol SHA-256 checksum mobile network drops

- **[docs/faq.md](https://github.com/tus/tus-js-client/blob/main/docs/faq.md)** (Exa)
- **[Resumable upload protocol 1.0.x | tus.io](https://tus.io/protocols/resumable-upload)** (Exa)
- **[Protocol | tus.io](https://tus.io/protocols/resumable-upload/1-0-x)** (Exa)
- **[Clarification on chunks and the checksum extension · Issue #143 · tus/tus-resumable-upload-protocol](https://github.com/tus/tus-resumable-upload-protocol/issues/143)** (Exa)

### Q4: Conflict free replicated data types CRDT for conversational messages and notes

- **[About CRDTs • Conflict-free Replicated Data Types](https://crdt.tech)** (Tavily)
  > "Edit this page  Create issue  # About CRDTs  A Conflict-free Replicated Data Type (CRDT) is a data structure that simplifies distributed data storage systems and multi-user applications.  In many systems, copies of some data need to be stored on multiple computers (known as replicas). Examples of su"
- **[Log-Structured Conflict-Free Replicated Data Types](https://cs.ucsb.edu/sites/default/files/documents/paper_9.pdf)** (Tavily)
  > "Conﬂict-Free Replicated Data Types (CRDTs) – are abstract data types that provide a principled approach for this asynchronous reconciliation. CRDTs support a weaker model than strong consistency, namely, Strong Eventual Consistency (SEC) . SEC guarantees that whenever two replicas receive the same s"
- **[Conflict-free replicated data type - Wikipedia](https://en.wikipedia.org/wiki/Conflict-free_replicated_data_type)** (Tavily)
  > "Wikidata item  Appearance  From Wikipedia, the free encyclopedia  Type of data structure  "CRDT" redirects here. For Centenary Rural Development Trust, see Centenary Bank.  In distributed computing, a conflict-free replicated data type (CRDT) is a data structure that is replicated "Replication (comp"

### Q5: Detecting event gaps and missing sequence numbers in streaming event ingestion

- **[](https://gethook.to/blog/webhook-reconciliation-catching-dropped-events)** (Exa)
- **[GapAwareTrackingToken (Axoniq Framework - Root 5.3.1 API)](https://apidocs.axoniq.io/latest/org/axonframework/messaging/eventhandling/processing/streaming/token/GapAwareTrackingToken.html)** (Exa)
- **[Change-Data-Capture Validation](https://www.cross-engine-reconciliation.org/streaming-reconciliation-pipelines/change-data-capture-validation/)** (Exa)
- **[Per-Stream Sequence-Gap Detection ](https://autocontrol.readthedocs.io/en/latest/Eng/doc/new_features/v105_features_doc.html)** (Exa)

### Q6: Idempotency keys UUID v4 deduplication in distributed API event processing

- **[harness-engineering/agents/skills/claude-code/api-idempotency-keys/SKILL.md at main · Intense-Visions/harness-engineering · GitHub](https://github.com/Intense-Visions/harness-engineering/blob/main/agents/skills/claude-code/api-idempotency-keys/SKILL.md)** (Tavily)
  > "1. Generating a new key on every retry attempt. The entire purpose of an idempotency key is that the same key is sent on all retry attempts for a single logical operation. Generating a new UUID on each retry means each attempt is treated as a new, independent operation — no deduplication occurs. Gen"
- **[Implementing Idempotency Keys in REST APIs - Zuplo](https://zuplo.com/learning-center/implementing-idempotency-keys-in-rest-apis-a-complete-guide)** (Tavily)
  > "In Python, frameworks like Flask and Django provide excellent support for handling idempotency keys. Below is an example using Flask, where a UUIDv4 key is generated and sent via the `Idempotency-Key` header. Middleware is used to intercept requests and ensure no duplicate processing occurs.  python"
- **[Idempotency Keys Explained: Stop Duplicate API Retries](https://www.alekseialeinikov.com/en/blog/topics/architecture/idempotency-in-practice-api-retries-2026)** (Tavily)
  > "Client generates the key. A UUIDv4 or similar high-entropy string, up to 255 characters. If the server generated it, a retry would arrive with a new key and the whole mechanism would be pointless.  No sensitive data in keys. Not email addresses, not personal identifiers. Keys end up in logs, metrics"

### Q7: Local encrypted storage SQLCipher Android Room Keystore encrypted database

- **[sqlcipher/sqlcipher-android](https://github.com/sqlcipher/sqlcipher-android)** (Exa)
- **[simons-hub/android-encrypted-storage](https://github.com/simons-hub/android-encrypted-storage)** (Exa)
- **[doc/guide/database.md at master · hwsecurity-sdk/hwsecurity](https://github.com/hwsecurity-sdk/hwsecurity/blob/master/doc/guide/database.md)** (Exa)
- **[Medium](https://proandroiddev.com/how-to-encrypt-your-room-database-in-android-using-sqlcipher-0bce78328bd6)** (Exa)

### Q8: iOS Keychain protected SQLite encryption at rest data protection complete

- **[iOS Keychain and Data Protection Classes Abuse and Misuse](https://medium.com/@salamsajid7/ios-keychain-and-data-protection-classes-abuse-and-misuse-759267ee03b4)** (Tavily)
  > "The iOS Keychain is a secure SQLite database managed by `securityd`. It stores items (passwords, tokens, etc.) encrypted with AES-256, but grants access per app based on entitlements support.apple.com. Each keychain item has an _accessibility class_ (via `kSecAttrAccessible`) analogous to the file c"
- **[SQLite Encryption and Secure Storage for Sensitive Data](https://www.sqliteforum.com/p/sqlite-encryption-and-secure-storage)** (Tavily)
  > "# SQLite Forum  # SQLite Encryption and Secure Storage for Sensitive Data  ### Implementing Transparent Encryption, Key Management, and Compliance-Friendly Storage  Jenny Muralidharan  In today’s world, sensitive data like personal details, financial records, and health information, needs strong pro"
- **[MongoDB Data Encryption | MongoDB](https://www.mongodb.com/products/capabilities/security/encryption)** (Tavily)
  > "By comparison, in-transit encryption protects data as it travels over the network but does not secure it once stored or processed. At-rest encryption protects stored data on disk but does not secure it while in transit or during queries. Queryable Encryption complements both by ensuring that the mos"

### Q9: Bounded offline buffer management LRU eviction strategy preventing disk exhaustion

- **[docs/S3-DISK-CACHE-PLAN.md](https://github.com/Hikari-Systems/slater/blob/main/docs/S3-DISK-CACHE-PLAN.md)** (Exa)
- **[File Cache Internals: Cache Slicing, Multi-Queue Management, Eviction, and Warm-Up - Apache Doris](https://doris.apache.org/docs/dev/compute-storage-decoupled/file-cache/file-cache-internals/)** (Exa)
- **[[Feature][KV Offload] Add bounded capacity and LRU eviction to the filesystem tier](https://github.com/vllm-project/vllm/pull/54327)** (Exa)
- **[Eviction | Milvus Documentation](https://milvus.io/docs/eviction.md)** (Exa)

### Q10: Exponential backoff with jitter retry strategy mobile network reconnection

- **[Exponential backoff - Wikipedia](https://en.wikipedia.org/wiki/Exponential_backoff)** (Tavily)
  > "An exponential backoff algorithm is a form of closed-loop control system that reduces the rate of a controlled process in response to adverse events. For example, if a mobile app fails to connect to its server, the mobile app might try again 1 second later, then if it fails again, 2 seconds later, t"
- **[Exponential Backoff And Jitter | AWS Architecture Blog](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter)** (Tavily)
  > "Update (May 2023): After 8 years, this solution continues to serve as a pillar for how Amazon builds remote client libraries for resilient systems. Most AWS SDKs now support exponential backoff and jitter as part of their retry behavior when using standard or adaptive modes. Consequently, this patte"
- **[How Do I Implement Exponential Backoff with Jitter  | Prismatic](https://prismatic.io/blog/how-do-i-implement-exponential-backoff-with-jitter)** (Tavily)
  > "The problem isn't the retry, but the retry approach. You are using a generic retry strategy with providers that have their own ways of saying "not yet."  ## Backoff solves half the problem  Exponential backoff increases the wait between attempts:  That is better than a tight retry loop, but it does"

### Q11: Checkpointing and session resumption after network disconnect in streaming chat

- **[Resumable Streams | Helix Agents](https://agents.open-source.onhelix.ai/guide/resumable-streams)** (Exa)
- **[Reconnection and recovery](https://ably.com/docs/ai-transport/features/reconnection-and-recovery)** (Exa)
- **[](https://supabase.com/docs/guides/functions/examples/resumable-websockets)** (Exa)
- **[Reconnection and recovery](https://ably.com/docs/ai-transport/streaming/reconnection-and-recovery)** (Exa)

### Q12: Disclosing offline state honestly to user distinguishing cached read from live AI

- **[Real-Time Context for AI Agents: Keep Inputs Fresh](https://redis.io/blog/real-time-context-ai-agents-fresh-inputs)** (Tavily)
  > "Cached answers skip the live tool. Session memory can return a previous answer without re-invoking the tool that was supposed to fetch live data, so the agent responds from a snapshot while believing it checked. Cache invalidation is hard enough in apps; in agents, a cached answer also skips a decis"
- **[The Hidden Data Problem in Prompt Caching | Medium](https://medium.com/@michael.hannecke/the-hidden-data-residency-problem-in-prompt-caching-f99e6207451e)** (Tavily)
  > "are paying attention to AI infrastructure details. Cache residency transparency is a matter of time, not principle. [...] Sitemap  Open in app  Sign in  Sign in  Ai Governance  Data Privacy  # The Hidden Data Residency Problem in Prompt Caching  Michael Hannecke  Michael Hannecke  12 min read  ·  Fe"
- **[Groundhog Day for AI agents: Prompt caching patterns for using OpenAI models on Amazon Bedrock | Artificial Intelligence](https://aws.amazon.com/blogs/machine-learning/groundhog-day-for-ai-agents-prompt-caching-patterns-for-using-openai-models-on-amazon-bedrock)** (Tavily)
  > "## How to tell caching is working  Start with response usage. `cached_tokens` reports input read from the cache, and `cache_write_tokens` reports input written to it. As the conversation grows, check that later turns reuse earlier history and that new writes reflect the content being added.  `cached"

### Q13: Cross-device sync conflict resolution last write wins vs causal ordering vector clocks

- **[Conflict Resolution | Couchbase Docs](https://docs.couchbase.com/sync-gateway/current/conflict-resolution.html)** (Exa)
- **[Syncing Concurrent Changes | ObjectBox Sync](https://sync.objectbox.io/syncing-concurrent-changes)** (Exa)
- **[Approaches to Conflict-free Replicated Data Types | ACM Computing Surveys](https://dl.acm.org/doi/full/10.1145/3695249)** (Exa)
- **[Bi-directional XDCR with Mobile Clusters | Couchbase Docs](https://docs.couchbase.com/sync-gateway/current/server-compatibility/server-compatibility-xdcr-mobile.html)** (Exa)

### Q14: Durable inbox outbox message queue pattern in SQLite background worker service

- **[Transactional Outbox Pattern with SQLite](https://www.sqliteforum.com/p/implementing-the-transactional-outbox)** (Tavily)
  > "The Transactional Outbox Pattern solves this problem by recording business changes and outgoing events together in a single SQLite transaction.  Instead of attempting to update the database and publish a message as two separate operations, the application first makes both intentions durable locally."
- **[Durable Messaging | Wolverine](https://wolverinefx.net/guide/durability)** (Tavily)
  > "eventual consistency between database changes and the outgoing messages that are part of the logical transaction. Wolverine implementation of the outbox pattern also includes a separate message relay process that will send the persisted outgoing messages in background processes (it's done by marshal"
- **[Implement the Transactional Outbox Pattern by Using Azure Cosmos DB - Azure Architecture Center | Microsoft Learn](https://learn.microsoft.com/en-us/azure/architecture/databases/guide/transactional-out-box-cosmos)** (Tavily)
  > "The primary consideration is to set a suitable `TTL` value on the `DomainEvent` documents when the background worker (change feed processor) or the service bus are unavailable. In a production environment, set a time span of multiple days, like 10 days. This duration ensures that all components have"

### Q15: WorkManager Android periodic sync constraints network unmetered battery not low

- **[Define work requests  |  Background work  |  Android Developers](https://developer.android.com/develop/background-work/background-tasks/persistent/getting-started/define-work)** (Exa)
- **[Minimize the effect of regular updates  |  Connectivity  |  Android Developers](https://developer.android.com/develop/connectivity/minimize-effect-regular-updates)** (Exa)
- **[Constraints  |  API reference  |  Android Developers](https://developer.android.com/reference/androidx/work/Constraints)** (Exa)
- **[Data transfer background task options  |  Background work  |  Android Developers](https://developer.android.com/develop/background-work/background-tasks/data-transfer-options)** (Exa)

### Q16: BGTaskScheduler iOS background processing sync window limitations guidelines

- **[Background Tasks in iOS: The Complete Guide](https://blog.stackademic.com/background-tasks-in-ios-the-complete-guide-2a46b793084b)** (Tavily)
  > "Here’s the thing: Background tasks in iOS are complex. There are multiple APIs. Each has different rules. Each has different limitations. Use the wrong one, and your task gets killed. Use the right one, and it works perfectly.  This guide will show you:     All background task APIs in iOS    When to"
- **[Handling Background Tasks and Multitasking in iOS Apps](https://reintech.io/blog/handling-background-tasks-multitasking-ios-apps)** (Tavily)
  > "``` Strategy: ├── Use BGAppRefreshTask for periodic content sync ├── Process remote notifications for breaking updates └── Implement finite-length tasks for posting content Schedule: ├── BGAppRefreshTask: Every 4-8 hours ├── Remote notifications: As needed └── User-initiated posts: On demand with ba"
- **[Why Is iOS Background Task Execution Unreliable After the Latest iOS Update?](https://www.c-sharpcorner.com/article/why-is-ios-background-task-execution-unreliable-after-the-latest-ios-update)** (Tavily)
  > "Examples include:   Reduced background location accuracy  Limits on background Bluetooth scanning  Tighter control over background network usage  If an app does not clearly justify its background behavior, iOS may silently restrict or stop it.  ## Background Task Time Limits Are Enforced More Strict"

### Q17: Delta synchronization calculating modified entities since last sync timestamp

- **[](https://learn.microsoft.com/en-us/graph/delta-query-overview)** (Exa)
- **[Using DynamoDB
            sync operations on versioned data sources in AWS AppSync](https://docs.aws.amazon.com/appsync/latest/devguide/aws-appsync-conflict-detection-and-sync-sync-operations.html)** (Exa)
- **[Downloading Only Modified Entities](https://help.sap.com/docs/service-asset-manager/sap-service-and-asset-manager-configuration-guide/optimized-delta-synchronization)** (Exa)
- **[Synchronization Architecture | ID PASS DataCollect](https://data-collect.idpass.org/architecture/sync-architecture)** (Exa)

### Q18: Data corruption recovery validating SQLite integrity_check on app startup

- **[SQLite User Forum: SQLite integrity check=ok but data corrupted](https://sqlite.org/forum/info/2bb1709c122e46724e94739cb0d0b356589315dcc8cea41b0880bb4a2fcb0ddc)** (Tavily)
  > "I'm developing a C# WinForms app that uses SQLite. The DB is very small with 18 tables and is only 168KB on disk. As part of app start-up an integrity check is performed on the DB, the DB is Vacuumed and the file copied to the backup (using C# to simplify overwrite of existing file), and then an int"
- **[How to Recover a Corrupted SQLite Database and Verify the Restore](https://oneuptime.com/blog/post/2026-09-08-recover-corrupted-sqlite-database/view)** (Tavily)
  > "The only clean result is one row containing `ok`. `integrity_check` detects malformed records, missing or multiply used pages, freelist problems, index inconsistencies, and several constraint errors. It does not report foreign-key violations, so run this separately if the database opens:  ``` sqlite"
- **[How To Corrupt An SQLite Database File](https://www.sqlite.org/howtocorrupt.html)** (Tavily)
  > "## Overview  An SQLite database is highly resistant to corruption. If an application crash, or an operating-system crash, or even a power failure occurs in the middle of a transaction, the partially written transaction should be automatically rolled back the next time the database file is accessed."

### Q19: Transparent sync status indicator pending uploads synced state error notifications

- **[](https://blog.aethas.ai/building-a-sync-status-indicator)** (Exa)
- **[How sync works | Filarr](https://filarr.com/en/docs/how-sync-works)** (Exa)
- **[Checking the datastore sync status in JavaScript](https://dropbox.tech/developers/checking-the-datastore-sync-status-in-javascript)** (Exa)
- **[Sync Status — Paragon UI](https://www.paragon-ui.com/docs/sync-status)** (Exa)

### Q20: Handling clock drift across multi-device clients NTP timestamp reconciliation

- **[Handling Clock Drift in Distributed Edge Devices • FlowFuse Blog](https://flowfuse.com/blog/2026/07/time-synchronization-edge-devices)** (Tavily)
  > "SCADA systems, historians, HMIs, edge gateways, and industrial data platforms depend on accurate timestamps to understand production events and maintain reliable historical records.  Preventing clock drift does not require complex infrastructure. A reliable NTP client, multiple or local time sources"
- **[Master NTP Clock Configuration for Optimal Time Accuracy](https://www.innovationwireless.com/blog/ntp-configuration-a-practical-guide-to-clock-synchronization.html)** (Tavily)
  > "Time is a hidden dependency in almost every system: authentication tokens expire, logs must align across hosts, databases rely on ordering, and distributed apps break when timestamps drift. That’s why ntp configuration matters. Done well, your ntp clock stays consistent across machines, improving cl"
- **[Understanding NTP, Chrony, and Time Synchronization in Distributed Systems](https://medium.com/@anil.goyal0057/understanding-ntp-chrony-and-time-synchronization-in-distributed-systems-448149ce25dc)** (Tavily)
  > "It is a protocol used to synchronize clocks across systems over a network.  Without NTP:  Machine A → 10:00:00   Machine B → 09:59:53   Machine C → 10:00:08 Over time, all computer clocks drift due to:     hardware differences    CPU timing variations    virtualization delays    temperature changes"

