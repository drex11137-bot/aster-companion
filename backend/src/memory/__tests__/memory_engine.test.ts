/**
 * Aster Companion - Memory Engine Comprehensive Verification Suite
 * File: backend/src/memory/__tests__/memory_engine.test.ts
 *
 * Verifies strict compliance with PRD v1.1 Section 9.4, 14, 16:
 * 1. Categorization across all 8 canonical PRD types.
 * 2. Confidence-gated admission (< 0.65 staged as tentative inferences).
 * 3. Non-destructive bitemporal updates and supersession with valid_time ranges.
 * 4. Epistemic fact distinction (explicit_fact vs inference).
 * 5. Sensitive inference refusal (religion, health, political speculation rejected).
 * 6. Semantic search with pgvector cosine distance, strict profile isolation, and citations.
 * 7. Affirmative item-level sharing, audit logging, and instant link/copy revocation.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import {
  CONFIDENCE_ADMISSION_THRESHOLD,
  MEMORY_CATEGORIES,
  MemoryCategory,
  MemoryRecord,
  ProfileIsolationViolationError,
  SensitiveInferenceRefusedError,
  UnconfirmedSharingError,
} from '../types.js';
import { InMemoryMemoryStore, computeCosineSimilarity } from '../memory_store.js';
import { MemoryManager } from '../memory_manager.js';
import { SemanticSearchEngine } from '../semantic_search.js';
import { MemorySharingService } from '../memory_sharing_service.js';
import { SensitiveInferenceGuard } from '../sensitive_inference_guard.js';

describe('Aster Companion Memory Engine (PRD v1.1)', () => {
  let store: InMemoryMemoryStore;
  let manager: MemoryManager;
  let searchEngine: SemanticSearchEngine;
  let sharingService: MemorySharingService;

  const profileA = '00000000-0000-0000-0000-000000000001';
  const profileB = '00000000-0000-0000-0000-000000000002';
  const userId = '11111111-1111-1111-1111-111111111111';

  beforeEach(() => {
    store = new InMemoryMemoryStore();
    manager = new MemoryManager(store, {
      admissionThreshold: CONFIDENCE_ADMISSION_THRESHOLD,
    });
    searchEngine = new SemanticSearchEngine(store, {
      defaultMinSimilarity: 0.5,
      defaultMatchLimit: 10,
    });
    sharingService = new MemorySharingService(store, {
      verifyProfilesBelongToUser: async () => true,
    });
  });

  // ==========================================================================
  // SECTION 1: Categorization Strictly into PRD v1.1 Types
  // ==========================================================================

  describe('1. Categorization & PRD v1.1 Types', () => {
    it('supports all 8 canonical memory categories from PRD v1.1 Section 14.2', async () => {
      expect(MEMORY_CATEGORIES).toEqual([
        'conversational',
        'preference',
        'behavioral',
        'activity',
        'relationship_social',
        'procedural',
        'profile_config',
        'explicitly_shared',
      ]);

      for (const category of MEMORY_CATEGORIES) {
        const memory = await manager.remember(profileA, {
          category,
          content: `Test content for ${category}`,
          confidenceScore: 0.9,
          provenanceSource: 'user_turn:1',
          factType: 'explicit_fact',
        });

        expect(memory.category).toBe(category);
        expect(memory.profileId).toBe(profileA);
        expect(memory.status).toBe('active');
      }
    });

    it('rejects invalid memory categories with Zod validation error', async () => {
      await expect(
        manager.remember(profileA, {
          category: 'invalid_category_type' as any,
          content: 'This should fail schema validation',
          confidenceScore: 0.8,
          provenanceSource: 'test',
          factType: 'explicit_fact',
        })
      ).rejects.toThrow();
    });

    it('heuristic categorizer correctly maps content to canonical types', () => {
      expect(MemoryManager.categorizeContent('Prefer concise bullet points with minimal preamble')).toBe('preference');
      expect(MemoryManager.categorizeContent('Steps to deploy the backend to staging environment')).toBe('procedural');
      expect(MemoryManager.categorizeContent('Usually exercises every morning at 7am before work')).toBe('behavioral');
      expect(MemoryManager.categorizeContent('Currently working on the pgvector migration task')).toBe('activity');
      expect(MemoryManager.categorizeContent('Sarah is the project manager and team leader')).toBe('relationship_social');
      expect(MemoryManager.categorizeContent('Set voice to British accent and warm personality')).toBe('profile_config');
      expect(MemoryManager.categorizeContent('We discussed the history of the solar system')).toBe('conversational');
    });
  });

  // ==========================================================================
  // SECTION 2: Confidence-Gated Admission (0.65 Threshold)
  // ==========================================================================

  describe('2. Confidence-Gated Admission', () => {
    it('stages memories below 0.65 confidence as tentative inferences', async () => {
      const tentative = await manager.remember(profileA, {
        category: 'preference',
        content: 'User may possibly prefer dark mode on laptop',
        confidenceScore: 0.62, // Below 0.65 threshold
        provenanceSource: 'screen_ocr:contrast_analysis',
        factType: 'inference',
      });

      expect(tentative.status).toBe('tentative_inference');
      expect(tentative.confidenceScore).toBe(0.62);
      expect(tentative.metadata?.isTentative).toBe(true);

      // By default, listMemories excludes tentative inferences
      const activeList = await manager.listMemories(profileA);
      expect(activeList.some((m) => m.id === tentative.id)).toBe(false);

      // Querying with includeTentative returns it
      const allList = await manager.listMemories(profileA, { includeTentative: true });
      expect(allList.some((m) => m.id === tentative.id)).toBe(true);
    });

    it('admits memories at or above 0.65 confidence as active permanent facts', async () => {
      const active = await manager.remember(profileA, {
        category: 'preference',
        content: 'User explicitly confirmed dark mode preference',
        confidenceScore: 0.65, // Exactly at 0.65 threshold
        provenanceSource: 'settings:user_input',
        factType: 'explicit_fact',
      });

      expect(active.status).toBe('active');
      expect(active.confidenceScore).toBe(0.65);

      const list = await manager.listMemories(profileA);
      expect(list.some((m) => m.id === active.id)).toBe(true);
    });

    it('promotes tentative memory to active status when verified with confidence >= 0.65', async () => {
      const tentative = await manager.remember(profileA, {
        category: 'activity',
        content: 'User appears to be learning Spanish',
        confidenceScore: 0.55,
        provenanceSource: 'screen_ocr:browser_duolingo',
        factType: 'inference',
      });

      expect(tentative.status).toBe('tentative_inference');

      // User confirms in conversation: "Yes, I am taking Spanish lessons every Tuesday"
      const promoted = await manager.promoteTentativeMemory(
        profileA,
        tentative.id,
        0.98,
        'user_dialogue:turn_12_confirmation'
      );

      expect(promoted.status).toBe('active');
      expect(promoted.confidenceScore).toBe(0.98);
      expect(promoted.version).toBe(2);
      expect(promoted.supersedesId).toBe(tentative.id);

      // Verify the old tentative version was marked superseded
      const history = await manager.getMemoryHistory(profileA, tentative.id);
      expect(history.length).toBe(2);
      expect(history[0]?.status).toBe('superseded');
      expect(history[1]?.status).toBe('active');
    });

    it('rejects promotion if provided confirmed confidence is still below 0.65', async () => {
      const tentative = await manager.remember(profileA, {
        category: 'activity',
        content: 'User might be interested in tennis',
        confidenceScore: 0.40,
        provenanceSource: 'audio_snippet',
        factType: 'inference',
      });

      await expect(
        manager.promoteTentativeMemory(profileA, tentative.id, 0.60)
      ).rejects.toThrow(/below admission threshold/);
    });
  });

  // ==========================================================================
  // SECTION 3: Epistemic Fact Distinction & Sensitive Inference Refusal
  // ==========================================================================

  describe('3. Epistemic Distinction & Sensitive Inference Refusal', () => {
    it('refuses speculative religious inference without explicit user statement', async () => {
      await expect(
        manager.remember(profileA, {
          category: 'conversational',
          content: 'User is probably a practicing Catholic based on church calendar search',
          confidenceScore: 0.70,
          provenanceSource: 'screen_search_history',
          factType: 'inference', // Inference on sensitive domain!
        })
      ).rejects.toThrow(SensitiveInferenceRefusedError);
    });

    it('refuses speculative health and mental health diagnosis inference', async () => {
      await expect(
        manager.remember(profileA, {
          category: 'conversational',
          content: 'User appears to suffer from clinical depression and anxiety symptoms',
          confidenceScore: 0.85,
          provenanceSource: 'typing_cadence_sentiment_analysis',
          factType: 'inference', // Health speculation without explicit statement!
        })
      ).rejects.toThrow(SensitiveInferenceRefusedError);
    });

    it('refuses speculative political voting affiliation inference', async () => {
      await expect(
        manager.remember(profileA, {
          category: 'conversational',
          content: 'User is likely a Democrat party donor and voter',
          confidenceScore: 0.75,
          provenanceSource: 'news_reading_tracker',
          factType: 'inference',
        })
      ).rejects.toThrow(SensitiveInferenceRefusedError);
    });

    it('admits explicit user statement regarding health, elevating sensitivity to restricted', async () => {
      // User explicitly says: "I have asthma and need to carry my inhaler"
      const memory = await manager.remember(profileA, {
        category: 'conversational',
        content: 'I have asthma and need to carry an albuterol inhaler',
        confidenceScore: 1.0,
        provenanceSource: 'user_spoken_statement:turn_5',
        factType: 'explicit_fact', // Stated directly by the user!
      });

      expect(memory.status).toBe('active');
      expect(memory.factType).toBe('explicit_fact');
      expect(memory.sensitivityLevel).toBe('restricted');
    });

    it('admits explicit user statement regarding religion, elevating sensitivity to high', async () => {
      // User explicitly says: "I observe Jewish holidays and keep kosher"
      const memory = await manager.remember(profileA, {
        category: 'preference',
        content: 'I observe Jewish holidays and require kosher food options',
        confidenceScore: 1.0,
        provenanceSource: 'user_chat_statement',
        factType: 'explicit_fact',
      });

      expect(memory.status).toBe('active');
      expect(memory.factType).toBe('explicit_fact');
      expect(memory.sensitivityLevel).toBe('high');
    });
  });

  // ==========================================================================
  // SECTION 4: Non-Destructive Updates & Supersession (valid_time ranges)
  // ==========================================================================

  describe('4. Non-Destructive Updates & Temporal Supersession', () => {
    it('creates a new version with valid_time ranges without destroying historical entry', async () => {
      const v1 = await manager.remember(profileA, {
        category: 'preference',
        content: 'User prefers Python for backend development',
        confidenceScore: 0.90,
        provenanceSource: 'user_statement:v1',
        factType: 'explicit_fact',
      });

      expect(v1.version).toBe(1);
      expect(v1.validTimeStart).toBeDefined();
      expect(v1.validTimeEnd).toBeNull();
      expect(v1.status).toBe('active');

      // User later changes preference: "I now prefer TypeScript for all backend work"
      const v2 = await manager.update(profileA, v1.id, {
        content: 'User prefers TypeScript for backend development',
        confidenceScore: 0.95,
        reason: 'User preference updated during conversation',
      });

      expect(v2.version).toBe(2);
      expect(v2.content).toBe('User prefers TypeScript for backend development');
      expect(v2.supersedesId).toBe(v1.id);
      expect(v2.validTimeEnd).toBeNull();
      expect(v2.status).toBe('active');

      // Check the old record was marked superseded with a closed valid_time_end
      const v1Record = await store.getMemoryById(profileA, v1.id);
      expect(v1Record?.status).toBe('superseded');
      expect(v1Record?.validTimeEnd).toBeDefined();
      expect(v1Record?.supersededById).toBe(v2.id);

      // Point-in-time query as of v1 should return v1
      const activeList = await manager.listMemories(profileA);
      expect(activeList.length).toBe(1);
      expect(activeList[0]?.id).toBe(v2.id);

      // Lineage retrieves both versions in historical order
      const history = await manager.getMemoryHistory(profileA, v2.id);
      expect(history.length).toBe(2);
      expect(history[0]?.id).toBe(v1.id);
      expect(history[0]?.version).toBe(1);
      expect(history[1]?.id).toBe(v2.id);
      expect(history[1]?.version).toBe(2);
    });

    it('enforces profile isolation during memory updates', async () => {
      const memA = await manager.remember(profileA, {
        category: 'preference',
        content: 'Profile A private memory',
        confidenceScore: 0.9,
        provenanceSource: 'test',
        factType: 'explicit_fact',
      });

      // Attempt to update Profile A memory using Profile B
      await expect(
        manager.update(profileB, memA.id, { content: 'Malicious cross-profile overwrite' })
      ).rejects.toThrow();
    });
  });

  // ==========================================================================
  // SECTION 5: Soft Forgetting & Pinning
  // ==========================================================================

  describe('5. Soft Forgetting & Pinning', () => {
    it('soft-forgets a memory preserving audit history', async () => {
      const memory = await manager.remember(profileA, {
        category: 'activity',
        content: 'Temporary project deadline November 5th',
        confidenceScore: 0.95,
        provenanceSource: 'calendar',
        factType: 'explicit_fact',
      });

      await manager.forget(profileA, memory.id);

      const forgotten = await store.getMemoryById(profileA, memory.id);
      expect(forgotten?.isForgotten).toBe(true);
      expect(forgotten?.status).toBe('forgotten');

      // Excluded from standard listings
      const active = await manager.listMemories(profileA);
      expect(active.some((m) => m.id === memory.id)).toBe(false);
    });

    it('pins and unpins memory items', async () => {
      const memory = await manager.remember(profileA, {
        category: 'preference',
        content: 'Always respond concisely with bullet points',
        confidenceScore: 1.0,
        provenanceSource: 'user_setting',
        factType: 'explicit_fact',
      });

      expect(memory.isPinned).toBe(false);

      const pinned = await manager.pin(profileA, memory.id, true);
      expect(pinned.isPinned).toBe(true);

      const unpinned = await manager.pin(profileA, memory.id, false);
      expect(unpinned.isPinned).toBe(false);
    });
  });

  // ==========================================================================
  // SECTION 6: Semantic Search & Citations with Strict Profile Isolation
  // ==========================================================================

  describe('6. Semantic Search & Structured Citations', () => {
    it('computes cosine distance similarity and enforces profile-isolation WHERE filter', async () => {
      // Vector representation of "TypeScript programming language"
      const vecTypeScript = [0.8, 0.6, 0.0, 0.0];
      // Vector representation of "Culinary recipes and baking"
      const vecCooking = [0.0, 0.0, 0.9, 0.4];

      // Insert memory in Profile A
      await manager.remember(profileA, {
        category: 'preference',
        content: 'User loves writing backend services in TypeScript',
        confidenceScore: 0.92,
        provenanceSource: 'chat:turn_10',
        factType: 'explicit_fact',
        embedding: vecTypeScript,
      });

      // Insert memory in Profile B (isolated profile under same account)
      await manager.remember(profileB, {
        category: 'preference',
        content: 'Profile B secret: user writes TypeScript on weekends',
        confidenceScore: 0.95,
        provenanceSource: 'chat:turn_2',
        factType: 'explicit_fact',
        embedding: vecTypeScript, // Identical semantic embedding
      });

      // Query Profile A with TypeScript vector
      const citationsA = await searchEngine.search(profileA, {
        embedding: [0.75, 0.65, 0.0, 0.0],
      });

      // Assertions:
      // 1. Strict Profile Isolation: Citations must ONLY come from Profile A
      expect(citationsA.length).toBe(1);
      expect(citationsA[0]?.profileId).toBe(profileA);
      expect(citationsA[0]?.content).toBe('User loves writing backend services in TypeScript');

      // 2. Output contains confidence score, source provenance, timestamp, and formatted citation
      expect(citationsA[0]?.confidenceScore).toBe(0.92);
      expect(citationsA[0]?.sourceProvenance).toBe('chat:turn_10');
      expect(citationsA[0]?.timestamp).toBeDefined();
      expect(citationsA[0]?.similarityScore).toBeGreaterThan(0.9);
      expect(citationsA[0]?.formattedCitation).toContain('Confidence: 92%');
      expect(citationsA[0]?.formattedCitation).toContain('Source: chat:turn_10');

      // Profile B search verifies Profile B isolation
      const citationsB = await searchEngine.search(profileB, {
        embedding: [0.75, 0.65, 0.0, 0.0],
      });
      expect(citationsB.length).toBe(1);
      expect(citationsB[0]?.profileId).toBe(profileB);
      expect(citationsB[0]?.content).toBe('Profile B secret: user writes TypeScript on weekends');
    });

    it('excludes forgotten memories from semantic search results', async () => {
      const vec = [0.5, 0.5, 0.5, 0.5];
      const mem = await manager.remember(profileA, {
        category: 'activity',
        content: 'Expired workout schedule',
        confidenceScore: 0.9,
        provenanceSource: 'test',
        factType: 'explicit_fact',
        embedding: vec,
      });

      await manager.forget(profileA, mem.id);

      const results = await searchEngine.search(profileA, { embedding: vec });
      expect(results.length).toBe(0);
    });

    it('rejects empty profileId for semantic search queries', async () => {
      await expect(
        searchEngine.search('', { embedding: [1, 0, 0, 0] })
      ).rejects.toThrow(ProfileIsolationViolationError);
    });
  });

  // ==========================================================================
  // SECTION 7: Memory Sharing Service (Deliberate Item-Level Sharing & Revocation)
  // ==========================================================================

  describe('7. Deliberate Memory Sharing & Instant Revocation', () => {
    it('mandates affirmative user confirmation; rejects unconfirmed sharing', async () => {
      const memA = await manager.remember(profileA, {
        category: 'preference',
        content: 'User prefers oat milk in coffee',
        confidenceScore: 0.95,
        provenanceSource: 'breakfast_dialogue',
        factType: 'explicit_fact',
      });

      // Attempt to share without affirmative confirmation (confirmedByUser: false)
      await expect(
        sharingService.shareMemoryItem({
          sourceProfileId: profileA,
          destinationProfileId: profileB,
          memoryId: memA.id,
          confirmedByUser: false, // Unconfirmed!
          userId,
        })
      ).rejects.toThrow(UnconfirmedSharingError);

      // Verify no share record or destination copy was created
      const isShared = await sharingService.isMemorySharedWith(profileA, profileB, memA.id);
      expect(isShared).toBe(false);
    });

    it('rejects sharing a memory with the same profile', async () => {
      const memA = await manager.remember(profileA, {
        category: 'activity',
        content: 'Work in progress',
        confidenceScore: 0.9,
        provenanceSource: 'test',
        factType: 'explicit_fact',
      });

      await expect(
        sharingService.shareMemoryItem({
          sourceProfileId: profileA,
          destinationProfileId: profileA, // Same profile!
          memoryId: memA.id,
          confirmedByUser: true,
          userId,
        })
      ).rejects.toThrow(/must differ/);
    });

    it('shares confirmed memory, logs share event, and categorizes destination copy as explicitly_shared', async () => {
      const vec = [0.1, 0.9, 0.2, 0.3];
      const memA = await manager.remember(profileA, {
        category: 'preference',
        content: 'User prefers vegetarian dining options',
        confidenceScore: 0.96,
        provenanceSource: 'diet_discussion',
        factType: 'explicit_fact',
        embedding: vec,
      });

      // Deliberately share with affirmative confirmation
      const { share, destinationMemory } = await sharingService.shareMemoryItem({
        sourceProfileId: profileA,
        destinationProfileId: profileB,
        memoryId: memA.id,
        confirmedByUser: true,
        userId,
        reason: 'Share dietary preference between companion profiles',
        confirmationDetails: {
          confirmedAt: new Date().toISOString(),
          clientDeviceId: 'pixel-9-pro',
        },
      });

      // 1. Share record logged
      expect(share.confirmedByUser).toBe(true);
      expect(share.sourceProfileId).toBe(profileA);
      expect(share.destinationProfileId).toBe(profileB);
      expect(share.revokedAt).toBeNull();

      // 2. Destination copy created in Profile B with 'explicitly_shared' category
      expect(destinationMemory.profileId).toBe(profileB);
      expect(destinationMemory.category).toBe('explicitly_shared');
      expect(destinationMemory.content).toBe('User prefers vegetarian dining options');
      expect(destinationMemory.confidenceScore).toBe(0.96);

      // 3. Profile B can now retrieve this memory in list and search
      const bList = await manager.listMemories(profileB);
      expect(bList.some((m) => m.id === destinationMemory.id)).toBe(true);

      const bSearch = await searchEngine.search(profileB, { embedding: vec });
      expect(bSearch.some((c) => c.content === destinationMemory.content)).toBe(true);
    });

    it('revocation instantly breaks link and deletes destination copy from Profile B', async () => {
      const vec = [0.4, 0.5, 0.6, 0.7];
      const memA = await manager.remember(profileA, {
        category: 'relationship_social',
        content: 'User sister name is Clara',
        confidenceScore: 1.0,
        provenanceSource: 'family_tree',
        factType: 'explicit_fact',
        embedding: vec,
      });

      const { share, destinationMemory } = await sharingService.shareMemoryItem({
        sourceProfileId: profileA,
        destinationProfileId: profileB,
        memoryId: memA.id,
        confirmedByUser: true,
        userId,
      });

      // Ensure Profile B currently has the memory
      expect(await store.getMemoryById(profileB, destinationMemory.id)).not.toBeNull();

      // REVOKE SHARE
      const revokeResult = await sharingService.revokeShare({
        shareId: share.id,
        userId,
        reason: 'User revoked cross-profile sharing',
      });

      expect(revokeResult.revokedShareId).toBe(share.id);
      expect(revokeResult.destinationMemoryDeleted).toBe(true);

      // Verify link is broken
      const isStillShared = await sharingService.isMemorySharedWith(profileA, profileB, memA.id);
      expect(isStillShared).toBe(false);

      // Verify destination copy in Profile B is deleted
      const destAfterRevoke = await store.getMemoryById(profileB, destinationMemory.id);
      expect(destAfterRevoke).toBeNull();

      // Profile B search no longer returns this memory
      const bSearchAfterRevoke = await searchEngine.search(profileB, { embedding: vec });
      expect(bSearchAfterRevoke.length).toBe(0);

      // Source memory in Profile A remains completely intact
      const sourceAfterRevoke = await store.getMemoryById(profileA, memA.id);
      expect(sourceAfterRevoke).not.toBeNull();
      expect(sourceAfterRevoke?.content).toBe('User sister name is Clara');
    });
  });

  // ==========================================================================
  // SECTION 8: Vector Math & Citation Block Formatting
  // ==========================================================================

  describe('8. Vector Cosine Distance & Math Accuracy', () => {
    it('computes exact cosine similarity and handles mathematical boundary cases', () => {
      // Identical vectors -> similarity 1.0
      expect(computeCosineSimilarity([1, 0, 0], [1, 0, 0])).toBeCloseTo(1.0);
      expect(computeCosineSimilarity([0.5, 0.5], [0.5, 0.5])).toBeCloseTo(1.0);

      // Orthogonal vectors -> similarity 0.0
      expect(computeCosineSimilarity([1, 0, 0], [0, 1, 0])).toBeCloseTo(0.0);

      // Opposing vectors -> similarity -1.0
      expect(computeCosineSimilarity([1, 0], [-1, 0])).toBeCloseTo(-1.0);

      // Zero vector -> returns 0.0 without NaN or divide-by-zero crash
      expect(computeCosineSimilarity([0, 0], [0, 0])).toBe(0);
      expect(computeCosineSimilarity([1, 2], [0, 0])).toBe(0);

      // Different length vectors -> returns 0
      expect(computeCosineSimilarity([1, 2], [1, 2, 3])).toBe(0);
    });

    it('formats LLM citation prompt injection block with strict isolation headers', async () => {
      const vec = [0.9, 0.1];
      await manager.remember(profileA, {
        category: 'preference',
        content: 'Prefers 2-space indentation',
        confidenceScore: 0.99,
        provenanceSource: 'user_editor_config',
        factType: 'explicit_fact',
        embedding: vec,
      });

      const citations = await searchEngine.search(profileA, { embedding: vec });
      const block = SemanticSearchEngine.formatCitationBlock(citations);

      expect(block).toContain('### Retrieved Companion Memory Context (Strict Profile Isolation)');
      expect(block).toContain('Prefers 2-space indentation');
      expect(block).toContain('Category: preference');
      expect(block).toContain('Confidence: 99%');
    });
  });

  // ==========================================================================
  // SECTION 9: Multi-generation Lineage Updates (v1 -> v2 -> v3)
  // ==========================================================================

  describe('9. Multi-generation Lineage Updates (v1 -> v2 -> v3)', () => {
    it('chains multiple versions preserving rootMemoryId and non-destructive bitemporal history', async () => {
      // v1
      const v1 = await manager.remember(profileA, {
        category: 'preference',
        content: 'Favorite drink is black coffee',
        confidenceScore: 0.9,
        provenanceSource: 'chat:v1',
        factType: 'explicit_fact',
      });

      // v2
      const v2 = await manager.update(profileA, v1.id, {
        content: 'Favorite drink is latte with oat milk',
        confidenceScore: 0.92,
        reason: 'Updated drink choice',
      });

      // v3
      const v3 = await manager.update(profileA, v2.id, {
        content: 'Favorite drink is matcha latte with oat milk',
        confidenceScore: 0.98,
        reason: 'Shifted to matcha',
      });

      expect(v1.version).toBe(1);
      expect(v2.version).toBe(2);
      expect(v3.version).toBe(3);

      expect(v2.supersedesId).toBe(v1.id);
      expect(v3.supersedesId).toBe(v2.id);

      // All share the exact same rootMemoryId
      expect(v1.rootMemoryId).toBe(v1.id);
      expect(v2.rootMemoryId).toBe(v1.id);
      expect(v3.rootMemoryId).toBe(v1.id);

      // Lineage returns all 3 versions in chronological order
      const history = await manager.getMemoryHistory(profileA, v3.id);
      expect(history.length).toBe(3);
      expect(history[0]?.version).toBe(1);
      expect(history[0]?.status).toBe('superseded');
      expect(history[1]?.version).toBe(2);
      expect(history[1]?.status).toBe('superseded');
      expect(history[2]?.version).toBe(3);
      expect(history[2]?.status).toBe('active');
    });
  });

  // ==========================================================================
  // SECTION 10: Adversarial Profile Isolation Security Suite
  // ==========================================================================

  describe('10. Adversarial Profile Isolation Security Suite', () => {
    it('proves Profile A cannot read, list, mutate, or search Profile B memories', async () => {
      const memB = await manager.remember(profileB, {
        category: 'conversational',
        content: 'Profile B top secret conversational disclosure',
        confidenceScore: 0.99,
        provenanceSource: 'private_chat',
        factType: 'explicit_fact',
        embedding: [0.12, 0.88],
      });

      // Attack 1: Direct ID read attempt by Profile A
      const readAttempt = await manager.getMemory(profileA, memB.id);
      expect(readAttempt).toBeNull();

      // Attack 2: Listing attempt by Profile A
      const listAttempt = await manager.listMemories(profileA);
      expect(listAttempt.some((m) => m.id === memB.id)).toBe(false);

      // Attack 3: Mutation attempt by Profile A
      await expect(
        manager.update(profileA, memB.id, { content: 'Compromised content' })
      ).rejects.toThrow();

      // Attack 4: Soft-forget / delete attempt by Profile A
      await expect(
        manager.forget(profileA, memB.id)
      ).rejects.toThrow();

      // Attack 5: Semantic search query by Profile A targeting Profile B embedding
      const searchAttempt = await searchEngine.search(profileA, { embedding: [0.12, 0.88] });
      expect(searchAttempt.length).toBe(0);
    });
  });
});
