/**
 * Aster Companion - Memory Store Interface & Implementations
 * File: backend/src/memory/memory_store.ts
 *
 * Provides database abstraction for Supabase pgvector operations
 * and an isolated in-memory implementation for unit testing and deterministic verification.
 */

import { SupabaseClient } from '@supabase/supabase-js';
import {
  MemoryRecord,
  MemoryQueryOptions,
  SemanticSearchOptions,
  MemoryShareRecord,
  ProfileIsolationViolationError,
} from './types.js';

export interface MemoryWithSimilarity {
  record: MemoryRecord;
  similarity: number;
}

export interface IMemoryStore {
  insertMemory(record: MemoryRecord): Promise<MemoryRecord>;
  updateMemory(id: string, profileId: string, updates: Partial<MemoryRecord>): Promise<MemoryRecord>;
  getMemoryById(profileId: string, id: string): Promise<MemoryRecord | null>;
  listMemories(profileId: string, options?: MemoryQueryOptions): Promise<MemoryRecord[]>;
  supersedeMemory(oldId: string, profileId: string, newId: string, validTimeEnd: string): Promise<void>;
  searchByVector(
    profileId: string,
    queryEmbedding: number[],
    options: SemanticSearchOptions
  ): Promise<MemoryWithSimilarity[]>;
  insertMemoryShare(share: MemoryShareRecord): Promise<MemoryShareRecord>;
  getMemoryShare(shareId: string): Promise<MemoryShareRecord | null>;
  findMemoryShare(sourceProfileId: string, destinationProfileId: string, memoryId: string): Promise<MemoryShareRecord | null>;
  revokeMemoryShare(shareId: string, revokedAt: string): Promise<void>;
  deleteMemory(profileId: string, memoryId: string): Promise<void>;
  getLineage(rootMemoryId: string, profileId: string): Promise<MemoryRecord[]>;
}

// ============================================================================
// Math Utilities for Vector Similarity (Cosine Similarity & Distance)
// ============================================================================

export function computeCosineSimilarity(a: number[], b: number[]): number {
  if (a.length !== b.length || a.length === 0) return 0;
  let dotProduct = 0;
  let normA = 0;
  let normB = 0;
  for (let i = 0; i < a.length; i++) {
    const valA = a[i] ?? 0;
    const valB = b[i] ?? 0;
    dotProduct += valA * valB;
    normA += valA * valA;
    normB += valB * valB;
  }
  if (normA === 0 || normB === 0) return 0;
  const similarity = dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
  // Clamp between -1.0 and 1.0 to handle floating point imprecision
  return Math.max(-1.0, Math.min(1.0, similarity));
}

// ============================================================================
// In-Memory Implementation (For Testing and Isolated Execution)
// ============================================================================

export class InMemoryMemoryStore implements IMemoryStore {
  private memories: Map<string, MemoryRecord> = new Map();
  private shares: Map<string, MemoryShareRecord> = new Map();

  public async insertMemory(record: MemoryRecord): Promise<MemoryRecord> {
    const cloned = { ...record };
    this.memories.set(cloned.id, cloned);
    return { ...cloned };
  }

  public async updateMemory(
    id: string,
    profileId: string,
    updates: Partial<MemoryRecord>
  ): Promise<MemoryRecord> {
    const existing = this.memories.get(id);
    if (!existing) {
      throw new Error(`Memory with ID ${id} not found.`);
    }
    if (existing.profileId !== profileId) {
      throw new ProfileIsolationViolationError(
        `Profile isolation error: Cannot update memory ${id} belonging to profile ${existing.profileId} from profile ${profileId}`
      );
    }

    const updated: MemoryRecord = {
      ...existing,
      ...updates,
      updatedAt: new Date().toISOString(),
    };
    this.memories.set(id, updated);
    return { ...updated };
  }

  public async getMemoryById(profileId: string, id: string): Promise<MemoryRecord | null> {
    const record = this.memories.get(id);
    if (!record) return null;
    if (record.profileId !== profileId) {
      // Profile isolation: return null if not matching profile
      return null;
    }
    return { ...record };
  }

  public async listMemories(
    profileId: string,
    options: MemoryQueryOptions = {}
  ): Promise<MemoryRecord[]> {
    const results: MemoryRecord[] = [];

    for (const record of this.memories.values()) {
      // Profile Isolation Filter
      if (record.profileId !== profileId) continue;

      // Filter forgotten
      if (!options.includeForgotten && record.isForgotten) continue;

      // Filter superseded
      if (!options.includeSuperseded && record.status === 'superseded') continue;

      // Filter tentative
      if (!options.includeTentative && record.status === 'tentative_inference') continue;

      // Filter category
      if (options.category && record.category !== options.category) continue;
      if (options.categories && !options.categories.includes(record.category)) continue;

      // Filter min confidence
      if (options.minConfidence !== undefined && record.confidenceScore < options.minConfidence) continue;

      // Filter pinned
      if (options.isPinned !== undefined && record.isPinned !== options.isPinned) continue;

      // Point-in-time temporal filter
      if (options.asOfTimestamp) {
        const asOf = new Date(options.asOfTimestamp).getTime();
        const start = new Date(record.validTimeStart).getTime();
        const end = record.validTimeEnd ? new Date(record.validTimeEnd).getTime() : Infinity;
        if (asOf < start || asOf >= end) continue;
      }

      results.push({ ...record });
    }

    // Sort by created_at DESC
    results.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

    // Apply offset and limit
    const offset = options.offset ?? 0;
    const limit = options.limit ?? results.length;
    return results.slice(offset, offset + limit);
  }

  public async supersedeMemory(
    oldId: string,
    profileId: string,
    newId: string,
    validTimeEnd: string
  ): Promise<void> {
    const old = this.memories.get(oldId);
    if (!old) return;
    if (old.profileId !== profileId) {
      throw new ProfileIsolationViolationError(`Cross-profile supersession attempted.`);
    }

    old.status = 'superseded';
    old.validTimeEnd = validTimeEnd;
    old.supersededById = newId;
    old.updatedAt = new Date().toISOString();
  }

  public async searchByVector(
    profileId: string,
    queryEmbedding: number[],
    options: SemanticSearchOptions
  ): Promise<MemoryWithSimilarity[]> {
    const minSim = options.minSimilarity ?? 0.0;
    const limit = options.matchLimit ?? 10;
    const matches: MemoryWithSimilarity[] = [];

    // Also collect unrevoked shared memory IDs if includeShared is requested
    const confirmedSharedMemoryIds = new Set<string>();
    if (options.includeShared) {
      for (const share of this.shares.values()) {
        if (
          share.destinationProfileId === profileId &&
          share.confirmedByUser &&
          !share.revokedAt
        ) {
          confirmedSharedMemoryIds.add(share.memoryId);
        }
      }
    }

    for (const record of this.memories.values()) {
      // Profile isolation: strictly enforce profileId or confirmed shared memory
      const isDirectMatch = record.profileId === profileId;
      const isSharedMatch = confirmedSharedMemoryIds.has(record.id);

      if (!isDirectMatch && !isSharedMatch) continue;

      // Must not be forgotten
      if (record.isForgotten) continue;

      // By default skip superseded records in semantic retrieval
      if (record.status === 'superseded') continue;

      // Tentative inference check
      if (!options.includeTentative && record.status === 'tentative_inference') continue;

      // Category filter
      if (options.categories && !options.categories.includes(record.category)) continue;

      // Must have embedding
      if (!record.embedding || record.embedding.length === 0) continue;

      const similarity = computeCosineSimilarity(queryEmbedding, record.embedding);

      if (similarity >= minSim) {
        matches.push({
          record: { ...record },
          similarity,
        });
      }
    }

    // Sort descending by similarity score
    matches.sort((a, b) => b.similarity - a.similarity);
    return matches.slice(0, limit);
  }

  public async insertMemoryShare(share: MemoryShareRecord): Promise<MemoryShareRecord> {
    const cloned = { ...share };
    this.shares.set(cloned.id, cloned);
    return { ...cloned };
  }

  public async getMemoryShare(shareId: string): Promise<MemoryShareRecord | null> {
    const s = this.shares.get(shareId);
    return s ? { ...s } : null;
  }

  public async findMemoryShare(
    sourceProfileId: string,
    destinationProfileId: string,
    memoryId: string
  ): Promise<MemoryShareRecord | null> {
    for (const share of this.shares.values()) {
      if (
        share.sourceProfileId === sourceProfileId &&
        share.destinationProfileId === destinationProfileId &&
        share.memoryId === memoryId &&
        share.revokedAt === null
      ) {
        return { ...share };
      }
    }
    return null;
  }

  public async revokeMemoryShare(shareId: string, revokedAt: string): Promise<void> {
    const share = this.shares.get(shareId);
    if (share) {
      share.revokedAt = revokedAt;
    }
  }

  public async deleteMemory(profileId: string, memoryId: string): Promise<void> {
    const existing = this.memories.get(memoryId);
    if (!existing) return;
    if (existing.profileId !== profileId) {
      throw new ProfileIsolationViolationError(`Cannot delete memory belonging to another profile.`);
    }
    this.memories.delete(memoryId);
  }

  public async getLineage(rootMemoryId: string, profileId: string): Promise<MemoryRecord[]> {
    const lineage: MemoryRecord[] = [];
    for (const record of this.memories.values()) {
      if (record.profileId === profileId) {
        if (record.id === rootMemoryId || record.rootMemoryId === rootMemoryId) {
          lineage.push({ ...record });
        }
      }
    }
    return lineage.sort((a, b) => a.version - b.version);
  }

  // Debug helper to clear in-memory database
  public clear(): void {
    this.memories.clear();
    this.shares.clear();
  }
}

// ============================================================================
// Supabase pgvector Implementation
// ============================================================================

export class SupabaseMemoryStore implements IMemoryStore {
  constructor(private readonly supabase: SupabaseClient) {}

  public async insertMemory(record: MemoryRecord): Promise<MemoryRecord> {
    const dbPayload = {
      id: record.id,
      profile_id: record.profileId,
      memory_category: record.category,
      content: record.content,
      confidence_score: record.confidenceScore,
      provenance_source: record.provenanceSource,
      sensitivity_level: record.sensitivityLevel,
      fact_type: record.factType,
      status: record.status,
      version: record.version,
      valid_time_start: record.validTimeStart,
      valid_time_end: record.validTimeEnd,
      root_memory_id: record.rootMemoryId,
      superseded_by_id: record.supersededById,
      supersedes_id: record.supersedesId,
      is_pinned: record.isPinned,
      is_forgotten: record.isForgotten,
      embedding: record.embedding ? JSON.stringify(record.embedding) : null,
      metadata: record.metadata ?? {},
      created_at: record.createdAt,
      updated_at: record.updatedAt,
    };

    const { data, error } = await this.supabase
      .from('memories')
      .insert(dbPayload)
      .select()
      .single();

    if (error || !data) {
      throw new Error(`Failed to insert memory into Supabase: ${error?.message || 'No data returned'}`);
    }

    return this.mapDbRowToRecord(data);
  }

  public async updateMemory(
    id: string,
    profileId: string,
    updates: Partial<MemoryRecord>
  ): Promise<MemoryRecord> {
    const dbUpdates: Record<string, unknown> = {
      updated_at: new Date().toISOString(),
    };

    if (updates.content !== undefined) dbUpdates['content'] = updates.content;
    if (updates.category !== undefined) dbUpdates['memory_category'] = updates.category;
    if (updates.confidenceScore !== undefined) dbUpdates['confidence_score'] = updates.confidenceScore;
    if (updates.provenanceSource !== undefined) dbUpdates['provenance_source'] = updates.provenanceSource;
    if (updates.sensitivityLevel !== undefined) dbUpdates['sensitivity_level'] = updates.sensitivityLevel;
    if (updates.isPinned !== undefined) dbUpdates['is_pinned'] = updates.isPinned;
    if (updates.isForgotten !== undefined) dbUpdates['is_forgotten'] = updates.isForgotten;
    if (updates.status !== undefined) dbUpdates['status'] = updates.status;
    if (updates.validTimeEnd !== undefined) dbUpdates['valid_time_end'] = updates.validTimeEnd;
    if (updates.supersededById !== undefined) dbUpdates['superseded_by_id'] = updates.supersededById;
    if (updates.embedding !== undefined) {
      dbUpdates['embedding'] = updates.embedding ? JSON.stringify(updates.embedding) : null;
    }
    if (updates.metadata !== undefined) dbUpdates['metadata'] = updates.metadata;

    const { data, error } = await this.supabase
      .from('memories')
      .update(dbUpdates)
      .eq('id', id)
      .eq('profile_id', profileId) // Profile Isolation Guard
      .select()
      .single();

    if (error || !data) {
      throw new Error(`Failed to update memory in Supabase: ${error?.message || 'Not found'}`);
    }

    return this.mapDbRowToRecord(data);
  }

  public async getMemoryById(profileId: string, id: string): Promise<MemoryRecord | null> {
    const { data, error } = await this.supabase
      .from('memories')
      .select('*')
      .eq('id', id)
      .eq('profile_id', profileId) // Strict Profile Isolation
      .maybeSingle();

    if (error) {
      throw new Error(`Error fetching memory from Supabase: ${error.message}`);
    }
    if (!data) return null;

    return this.mapDbRowToRecord(data);
  }

  public async listMemories(
    profileId: string,
    options: MemoryQueryOptions = {}
  ): Promise<MemoryRecord[]> {
    let query = this.supabase
      .from('memories')
      .select('*')
      .eq('profile_id', profileId); // Strict profile isolation filter

    if (!options.includeForgotten) {
      query = query.eq('is_forgotten', false);
    }

    if (!options.includeSuperseded) {
      query = query.neq('status', 'superseded');
    }

    if (!options.includeTentative) {
      query = query.neq('status', 'tentative_inference');
    }

    if (options.category) {
      query = query.eq('memory_category', options.category);
    }

    if (options.categories && options.categories.length > 0) {
      query = query.in('memory_category', options.categories);
    }

    if (options.minConfidence !== undefined) {
      query = query.gte('confidence_score', options.minConfidence);
    }

    if (options.isPinned !== undefined) {
      query = query.eq('is_pinned', options.isPinned);
    }

    query = query.order('created_at', { ascending: false });

    if (options.offset !== undefined) {
      query = query.range(options.offset, options.offset + (options.limit ?? 20) - 1);
    } else if (options.limit !== undefined) {
      query = query.limit(options.limit);
    }

    const { data, error } = await query;
    if (error) {
      throw new Error(`Failed to list memories from Supabase: ${error.message}`);
    }

    return (data || []).map((row) => this.mapDbRowToRecord(row));
  }

  public async supersedeMemory(
    oldId: string,
    profileId: string,
    newId: string,
    validTimeEnd: string
  ): Promise<void> {
    const { error } = await this.supabase
      .from('memories')
      .update({
        status: 'superseded',
        valid_time_end: validTimeEnd,
        superseded_by_id: newId,
        updated_at: new Date().toISOString(),
      })
      .eq('id', oldId)
      .eq('profile_id', profileId); // Strict profile isolation

    if (error) {
      throw new Error(`Failed to supersede memory: ${error.message}`);
    }
  }

  public async searchByVector(
    profileId: string,
    queryEmbedding: number[],
    options: SemanticSearchOptions
  ): Promise<MemoryWithSimilarity[]> {
    // Invoke stored procedure 'search_active_memories' or fallback to 'search_profile_memories'
    const matchCount = options.matchLimit ?? 10;
    const matchThreshold = options.minSimilarity ?? 0.0;
    const includeShared = options.includeShared ?? false;

    const { data, error } = await this.supabase.rpc('search_active_memories', {
      p_profile_id: profileId,
      p_query_embedding: queryEmbedding,
      p_match_threshold: matchThreshold,
      p_match_count: matchCount,
      p_include_shared: includeShared,
    });

    if (error) {
      // If RPC fails (e.g. extension not yet migrated), fall back to standard RPC or query
      const fallback = await this.supabase.rpc('search_profile_memories', {
        p_profile_id: profileId,
        p_query_embedding: queryEmbedding,
        p_match_threshold: matchThreshold,
        p_match_count: matchCount,
      });

      if (fallback.error) {
        throw new Error(`Vector similarity query failed: ${fallback.error.message}`);
      }

      return (fallback.data || []).map((row: any) => ({
        record: this.mapDbRowToRecord(row),
        similarity: Number(row.similarity ?? 0),
      }));
    }

    return (data || []).map((row: any) => ({
      record: this.mapDbRowToRecord(row),
      similarity: Number(row.similarity ?? 0),
    }));
  }

  public async insertMemoryShare(share: MemoryShareRecord): Promise<MemoryShareRecord> {
    const dbPayload = {
      id: share.id,
      source_profile_id: share.sourceProfileId,
      destination_profile_id: share.destinationProfileId,
      memory_id: share.memoryId,
      destination_memory_id: share.destinationMemoryId,
      confirmed_by_user: share.confirmedByUser,
      confirmation_metadata: share.confirmationMetadata,
      shared_at: share.sharedAt,
      revoked_at: share.revokedAt,
      created_at: share.createdAt,
    };

    const { data, error } = await this.supabase
      .from('memory_shares')
      .insert(dbPayload)
      .select()
      .single();

    if (error || !data) {
      throw new Error(`Failed to insert memory share in Supabase: ${error?.message}`);
    }

    return this.mapDbRowToShare(data);
  }

  public async getMemoryShare(shareId: string): Promise<MemoryShareRecord | null> {
    const { data, error } = await this.supabase
      .from('memory_shares')
      .select('*')
      .eq('id', shareId)
      .maybeSingle();

    if (error) throw new Error(`Failed to get memory share: ${error.message}`);
    if (!data) return null;

    return this.mapDbRowToShare(data);
  }

  public async findMemoryShare(
    sourceProfileId: string,
    destinationProfileId: string,
    memoryId: string
  ): Promise<MemoryShareRecord | null> {
    const { data, error } = await this.supabase
      .from('memory_shares')
      .select('*')
      .eq('source_profile_id', sourceProfileId)
      .eq('destination_profile_id', destinationProfileId)
      .eq('memory_id', memoryId)
      .is('revoked_at', null)
      .maybeSingle();

    if (error) throw new Error(`Failed to find memory share: ${error.message}`);
    if (!data) return null;

    return this.mapDbRowToShare(data);
  }

  public async revokeMemoryShare(shareId: string, revokedAt: string): Promise<void> {
    const { error } = await this.supabase
      .from('memory_shares')
      .update({ revoked_at: revokedAt })
      .eq('id', shareId);

    if (error) throw new Error(`Failed to revoke memory share: ${error.message}`);
  }

  public async deleteMemory(profileId: string, memoryId: string): Promise<void> {
    const { error } = await this.supabase
      .from('memories')
      .delete()
      .eq('id', memoryId)
      .eq('profile_id', profileId); // Strict profile isolation

    if (error) throw new Error(`Failed to delete memory: ${error.message}`);
  }

  public async getLineage(rootMemoryId: string, profileId: string): Promise<MemoryRecord[]> {
    const { data, error } = await this.supabase
      .from('memories')
      .select('*')
      .eq('profile_id', profileId)
      .or(`id.eq.${rootMemoryId},root_memory_id.eq.${rootMemoryId}`)
      .order('version', { ascending: true });

    if (error) throw new Error(`Failed to get memory lineage: ${error.message}`);

    return (data || []).map((row) => this.mapDbRowToRecord(row));
  }

  private mapDbRowToRecord(row: any): MemoryRecord {
    let embedding: number[] | null = null;
    if (row.embedding) {
      if (Array.isArray(row.embedding)) {
        embedding = row.embedding;
      } else if (typeof row.embedding === 'string') {
        try {
          embedding = JSON.parse(row.embedding);
        } catch {
          embedding = null;
        }
      }
    }

    return {
      id: row.id,
      profileId: row.profile_id,
      category: row.memory_category,
      content: row.content,
      confidenceScore: row.confidence_score,
      provenanceSource: row.provenance_source,
      sensitivityLevel: row.sensitivity_level ?? 'standard',
      isPinned: Boolean(row.is_pinned),
      isForgotten: Boolean(row.is_forgotten),
      factType: row.fact_type ?? 'explicit_fact',
      status: row.status ?? 'active',
      version: Number(row.version ?? 1),
      validTimeStart: row.valid_time_start ?? row.created_at,
      validTimeEnd: row.valid_time_end ?? null,
      rootMemoryId: row.root_memory_id ?? null,
      supersededById: row.superseded_by_id ?? null,
      supersedesId: row.supersedes_id ?? null,
      embedding,
      metadata: row.metadata ?? {},
      createdAt: row.created_at,
      updatedAt: row.updated_at,
    };
  }

  private mapDbRowToShare(row: any): MemoryShareRecord {
    return {
      id: row.id,
      sourceProfileId: row.source_profile_id,
      destinationProfileId: row.destination_profile_id,
      memoryId: row.memory_id,
      destinationMemoryId: row.destination_memory_id ?? null,
      confirmedByUser: Boolean(row.confirmed_by_user),
      confirmationMetadata: row.confirmation_metadata ?? {},
      sharedAt: row.shared_at,
      revokedAt: row.revoked_at ?? null,
      createdAt: row.created_at,
    };
  }
}
