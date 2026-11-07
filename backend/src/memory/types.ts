/**
 * Aster Companion - Memory Engine Type Definitions
 * File: backend/src/memory/types.ts
 *
 * Implements strict data models and interfaces adhering to PRD v1.1 Section 14:
 * 1. Categorization into 8 canonical PRD memory types.
 * 2. Confidence-gated admission thresholds (0.65 boundary).
 * 3. Bitemporal modeling (valid_time ranges, supersession, versioning).
 * 4. Epistemic fact distinction (explicit_fact vs inference).
 * 5. Structured citations with provenance, confidence, and timestamps.
 * 6. Affirmative item-level memory sharing and revocation contracts.
 */

import { z } from 'zod';

// ============================================================================
// Canonical Memory Categories (PRD v1.1 Section 14.2)
// ============================================================================

export const MEMORY_CATEGORIES = [
  'conversational',
  'preference',
  'behavioral',
  'activity',
  'relationship_social',
  'procedural',
  'profile_config',
  'explicitly_shared',
] as const;

export type MemoryCategory = (typeof MEMORY_CATEGORIES)[number];

export const MemoryCategorySchema = z.enum(MEMORY_CATEGORIES);

// ============================================================================
// Epistemic Status & Fact Classification (PRD v1.1 Section 14.4)
// ============================================================================

export const FACT_TYPES = ['explicit_fact', 'inference'] as const;
export type FactType = (typeof FACT_TYPES)[number];
export const FactTypeSchema = z.enum(FACT_TYPES);

// ============================================================================
// Memory Admission Status
// ============================================================================

export const MEMORY_STATUSES = [
  'active',
  'tentative_inference',
  'superseded',
  'forgotten',
] as const;
export type MemoryStatus = (typeof MEMORY_STATUSES)[number];
export const MemoryStatusSchema = z.enum(MEMORY_STATUSES);

// ============================================================================
// Sensitivity Levels
// ============================================================================

export const SENSITIVITY_LEVELS = ['low', 'standard', 'high', 'restricted'] as const;
export type SensitivityLevel = (typeof SENSITIVITY_LEVELS)[number];
export const SensitivityLevelSchema = z.enum(SENSITIVITY_LEVELS);

// ============================================================================
// Confidence Threshold Constants
// ============================================================================

/**
 * Strict admission gate: inferences or candidate facts below 0.65 confidence
 * are NEVER admitted as permanent active facts. They are staged as tentative inferences.
 */
export const CONFIDENCE_ADMISSION_THRESHOLD = 0.65;

// ============================================================================
// Core Memory Model Interfaces
// ============================================================================

export interface MemoryRecord {
  id: string;
  profileId: string;
  category: MemoryCategory;
  content: string;
  confidenceScore: number;
  provenanceSource: string;
  sensitivityLevel: SensitivityLevel;
  isPinned: boolean;
  isForgotten: boolean;
  factType: FactType;
  status: MemoryStatus;
  version: number;
  validTimeStart: string; // ISO 8601
  validTimeEnd: string | null; // ISO 8601, null indicates currently valid
  rootMemoryId: string | null;
  supersededById: string | null;
  supersedesId: string | null;
  embedding?: number[] | null;
  metadata?: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

export interface CandidateMemoryInput {
  category: MemoryCategory;
  content: string;
  confidenceScore: number;
  provenanceSource: string;
  factType: FactType;
  sensitivityLevel?: SensitivityLevel;
  isPinned?: boolean;
  embedding?: number[];
  metadata?: Record<string, unknown>;
  validTimeStart?: string;
}

export interface MemoryUpdateInput {
  content?: string;
  confidenceScore?: number;
  category?: MemoryCategory;
  sensitivityLevel?: SensitivityLevel;
  isPinned?: boolean;
  provenanceSource?: string;
  embedding?: number[];
  metadata?: Record<string, unknown>;
  reason?: string;
}

export interface MemoryQueryOptions {
  category?: MemoryCategory;
  categories?: MemoryCategory[];
  includeSuperseded?: boolean;
  includeTentative?: boolean;
  includeForgotten?: boolean;
  minConfidence?: number;
  isPinned?: boolean;
  limit?: number;
  offset?: number;
  asOfTimestamp?: string; // Point-in-time temporal query
}

// ============================================================================
// Semantic Search & Citation Types
// ============================================================================

export interface SemanticSearchOptions {
  queryText?: string;
  queryEmbedding?: number[];
  minSimilarity?: number;
  matchLimit?: number;
  categories?: MemoryCategory[];
  includeShared?: boolean;
  includeTentative?: boolean;
}

export interface CitationResult {
  memoryId: string;
  profileId: string;
  category: MemoryCategory;
  content: string;
  similarityScore: number;
  confidenceScore: number;
  sourceProvenance: string;
  timestamp: string; // ISO 8601
  factType: FactType;
  isPinned: boolean;
  isTentative: boolean;
  formattedCitation: string;
}

// ============================================================================
// Memory Sharing Contracts (PRD v1.1 Section 9.4)
// ============================================================================

export interface ShareMemoryRequest {
  sourceProfileId: string;
  destinationProfileId: string;
  memoryId: string;
  confirmedByUser: boolean;
  userId: string;
  reason?: string;
  confirmationDetails?: {
    confirmedAt: string;
    clientDeviceId?: string;
    userAgent?: string;
  };
}

export interface MemoryShareRecord {
  id: string;
  sourceProfileId: string;
  destinationProfileId: string;
  memoryId: string;
  destinationMemoryId: string | null;
  confirmedByUser: boolean;
  confirmationMetadata: Record<string, unknown>;
  sharedAt: string;
  revokedAt: string | null;
  createdAt: string;
}

export interface RevokeShareRequest {
  shareId?: string;
  sourceProfileId?: string;
  destinationProfileId?: string;
  memoryId?: string;
  userId: string;
  reason?: string;
}

// ============================================================================
// Domain Errors
// ============================================================================

export class MemoryEngineError extends Error {
  constructor(message: string, public readonly code: string) {
    super(message);
    this.name = 'MemoryEngineError';
  }
}

export class ProfileIsolationViolationError extends MemoryEngineError {
  constructor(message: string) {
    super(message, 'PROFILE_ISOLATION_VIOLATION');
    this.name = 'ProfileIsolationViolationError';
  }
}

export class SensitiveInferenceRefusedError extends MemoryEngineError {
  constructor(
    public readonly reason: string,
    public readonly sensitiveCategory: string,
    public readonly candidateContent: string
  ) {
    super(
      `Sensitive inference refused: ${reason}. PRD v1.1 strictly prohibits unconfirmed AI speculation regarding sensitive attributes (${sensitiveCategory}) without an explicit user statement.`,
      'SENSITIVE_INFERENCE_REFUSED'
    );
    this.name = 'SensitiveInferenceRefusedError';
  }
}

export class UnconfirmedSharingError extends MemoryEngineError {
  constructor(message: string) {
    super(
      `Unconfirmed memory sharing rejected: ${message}. PRD v1.1 Section 9.4 mandates explicit, affirmative user confirmation prior to item-level sharing.`,
      'UNCONFIRMED_SHARING_REJECTED'
    );
    this.name = 'UnconfirmedSharingError';
  }
}

export class MemoryNotFoundError extends MemoryEngineError {
  constructor(memoryId: string, profileId: string) {
    super(`Memory ${memoryId} not found for profile ${profileId}`, 'MEMORY_NOT_FOUND');
    this.name = 'MemoryNotFoundError';
  }
}

// ============================================================================
// Zod Runtime Validators
// ============================================================================

export const CandidateMemoryInputSchema = z.object({
  category: MemoryCategorySchema,
  content: z.string().min(1, 'Memory content cannot be empty').max(10000),
  confidenceScore: z.number().min(0.0).max(1.0),
  provenanceSource: z.string().min(1, 'Provenance source is required'),
  factType: FactTypeSchema,
  sensitivityLevel: SensitivityLevelSchema.optional(),
  isPinned: z.boolean().optional().default(false),
  embedding: z.array(z.number()).optional(),
  metadata: z.record(z.unknown()).optional().default({}),
  validTimeStart: z.string().datetime().optional(),
});
