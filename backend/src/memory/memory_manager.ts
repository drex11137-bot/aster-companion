/**
 * Aster Companion - Core Memory Manager
 * File: backend/src/memory/memory_manager.ts
 *
 * Implements authoritative PRD v1.1 Memory Engine requirements:
 * 1. Strict categorization into 8 PRD memory types:
 *    conversational, preference, behavioral, activity,
 *    relationship_social, procedural, profile_config, explicitly_shared.
 * 2. Confidence-gated admission:
 *    memories below 0.65 confidence are staged as tentative inferences
 *    rather than permanent facts.
 * 3. Non-destructive updates / supersession:
 *    updates create new versions with valid_time ranges;
 *    historical entries marked superseded.
 * 4. Epistemic fact distinction:
 *    distinguishes explicitly stated facts from inferences;
 *    refuses sensitive inferences (religion, medical/health speculation, etc.)
 *    without explicit user statement.
 */

import { randomUUID } from 'node:crypto';
import {
  CandidateMemoryInput,
  CandidateMemoryInputSchema,
  CONFIDENCE_ADMISSION_THRESHOLD,
  MemoryCategory,
  MemoryNotFoundError,
  MemoryQueryOptions,
  MemoryRecord,
  MemoryStatus,
  MemoryUpdateInput,
  ProfileIsolationViolationError,
  SensitivityLevel,
} from './types.js';
import { SensitiveInferenceGuard } from './sensitive_inference_guard.js';
import { IMemoryStore } from './memory_store.js';

export interface EmbeddingProvider {
  generateEmbedding(text: string): Promise<number[]>;
}

export interface MemoryManagerConfig {
  admissionThreshold?: number;
  embeddingProvider?: EmbeddingProvider;
}

export class MemoryManager {
  private readonly admissionThreshold: number;
  private readonly embeddingProvider?: EmbeddingProvider;

  constructor(
    private readonly store: IMemoryStore,
    config: MemoryManagerConfig = {}
  ) {
    this.admissionThreshold = config.admissionThreshold ?? CONFIDENCE_ADMISSION_THRESHOLD;
    this.embeddingProvider = config.embeddingProvider;
  }

  /**
   * Adopts and records a candidate memory into profile long-term storage.
   *
   * Enforces:
   * 1. Schema & category validation (strict 8 canonical PRD categories).
   * 2. Sensitive inference refusal (PRD 14.4 & 16: religion, health speculation rejected).
   * 3. Confidence-gated admission:
   *    - Score < 0.65 -> staged as 'tentative_inference'
   *    - Score >= 0.65 -> admitted as 'active' permanent fact
   * 4. Bitemporal valid_time initialization: version 1, valid_time_start = now, valid_time_end = null.
   */
  public async remember(
    profileId: string,
    rawInput: CandidateMemoryInput
  ): Promise<MemoryRecord> {
    if (!profileId || typeof profileId !== 'string') {
      throw new ProfileIsolationViolationError('Valid profileId is required for memory admission.');
    }

    // 1. Validate payload against Zod schema
    const parsed = CandidateMemoryInputSchema.parse(rawInput);

    // 2. Sensitive Inference Security Gate
    // Refuses speculative inferences touching sensitive domains
    const guardResult = SensitiveInferenceGuard.validate(parsed);
    const effectiveSensitivity: SensitivityLevel =
      guardResult.sensitiveCategoryDetected
        ? guardResult.sensitivityLevel
        : (parsed.sensitivityLevel ?? guardResult.sensitivityLevel);

    // 3. Confidence-Gated Admission Logic (PRD 14.4)
    // Memories below 0.65 are staged as tentative inferences rather than permanent facts
    const isTentative =
      parsed.confidenceScore < this.admissionThreshold || parsed.factType === 'inference';

    const status: MemoryStatus = parsed.confidenceScore < this.admissionThreshold
      ? 'tentative_inference'
      : 'active';

    const now = new Date().toISOString();
    const validTimeStart = parsed.validTimeStart ?? now;

    // 4. Generate vector embedding if not provided and embedding provider exists
    let embedding: number[] | null = parsed.embedding ?? null;
    if (!embedding && this.embeddingProvider) {
      try {
        embedding = await this.embeddingProvider.generateEmbedding(parsed.content);
      } catch (err) {
        // Fall back gracefully to null embedding rather than blocking memory write
        embedding = null;
      }
    }

    const memoryId = randomUUID();
    const record: MemoryRecord = {
      id: memoryId,
      profileId,
      category: parsed.category,
      content: parsed.content.trim(),
      confidenceScore: parsed.confidenceScore,
      provenanceSource: parsed.provenanceSource,
      sensitivityLevel: effectiveSensitivity,
      isPinned: parsed.isPinned ?? false,
      isForgotten: false,
      factType: parsed.factType,
      status,
      version: 1,
      validTimeStart,
      validTimeEnd: null, // Open-ended: currently active / valid
      rootMemoryId: memoryId, // Root of its own version tree
      supersededById: null,
      supersedesId: null,
      embedding,
      metadata: {
        ...parsed.metadata,
        isTentative,
        admissionThresholdUsed: this.admissionThreshold,
        sensitiveDomainMatched: guardResult.matchedDomain ?? null,
      },
      createdAt: now,
      updatedAt: now,
    };

    return await this.store.insertMemory(record);
  }

  /**
   * Non-destructive Update / Supersession
   *
   * PRD v1.1 Rule:
   * Updates NEVER destroy historical truth or overwrite in-place.
   * Instead:
   * 1. The existing record's valid_time_end is closed at `now`,
   *    its status is marked 'superseded', and superseded_by_id points to the new version.
   * 2. A brand-new record version is created with version = old.version + 1,
   *    valid_time_start = now, valid_time_end = null, supersedes_id = old.id.
   * 3. The full audit trail and bitemporal history is preserved.
   */
  public async update(
    profileId: string,
    memoryId: string,
    updates: MemoryUpdateInput
  ): Promise<MemoryRecord> {
    if (!profileId) {
      throw new ProfileIsolationViolationError('Valid profileId is required for update.');
    }

    // Retrieve active version ensuring profile isolation
    const current = await this.store.getMemoryById(profileId, memoryId);
    if (!current) {
      throw new MemoryNotFoundError(memoryId, profileId);
    }

    if (current.status === 'superseded') {
      throw new Error(`Cannot update memory ${memoryId} because it has already been superseded.`);
    }

    const now = new Date().toISOString();
    const newContent = updates.content !== undefined ? updates.content.trim() : current.content;
    const newConfidence = updates.confidenceScore ?? current.confidenceScore;
    const newCategory = updates.category ?? current.category;
    const newSensitivity = updates.sensitivityLevel ?? current.sensitivityLevel;
    const newPinned = updates.isPinned ?? current.isPinned;
    const newProvenance = updates.provenanceSource ?? current.provenanceSource;

    // Run sensitive inference validation on new content
    const testCandidate: CandidateMemoryInput = {
      category: newCategory,
      content: newContent,
      confidenceScore: newConfidence,
      provenanceSource: newProvenance,
      factType: current.factType,
      sensitivityLevel: newSensitivity,
    };
    const guardResult = SensitiveInferenceGuard.validate(testCandidate);

    // Compute embedding for updated content if needed
    let embedding: number[] | null = updates.embedding ?? current.embedding ?? null;
    if (updates.content && !updates.embedding && this.embeddingProvider) {
      try {
        embedding = await this.embeddingProvider.generateEmbedding(newContent);
      } catch {
        embedding = current.embedding ?? null;
      }
    }

    const newVersionId = randomUUID();
    const rootId = current.rootMemoryId || current.id;

    // Check confidence admission status for updated version
    const newStatus: MemoryStatus = newConfidence < this.admissionThreshold
      ? 'tentative_inference'
      : 'active';

    // 1. Mark existing version superseded with valid_time_end = now
    await this.store.supersedeMemory(current.id, profileId, newVersionId, now);

    // 2. Insert new version with valid_time_start = now, open valid_time_end
    const newRecord: MemoryRecord = {
      id: newVersionId,
      profileId,
      category: newCategory,
      content: newContent,
      confidenceScore: newConfidence,
      provenanceSource: newProvenance,
      sensitivityLevel: guardResult.sensitivityLevel,
      isPinned: newPinned,
      isForgotten: false,
      factType: current.factType,
      status: newStatus,
      version: current.version + 1,
      validTimeStart: now,
      validTimeEnd: null,
      rootMemoryId: rootId,
      supersededById: null,
      supersedesId: current.id,
      embedding,
      metadata: {
        ...current.metadata,
        ...updates.metadata,
        supersededReason: updates.reason ?? 'Direct memory modification',
        supersededAt: now,
      },
      createdAt: now,
      updatedAt: now,
    };

    return await this.store.insertMemory(newRecord);
  }

  /**
   * Forgets a memory (soft-deletion preserving privacy and auditability).
   * Sets is_forgotten = true and status = 'forgotten'.
   */
  public async forget(profileId: string, memoryId: string): Promise<MemoryRecord> {
    const existing = await this.store.getMemoryById(profileId, memoryId);
    if (!existing) {
      throw new MemoryNotFoundError(memoryId, profileId);
    }

    const now = new Date().toISOString();
    return await this.store.updateMemory(memoryId, profileId, {
      isForgotten: true,
      status: 'forgotten',
      validTimeEnd: now,
    });
  }

  /**
   * Toggles pinned status for important memories.
   */
  public async pin(profileId: string, memoryId: string, isPinned: boolean): Promise<MemoryRecord> {
    const existing = await this.store.getMemoryById(profileId, memoryId);
    if (!existing) {
      throw new MemoryNotFoundError(memoryId, profileId);
    }

    return await this.store.updateMemory(memoryId, profileId, { isPinned });
  }

  /**
   * Promotes a staged tentative inference (< 0.65) to active permanent memory status
   * once confidence has been confirmed or explicitly verified by the user.
   */
  public async promoteTentativeMemory(
    profileId: string,
    memoryId: string,
    confirmedConfidence: number,
    provenanceSource?: string
  ): Promise<MemoryRecord> {
    if (confirmedConfidence < this.admissionThreshold) {
      throw new Error(
        `Cannot promote tentative memory: confirmed confidence (${confirmedConfidence}) is below admission threshold (${this.admissionThreshold}).`
      );
    }

    const existing = await this.store.getMemoryById(profileId, memoryId);
    if (!existing) {
      throw new MemoryNotFoundError(memoryId, profileId);
    }

    if (existing.status !== 'tentative_inference') {
      throw new Error(`Memory ${memoryId} is not in tentative_inference status (current: ${existing.status}).`);
    }

    // Perform non-destructive promotion into a new active version
    return await this.update(profileId, memoryId, {
      confidenceScore: confirmedConfidence,
      provenanceSource: provenanceSource ?? `promoted_from_tentative:${existing.provenanceSource}`,
      reason: 'Confirmed verification and promotion to permanent memory',
    });
  }

  /**
   * Fetches a single memory, strictly validating profile isolation.
   */
  public async getMemory(profileId: string, memoryId: string): Promise<MemoryRecord | null> {
    if (!profileId) {
      throw new ProfileIsolationViolationError('profileId is mandatory for getMemory.');
    }
    return await this.store.getMemoryById(profileId, memoryId);
  }

  /**
   * Lists memories belonging to the profile, with options for filtering
   * by category, status, confidence, and temporal range.
   */
  public async listMemories(
    profileId: string,
    options: MemoryQueryOptions = {}
  ): Promise<MemoryRecord[]> {
    if (!profileId) {
      throw new ProfileIsolationViolationError('profileId is mandatory for listMemories.');
    }
    return await this.store.listMemories(profileId, options);
  }

  /**
   * Retrieves full chronological version history (temporal lineage) of a memory.
   */
  public async getMemoryHistory(profileId: string, memoryId: string): Promise<MemoryRecord[]> {
    const target = await this.store.getMemoryById(profileId, memoryId);
    if (!target) {
      throw new MemoryNotFoundError(memoryId, profileId);
    }

    const rootId = target.rootMemoryId || target.id;
    return await this.store.getLineage(rootId, profileId);
  }

  /**
   * Categorizes memory content into PRD v1.1 canonical types based on semantic heuristics.
   */
  public static categorizeContent(content: string): MemoryCategory {
    const text = content.toLowerCase();

    // Procedural: instructions, recurring workflows, step-by-step
    if (/\b(how to|steps to|workflow|procedure|routine|recipe|always do|guide)\b/i.test(text)) {
      return 'procedural';
    }

    // Preference: user likes, dislikes, response styles, favorites
    if (/\b(prefer|preference|favorite|like|dislike|hate|enjoy|tone|formality|brevity|concise)\b/i.test(text)) {
      return 'preference';
    }

    // Behavioral: observed user patterns, recurring habits, routine times
    if (/\b(usually|typically|habit|pattern|regularly|every morning|tend to|frequently)\b/i.test(text)) {
      return 'behavioral';
    }

    // Relationship & social: people, friends, family, coworkers, titles, roles
    if (/\b(friend|colleague|coworker|partner|spouse|wife|husband|mother|father|sister|brother|boss|manager|leader|client|relationship|sarah|john|family)\b/i.test(text)) {
      return 'relationship_social';
    }

    // Activity: ongoing task, project, event, current work
    if (/\b(working on|project|task|meeting|appointment|building|coding|drafting|reading)\b/i.test(text)) {
      return 'activity';
    }

    // Profile config: avatar, voice, name, personality settings
    if (/\b(avatar|voice|companion name|personality|appearance|accent|speaking rate)\b/i.test(text)) {
      return 'profile_config';
    }

    // Default conversational memory
    return 'conversational';
  }
}
