/**
 * Aster Companion - Semantic Memory Search & Citation Engine
 * File: backend/src/memory/semantic_search.ts
 *
 * Implements PRD v1.1 Section 14 pgvector semantic search:
 * 1. Interfaces with Supabase pgvector embedding table (1536-dimensional HNSW index).
 * 2. Computes cosine distance similarity query with profile-isolation WHERE filter:
 *    WHERE profile_id = :profileId AND is_forgotten = false.
 * 3. Returns rich, structured citations with confidence score, source provenance, and timestamp.
 */

import {
  CitationResult,
  MemoryCategory,
  ProfileIsolationViolationError,
  SemanticSearchOptions,
} from './types.js';
import { IMemoryStore } from './memory_store.js';
import { EmbeddingProvider } from './memory_manager.js';

export interface SemanticSearchEngineConfig {
  defaultMinSimilarity?: number;
  defaultMatchLimit?: number;
  embeddingProvider?: EmbeddingProvider;
}

export class SemanticSearchEngine {
  private readonly defaultMinSimilarity: number;
  private readonly defaultMatchLimit: number;
  private readonly embeddingProvider?: EmbeddingProvider;

  constructor(
    private readonly store: IMemoryStore,
    config: SemanticSearchEngineConfig = {}
  ) {
    this.defaultMinSimilarity = config.defaultMinSimilarity ?? 0.60;
    this.defaultMatchLimit = config.defaultMatchLimit ?? 10;
    this.embeddingProvider = config.embeddingProvider;
  }

  /**
   * Performs semantic similarity search across companion profile memories.
   *
   * Profile Isolation Guarantee:
   * Strictly enforces WHERE profile_id = :profileId AND is_forgotten = false.
   * Cross-profile memory leakage is architecturally impossible.
   */
  public async search(
    profileId: string,
    query: string | { embedding: number[] },
    options: SemanticSearchOptions = {}
  ): Promise<CitationResult[]> {
    if (!profileId || typeof profileId !== 'string' || profileId.trim().length === 0) {
      throw new ProfileIsolationViolationError(
        'Profile isolation requires a non-empty profileId for all semantic search queries.'
      );
    }

    // 1. Resolve query embedding
    let queryEmbedding: number[];
    if (typeof query === 'string') {
      if (!this.embeddingProvider) {
        throw new Error(
          'Text query passed to search, but no EmbeddingProvider is configured. Provide precomputed embedding or configure an EmbeddingProvider.'
        );
      }
      queryEmbedding = await this.embeddingProvider.generateEmbedding(query);
    } else {
      queryEmbedding = query.embedding;
    }

    if (!Array.isArray(queryEmbedding) || queryEmbedding.length === 0) {
      throw new Error('Query vector embedding must be a non-empty array of numbers.');
    }

    const minSimilarity = options.minSimilarity ?? this.defaultMinSimilarity;
    const matchLimit = options.matchLimit ?? this.defaultMatchLimit;

    // 2. Query Supabase pgvector table with profile-isolation filter:
    // WHERE profile_id = :profileId AND is_forgotten = false
    const matches = await this.store.searchByVector(profileId, queryEmbedding, {
      ...options,
      minSimilarity,
      matchLimit,
    });

    // 3. Format and return citations
    return matches.map(({ record, similarity }) => {
      // Build LLM-ready citation text
      const shortId = record.id.slice(0, 8);
      const confFormatted = (record.confidenceScore * 100).toFixed(0);
      const dateStr = record.validTimeStart.split('T')[0] ?? record.validTimeStart;
      const formattedCitation = `[Citation #${shortId} | Category: ${record.category} | Confidence: ${confFormatted}% | Source: ${record.provenanceSource} | Date: ${dateStr}] "${record.content}"`;

      return {
        memoryId: record.id,
        profileId: record.profileId,
        category: record.category,
        content: record.content,
        similarityScore: Number(similarity.toFixed(4)),
        confidenceScore: record.confidenceScore,
        sourceProvenance: record.provenanceSource,
        timestamp: record.validTimeStart,
        factType: record.factType,
        isPinned: record.isPinned,
        isTentative: record.status === 'tentative_inference',
        formattedCitation,
      };
    });
  }

  /**
   * Helper to format retrieved citations into a markdown injection block
   * for LLM dialogue orchestration and prompt building.
   */
  public static formatCitationBlock(citations: CitationResult[]): string {
    if (citations.length === 0) {
      return '';
    }

    const lines: string[] = [
      '### Retrieved Companion Memory Context (Strict Profile Isolation)',
    ];

    for (const c of citations) {
      lines.push(
        `- ${c.formattedCitation} (Similarity: ${(c.similarityScore * 100).toFixed(1)}%)`
      );
    }

    return lines.join('\n');
  }

  /**
   * Computes cosine similarity between two numeric vectors.
   */
  public static cosineSimilarity(vecA: number[], vecB: number[]): number {
    if (vecA.length !== vecB.length || vecA.length === 0) return 0;
    let dot = 0;
    let normA = 0;
    let normB = 0;
    for (let i = 0; i < vecA.length; i++) {
      const a = vecA[i] ?? 0;
      const b = vecB[i] ?? 0;
      dot += a * b;
      normA += a * a;
      normB += b * b;
    }
    if (normA === 0 || normB === 0) return 0;
    return dot / (Math.sqrt(normA) * Math.sqrt(normB));
  }
}
