# Aster Companion Research Dossier: Supabase PostgreSQL Architecture, RLS & Multi-Tenant Isolation

**Domain Key**: `03_supabase_architecture_rls`  
**Generated**: November 2026  
**Total Queries Executed**: 20  

## Executive Findings & Architectural Directives

This document compiles verified engineering research for Supabase PostgreSQL Architecture, RLS & Multi-Tenant Isolation in the Aster Companion ecosystem. These findings directly inform our Supabase backend, Android Compose client, iOS SwiftUI app, laptop web client, and multimodal AI pipelines.

---

## Query Inventory & Verified Evidence

### Q1: Supabase PostgreSQL Row Level Security multi-tenant profile isolation auth.uid()

- **[Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)** (Exa)
- **[Can Supabase isolate tenant data in a multi-tenant SaaS app?](https://supabase.com/kb/faqs/database/multi-tenant-isolation)** (Exa)
- **[Authorization via Row Level Security | Supabase Features](https://supabase.com/features/row-level-security)** (Exa)
- **[examples/tenancy.sql](https://github.com/unitautogen/rlsautotest/blob/e2dc7e0f/examples/tenancy.sql)** (Exa)

### Q2: Postgres CHECK constraint enforce maximum two companion profiles per account

- **[PostgreSQL CHECK Constraints](https://neon.com/postgresql/tutorial/check-constraint)** (Tavily)
  > "A check constraint allows you to enforce data integrity rules at the database level. A check constraint uses a boolean expression to evaluate the values, ensuring that only valid data is inserted or updated in a table.  ### Creating CHECK constraints  Typically, you create a check constraint when cr"
- **[Understanding Check Constraints in PostgreSQL | Severalnines](https://severalnines.com/blog/understanding-check-constraints-postgresql)** (Tavily)
  > "Check constraints are awesome. Using the ‘built-in’ solutions provided by the PostgreSQL database itself, to enforce any data restriction(s) makes perfect sense. Time and effort spent implementing Check constraints for necessary column(s), far outweighs not implementing any at all. Thus saving time"
- **[PostgreSQL: Documentation: 18: 5.5. Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)** (Tavily)
  > "As you see, the constraint definition comes after the data type, just like default value definitions. Default values and constraints can be listed in any order. A check constraint consists of the key word `CHECK` followed by an expression in parentheses. The check constraint expression should involv"

### Q3: Row level security default deny with check using clauses PostgreSQL 16 best practices

- **[PostgreSQL: Documentation: 18: 5.9. Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)** (Exa)
- **[PostgreSQL: Documentation: 18: CREATE POLICY](https://www.postgresql.org/docs/current/sql-createpolicy.html)** (Exa)
- **[Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)** (Exa)
- **[Everything you need to know about Postgres Row Level Security | Microsoft Learn](https://learn.microsoft.com/en-us/shows/posette-an-event-for-postgres-2024/everything-you-need-to-know-about-postgres-row-level-security)** (Exa)

### Q4: Postgres table schema companion profiles devices sessions events memories chat messages

- **[Building Stateful Conversations with Postgres and LLMs](https://medium.com/@levi_stringer/building-stateful-conversations-with-postgres-and-llms-e6bb2a5ff73e)** (Tavily)
  > "Users Table: Stores user-specific information.    Sessions Table: Keeps track of each chat session, noting start and end times, and linking back to the respective user.    Messages Table: Records the details of every message within a session, including sender, text, and timestamps. [...] ); With the"
- **[Chat schema for PostgreSQL and MongoDB](https://dba.stackexchange.com/questions/306757/chat-schema-for-postgresql-and-mongodb)** (Tavily)
  > "1  I added the message schema to the question.Jacqueline  –Jacqueline 2022-01-29 23:31:53 +00:00 Commented Jan 29, 2022 at 23:31                Thank you, Your answer was very helpful.Jacqueline  –Jacqueline 2022-01-30 07:43:34 +00:00 Commented Jan 30, 2022 at 7:43 [...] for the `messages` they crea"
- **[Chat with your database - Postgres Database Chat Assistant – Full Workflow Guide](https://aineversleeps.substack.com/p/chat-with-your-database-postgres)** (Tavily)
  > "5. Chat History (Memory Buffer)      Keeps the last few messages (default: 5) in context so that follow-ups like “What about July?” work seamlessly. [...] ccu ON tc.constraint_name = ccu.constraint_name WHERE c.table_name = '{{ $fromAI("table_name") }}' AND c.table_schema = '{{ $fromAI("schema_name""

### Q5: Supabase Realtime postgres_changes broadcast presence active profile per device sync

- **[Presence](https://supabase.com/docs/guides/realtime/presence)** (Exa)
- **[Postgres Changes | Supabase Docs](https://supabase.com/docs/guides/realtime/postgres-changes)** (Exa)
- **[Supabase Realtime](https://supabase.com/realtime)** (Exa)
- **[JavaScript: on | Supabase Docs](https://supabase.com/docs/reference/javascript/on)** (Exa)

### Q6: Supabase pgvector HNSW indexing cosine distance high dimensional memory embeddings

- **[HNSW indexes | Supabase Docs](https://supabase.com/docs/guides/ai/vector-indexes/hnsw-indexes)** (Tavily)
  > "Supabase wordmarkSupabase wordmarkDOCS   Start  Supabase wordmarkSupabase wordmarkDOCS  AI & Vectors  HNSW indexes  HNSW is an algorithm for approximate nearest neighbor search. It is a frequently used index type that can improve performance when querying highly-dimensional vectors, like those repre"
- **[Understanding vector search and HNSW index with pgvector - Neon](https://neon.com/blog/understanding-vector-search-and-hnsw-index-with-pgvector)** (Tavily)
  > "CREATE INDEX ON words USING hnsw (embedding vector\_cosine\_ops) WITH (m = 16, ef\_construction = 64);  The index build query above creates an HNSW index on the `vectors` column of `documents` table, using the cosine distance and the specified parameters m and ef\_construction.  When you create an H"
- **[Faster similarity search performance with pgvector indexes | Google Cloud Blog](https://cloud.google.com/blog/products/databases/faster-similarity-search-performance-with-pgvector-indexes)** (Tavily)
  > "The following code snippet demonstrates how you can build HNSW indexes in pgvector with different distance functions and index parameters.  This snippet creates an HNSW index on the `embedding` column of the `product_embeddings` table using the cosine distance function, with HNSW parameters m and `e"

### Q7: Postgres bitemporal data modeling valid_time transaction_time non-destructive updates

- **[PostgreSQL: Documentation: 19: 5.7. Temporal Tables](https://www.postgresql.org/docs/19/ddl-temporal-tables.html)** (Exa)
- **[SQL2011Temporal - PostgreSQL wiki](https://wiki.postgresql.org/wiki/SQL2011Temporal)** (Exa)
- **[adamsanghera/pg_bitemporal](https://github.com/adamsanghera/pg_bitemporal)** (Exa)
- **[Implementing Temporal Features in PostgreSQL: SQL Standard and Beyond](https://postgresql.us/events/pgdaychicago2024/sessions/session/1553/slides/130/bitemporal_standard.pdf)** (Exa)

### Q8: Supabase storage bucket RLS policies secure uploaded media photos audio chunks

- **[Storage Access Control | Supabase Docs](https://supabase.com/docs/guides/storage/security/access-control)** (Tavily)
  > "By default Storage does not allow any uploads to buckets without RLS policies. You selectively allow certain operations by creating RLS policies on the `storage.objects` table.  You can find the documentation for the storage schema here , and to simplify the process of crafting your policies, you ca"
- **[Supabase Storage: Buckets, Policies, Signed URLs and Limits](https://www.runxbuild.com/blog/supabase-storage)** (Tavily)
  > "Each file has a row in the storage.objects table, and access is governed by row level security on that table. If you create a private bucket and upload with a user session before adding any policy, the upload fails, because RLS denies by default. This is the single most common first-hour problem. [."
- **[Upload Files to Supabase Storage | Tutorial | RapidDev](https://www.rapidevelopers.com/supabase-tutorial/how-to-upload-files-to-supabase-storage)** (Tavily)
  > "Supabase Storage is an S3-compatible object storage system integrated with Supabase Auth and Row Level Security. This tutorial covers creating buckets, uploading files from the client, securing uploads with RLS policies, and generating URLs to access your files. You will build a complete file upload"

### Q9: Postgres advisory locks single writer lease locking prevent race conditions in sync

- **[PostgreSQL: Documentation: 18: 13.3. Explicit Locking](https://www.postgresql.org/docs/current/explicit-locking.html)** (Exa)
- **[feat: Postgres reader-writer lock (v0.5.0)](https://github.com/tunahanaliozturk/OrionLock/pull/52)** (Exa)
- **[Making Exactly-Once Effects Boring with PostgreSQL Advisory Locks, Leases, and Fencing Tokens | 晨昏线](https://blog.ipuau.com/en/posts/20230131-making-exactly-once-effects-boring-with-postgresql-advisory-locks-leases-and-fencing-tokens.html)** (Exa)
- **[](https://docs.ecotone.tech/modelling/event-sourcing/setting-up-projections/gap-detection-and-consistency)** (Exa)

### Q10: Supabase Edge Functions Deno TypeScript JWT verification auth context service role

- **[Supabase Edge Functions Quickstart](https://www.youtube.com/watch?v=5OWH9c4u68M)** (Tavily)
  > "Edge Functions are server-side TypeScript functions, distributed globally at the edge—close to your users. They can be used for listening to webhooks or integrating your Supabase project with third-parties like Stripe. Edge Functions are developed using Deno.  Read the docs:   Install and update the"
- **[Edge Functions | Supabase Docs](https://supabase.com/docs/guides/functions)** (Tavily)
  > "Supabase wordmarkSupabase wordmarkDOCS   Start  Supabase wordmarkSupabase wordmarkDOCS  Edge Functions  Run TypeScript functions globally at the edge.  Edge Functions are server-side TypeScript functions, distributed globally at the edge—close to your users. They can be used for listening to webhook"
- **[Edge Functions - Supabase](https://supabase-supabase.mintlify.app/concepts/edge-functions)** (Tavily)
  > "# Edge Functions  Learn about Supabase Edge Functions - globally distributed TypeScript functions running on Deno for low-latency server-side logic.  Supabase Edge Functions are server-side TypeScript functions distributed globally at the edge—close to your users. Built on Deno, they provide a porta"

### Q11: Postgres database migration strategy idempotent SQL DDL rollback scripts

- **[PostgreSQL: Re: Idempotent DDL Updates](https://www.postgresql.org/message-id/CAALojA8wMNRdYhx%3DTWMP3PudWqxtRvyNE%3DXNNL7Mwu6dOc%2B8cQ%40mail.gmail.com)** (Exa)
- **[Idempotent migrations - supaschema](https://supaschema.com/docs/guides/idempotent-postgres-migrations)** (Exa)
- **[Idempotent DDL Updates](https://www.postgresql.org/message-id/CAALojA_KrOF4AT1LeNjcSdoMkS25QcZsftG%3D6c%2B8qB58DRgtaA%40mail.gmail.com)** (Exa)
- **[Idempotent Migration Scripts | Zero-Downtime Schema](https://www.zero-downtime-schema.com/database-migration-fundamentals-tool-selection/idempotent-script-design/)** (Exa)

### Q12: Supabase adversarial RLS test suite proving profile A cannot read profile B rows

- **[A small RLS read-test case study: what makes testing a real app difficult? · supabase · Discussion #51878 · GitHub](https://github.com/orgs/supabase/discussions/51878)** (Tavily)
  > "| One thing I'd add to this is testing the negative cases for both reads and writes, not just verifying that each user can read their own rows.  For a multi-tenant app, I'd test with two authenticated users belonging to different tenants and verify that Tenant A cannot read, update, or delete Tenant"
- **[Mastering Supabase RLS - "Row Level Security" as a Beginner - DEV Community](https://dev.to/asheeshh/mastering-supabase-rls-row-level-security-as-a-beginner-5175)** (Tavily)
  > "``` // Test as a specific user const{data: userATodos} = await supabaseClientForUserA. from(' todos '). select(' ');// Test as another user const{data: userBTodos} = await supabaseClientForUserB. from(' todos '). select(' ');// Verify that each user only sees their own todos console. assert(userATod"
- **[Row Level Security | Supabase Docs](https://supabase.com/docs/guides/database/postgres/row-level-security)** (Tavily)
  > "93  );  94  95  -- Matching no rows is not proof on its own. Pair every denied write with a  96  -- check that the row it targeted is intact. Scope it to that row: a suite  97  -- that asserts on everything a role can see breaks once the table holds more.  98  set local request.jwt.claim.sub = '1111"

### Q13: Postgres composite foreign keys profile_id and user_id enforcing strict boundaries

- **[this is the db for ultimate twitter clone](https://gist.github.com/sonipranjal/8015583e89ecb75ef7361605991d7b6d)** (Exa)
- **[PostgreSQL: Documentation: 18: 5.5. Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)** (Exa)
- **[Composite FK referencing PK + non unique attribute](https://dba.stackexchange.com/questions/297552/composite-fk-referencing-pk-non-unique-attribute)** (Exa)
- **[](https://www.prisma.io/docs/orm/next/data-modeling/relational-databases)** (Exa)

### Q14: Supabase connection pooling Supavisor transaction mode vs session mode pgvector queries

- **[Supavisor FAQ | Supabase Knowledge Base](https://supabase.com/kb/troubleshooting/supavisor-faq-YyP5tI)** (Tavily)
  > "In session mode, it will immediately create a new a direct connection for a new client unless the “Pool Size” is reached  In transaction mode, once a direct connection is established, the pooler will keep it available for reuse for another client. However, if the connection remains unused for 5 minu"
- **[Supavisor Session Mode (5432) not releasing connections from application (Softr.io client) · supabase · Discussion #41520 · GitHub](https://github.com/orgs/supabase/discussions/41520)** (Tavily)
  > "always Session mode + polling clients.  For Softr / REST-style traffic you generally want Supavisor in Transaction mode so idle sessions return to the pool between requests.  The 8–9s fetch interval is a giveaway, each poll can pin or reopen a session.  Quick way to confirm:    Switch to Transaction"
- **[Connection pooling and limits | Supabase Docs](https://supabase.com/docs/guides/database/connecting-to-postgres/pooling-and-limits)** (Tavily)
  > "In most cases, choose either PgBouncer or Supavisor for pooled or transaction-based traffic. Direct connections remain the best choice for long-lived sessions, and shared pooler session mode is the alternative when those sessions need IPv4. Run both poolers at once only when you need to raise the to"

### Q15: Supabase database triggers updating updated_at timestamps and audit log entries

- **[Postgres Triggers | Supabase Docs](https://supabase.com/docs/guides/database/postgres/triggers)** (Exa)
- **[Postgres Auditing in 150 lines of SQL](https://supabase.com/blog/postgres-audit)** (Exa)
- **[](https://supabase-supabase.mintlify.app/database/triggers)** (Exa)
- **[Auth Audit Logs](https://supabase.com/docs/guides/auth/audit-logs)** (Exa)

### Q16: Postgres cryptographically secure token hashing pgcrypto sha256 for device sessions

- **[Enhancing data security with PostgreSQL’s pgcrypto Extension Part - 2 - OpenSourceDB](https://opensource-db.com/enhancing-data-security-with-postgresqls-pgcrypto-extension-part-2)** (Tavily)
  > "Hashing is commonly used for storing passwords securely and verifying data integrity. Even if an attacker gains access to the hash, they cannot easily reverse-engineer it to obtain the original data.  ### How Hashing Works in pgcrypto  pgcrypto offers multiple hashing functions, including popular al"
- **[Day 26: PostgreSQL 18 Data Encryption with pgcrypto #postgresql #security #day26](https://www.linkedin.com/pulse/day-26-postgresql-18-data-encryption-pgcrypto-security-mahto-naayc)** (Tavily)
  > "pgcrypto is an extension for PostgreSQL that provides cryptographic functions directly inside the database. It allows you to encrypt/decrypt data, generate hashes, create random bytes, and securely store sensitive information without relying entirely on application-side code.  ### Common capabilitie"
- **[PostgreSQL: Documentation: 18: F.26. pgcrypto — cryptographic functions](https://www.postgresql.org/docs/current/pgcrypto.html)** (Tavily)
  > "`CREATE`  `pgcrypto` requires OpenSSL and won't be installed if OpenSSL support was not selected when PostgreSQL was built.  `pgcrypto`  ### F.26.1. General Hashing Functions #  #### F.26.1.1. `digest()` #  `digest()`  Computes a binary hash of the given `data`. `type` is the algorithm to use. Stand"

### Q17: Data export JSON schema GDPR Article 20 data portability compliance PostgreSQL

- **[How to Handle GDPR Subject Access Requests (SAR) in PostgreSQL — pgcomply](https://pgcomply.com/blog/gdpr-subject-access-request-postgresql)** (Exa)
- **[@vocoweb/portability](https://www.npmjs.com/package/@vocoweb/portability)** (Exa)
- **[Users can export their data in a structured, machine-readable format — AuditBuffet Pattern Catalog | AuditBuffet](https://auditbuffet.com/patterns/ab-001503)** (Exa)
- **[Database Compliance for SaaS Startups: The Minimum Viable Compliance Stack — pgcomply](https://pgcomply.com/blog/postgresql-compliance-saas-startups)** (Exa)

### Q18: Soft delete vs hard cascading delete compliance retention policies PostgreSQL

- **[Soft Delete vs Hard Delete: The Database Decision That Looks Simple Until Production](https://www.linkedin.com/pulse/soft-delete-vs-hard-database-decision-looks-simple-until-goyal-r00mf)** (Tavily)
  > "Does law or policy require actual erasure? Hard delete or anonymize according to the applicable retention requirements.  Does the data need to remain for financial or legal records? Retain what you're required to retain; don't blindly cascade deletion.  Will historical analytics or relationships dep"
- **[Soft Deletes with Ecto and PostgreSQL | Hacker News](https://news.ycombinator.com/item?id=41270830)** (Tavily)
  > "|  |  |  |  ---  |  |  | nine\_k on Aug 17, 2024  | root | parent | next (javascript:void(0))   I suppose "on delete cascade" would fire appropriate triggers in the downstream tables, and "on delete set null" will take care of upstream and peer tables. If this is not sufficient, and a live record in"
- **[Soft deletion with PostgreSQL: but with logic on the database | Lobsters](https://lobste.rs/s/kfaauq/soft_deletion_with_postgresql_with_logic)** (Tavily)
  > "Other than that, I don't understand understand what specific problem with cascade deletes arise from doing it from within a procedure versus doing it with tricks like the one in this post. If you want to undo a cascaded deletion, you have to know the chain and do it in the right order regardless of"

### Q19: Supabase webhook signatures HMAC-SHA256 verification Edge Functions event processing

- **[Platform Webhooks](https://supabase.com/docs/guides/platform/webhooks)** (Exa)
- **[Auth Hooks](https://supabase.com/docs/guides/auth/auth-hooks)** (Exa)
- **[Database Webhooks](https://supabase.com/docs/guides/database/webhooks)** (Exa)
- **[examples/edge-functions/supabase/functions/stripe-webhooks/index.ts](https://github.com/supabase/supabase/blob/master/examples/edge-functions/supabase/functions/stripe-webhooks/index.ts)** (Exa)

### Q20: PostgreSQL indexes composite index optimization for profile_id created_at sequence_id

- **[PostgreSQL Index Usage and Optimization | myDBA.dev](https://mydba.dev/blog/postgres-index-usage-optimization)** (Tavily)
  > "An index only helps queries whose filters (`WHERE`), joins (`ON`), or ordering (`ORDER BY`) can use it. A composite index on `(user_id, created_at)` helps:   `WHERE user_id = ?` (uses the leading column alone).  `WHERE user_id = ? AND created_at > ?` (uses both).  `WHERE user_id = ? ORDER BY created"
- **[Designing PostgreSQL Composite Indexes for Filters and Sorting - Vincent Schmalbach](https://www.vincentschmalbach.com/designing-postgresql-composite-indexes-for-filters-and-sorting)** (Tavily)
  > "The first two keys are the columns the query checks for one exact value. Within the entries for that customer and status, `created_at` orders tickets from newest to oldest. PostgreSQL can use the index to find the matching rows in the requested order, and with a suitable plan it can stop after findi"
- **[SQL Indexing Explained: Composite Indexes and Column Order](https://milanjovanovic.tech/blog/how-to-design-the-right-sql-index)** (Tavily)
  > "``` SELECT  SELECT FROM comments FROMWHERE issue_id = 10 WHERE = 10 AND user_id = 29 AND = 29 AND created_at >= NOW() - INTERVAL '1 month' AND>= NOW() - INTERVAL '1 month'ORDER BY created_at DESC; ORDER BY DESC; ```  With no index, it's another sequential scan: 16.6ms. With single-column indexes on"

