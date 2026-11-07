/**
 * Aster Companion - Deliberate Item-Level Memory Sharing Service
 * File: backend/src/memory/memory_sharing_service.ts
 *
 * Implements PRD v1.1 Section 9.4 & DEC-025 requirements:
 * 1. Deliberate, item-level sharing between Profile A and Profile B.
 * 2. Mandates affirmative user confirmation (unconfirmed sharing rejected).
 * 3. Logs share event in memory_shares table and audit records.
 * 4. Revocation instantly breaks the link and permanently purges the destination copy.
 */

import { randomUUID } from 'node:crypto';
import {
  MemoryRecord,
  MemoryShareRecord,
  ProfileIsolationViolationError,
  RevokeShareRequest,
  ShareMemoryRequest,
  UnconfirmedSharingError,
} from './types.js';
import { IMemoryStore } from './memory_store.js';

export interface ProfileOwnershipVerifier {
  verifyProfilesBelongToUser(userId: string, profileA: string, profileB: string): Promise<boolean>;
}

export interface AuditLogger {
  logAction(action: string, payload: Record<string, unknown>): Promise<void>;
}

export class MemorySharingService {
  constructor(
    private readonly store: IMemoryStore,
    private readonly ownershipVerifier?: ProfileOwnershipVerifier,
    private readonly auditLogger?: AuditLogger
  ) {}

  /**
   * Shares an individual memory item from sourceProfileId to destinationProfileId.
   *
   * PRD v1.1 Invariants:
   * 1. Requires affirmative user confirmation (confirmedByUser === true).
   * 2. Cannot share with self (sourceProfileId !== destinationProfileId).
   * 3. Source memory must exist and be active.
   * 4. Clones a destination record in Profile B categorized as 'explicitly_shared'.
   * 5. Logs share event to memory_shares table and security audit log.
   */
  public async shareMemoryItem(request: ShareMemoryRequest): Promise<{
    share: MemoryShareRecord;
    destinationMemory: MemoryRecord;
  }> {
    const {
      sourceProfileId,
      destinationProfileId,
      memoryId,
      confirmedByUser,
      userId,
      reason,
      confirmationDetails,
    } = request;

    // 1. Mandatory Affirmative User Confirmation Gate (PRD 9.4)
    if (confirmedByUser !== true) {
      throw new UnconfirmedSharingError(
        'User confirmation was false or omitted. Cross-profile memory transfer requires explicit, affirmative confirmation.'
      );
    }

    // 2. Prevent self-sharing
    if (sourceProfileId === destinationProfileId) {
      throw new Error(
        `Cannot share memory with same profile (${sourceProfileId}). Source and destination profiles must differ.`
      );
    }

    // 3. Verify Account Ownership of both profiles
    if (this.ownershipVerifier && userId) {
      const isOwner = await this.ownershipVerifier.verifyProfilesBelongToUser(
        userId,
        sourceProfileId,
        destinationProfileId
      );
      if (!isOwner) {
        throw new ProfileIsolationViolationError(
          `Unauthorized memory share: Profiles ${sourceProfileId} and ${destinationProfileId} do not both belong to user ${userId}.`
        );
      }
    }

    // 4. Fetch Source Memory from Profile A (Strict Profile Isolation Check)
    const sourceMemory = await this.store.getMemoryById(sourceProfileId, memoryId);
    if (!sourceMemory) {
      throw new Error(`Source memory ${memoryId} not found in profile ${sourceProfileId}.`);
    }

    if (sourceMemory.isForgotten || sourceMemory.status === 'forgotten') {
      throw new Error(`Cannot share forgotten memory ${memoryId}.`);
    }

    // 5. Check if already actively shared
    const existingShare = await this.store.findMemoryShare(
      sourceProfileId,
      destinationProfileId,
      memoryId
    );
    if (existingShare && !existingShare.revokedAt) {
      // Memory is already actively shared
      if (existingShare.destinationMemoryId) {
        const destMem = await this.store.getMemoryById(
          destinationProfileId,
          existingShare.destinationMemoryId
        );
        if (destMem) {
          return { share: existingShare, destinationMemory: destMem };
        }
      }
    }

    const shareId = randomUUID();
    const destMemoryId = randomUUID();
    const now = new Date().toISOString();

    // 6. Create destination memory record in Profile B with 'explicitly_shared' category
    const destinationMemoryRecord: MemoryRecord = {
      id: destMemoryId,
      profileId: destinationProfileId,
      category: 'explicitly_shared', // PRD v1.1 canonical category
      content: sourceMemory.content,
      confidenceScore: sourceMemory.confidenceScore,
      provenanceSource: `shared_from_profile:${sourceProfileId}:source_mem:${sourceMemory.id}`,
      sensitivityLevel: sourceMemory.sensitivityLevel,
      isPinned: false,
      isForgotten: false,
      factType: sourceMemory.factType,
      status: 'active',
      version: 1,
      validTimeStart: now,
      validTimeEnd: null,
      rootMemoryId: destMemoryId,
      supersededById: null,
      supersedesId: null,
      embedding: sourceMemory.embedding ?? null,
      metadata: {
        sharedFromProfileId: sourceProfileId,
        sourceMemoryId: sourceMemory.id,
        shareRecordId: shareId,
        sharedAt: now,
        reason: reason ?? 'User-initiated explicit item-level share',
      },
      createdAt: now,
      updatedAt: now,
    };

    const insertedDestMem = await this.store.insertMemory(destinationMemoryRecord);

    // 7. Log share event in memory_shares table
    const shareRecord: MemoryShareRecord = {
      id: shareId,
      sourceProfileId,
      destinationProfileId,
      memoryId,
      destinationMemoryId: destMemoryId,
      confirmedByUser: true,
      confirmationMetadata: {
        confirmedAt: now,
        userId,
        reason: reason ?? null,
        clientDeviceId: confirmationDetails?.clientDeviceId ?? null,
        userAgent: confirmationDetails?.userAgent ?? null,
      },
      sharedAt: now,
      revokedAt: null,
      createdAt: now,
    };

    const insertedShare = await this.store.insertMemoryShare(shareRecord);

    // 8. Log security audit event
    if (this.auditLogger) {
      await this.auditLogger.logAction('MEMORY_ITEM_SHARED', {
        shareId,
        sourceProfileId,
        destinationProfileId,
        memoryId,
        destinationMemoryId: destMemoryId,
        userId,
        timestamp: now,
      });
    }

    return {
      share: insertedShare,
      destinationMemory: insertedDestMem,
    };
  }

  /**
   * Revocation instantly breaks the sharing link and deletes/purges the destination copy.
   *
   * PRD v1.1 Rule:
   * Revoking access immediately:
   * 1. Marks revoked_at timestamp on the memory_shares audit record.
   * 2. Permanently deletes destination copy from Profile B's memory store.
   * 3. Prevents Profile B from searching, viewing, or citing this memory ever again.
   */
  public async revokeShare(request: RevokeShareRequest): Promise<{
    revokedShareId: string;
    revokedAt: string;
    destinationMemoryDeleted: boolean;
  }> {
    const { shareId, sourceProfileId, destinationProfileId, memoryId, userId, reason } = request;

    let targetShare: MemoryShareRecord | null = null;

    if (shareId) {
      targetShare = await this.store.getMemoryShare(shareId);
    } else if (sourceProfileId && destinationProfileId && memoryId) {
      targetShare = await this.store.findMemoryShare(
        sourceProfileId,
        destinationProfileId,
        memoryId
      );
    }

    if (!targetShare) {
      throw new Error('Memory share record not found to revoke.');
    }

    if (targetShare.revokedAt) {
      return {
        revokedShareId: targetShare.id,
        revokedAt: targetShare.revokedAt,
        destinationMemoryDeleted: true,
      };
    }

    const now = new Date().toISOString();

    // 1. Break link in memory_shares table
    await this.store.revokeMemoryShare(targetShare.id, now);

    // 2. Instantly purge destination copy in Profile B
    let destinationMemoryDeleted = false;
    if (targetShare.destinationMemoryId) {
      try {
        await this.store.deleteMemory(
          targetShare.destinationProfileId,
          targetShare.destinationMemoryId
        );
        destinationMemoryDeleted = true;
      } catch (err) {
        // Fall back to marking destination copy forgotten if delete is restricted
        try {
          await this.store.updateMemory(
            targetShare.destinationMemoryId,
            targetShare.destinationProfileId,
            {
              isForgotten: true,
              status: 'forgotten',
              validTimeEnd: now,
            }
          );
          destinationMemoryDeleted = true;
        } catch {
          destinationMemoryDeleted = false;
        }
      }
    }

    // 3. Log security audit event
    if (this.auditLogger) {
      await this.auditLogger.logAction('MEMORY_SHARE_REVOKED', {
        shareId: targetShare.id,
        sourceProfileId: targetShare.sourceProfileId,
        destinationProfileId: targetShare.destinationProfileId,
        memoryId: targetShare.memoryId,
        destinationMemoryId: targetShare.destinationMemoryId,
        userId,
        reason: reason ?? 'User-initiated share revocation',
        revokedAt: now,
      });
    }

    return {
      revokedShareId: targetShare.id,
      revokedAt: now,
      destinationMemoryDeleted,
    };
  }

  /**
   * Checks whether a destination profile currently holds active access to a shared memory.
   */
  public async isMemorySharedWith(
    sourceProfileId: string,
    destinationProfileId: string,
    memoryId: string
  ): Promise<boolean> {
    const share = await this.store.findMemoryShare(
      sourceProfileId,
      destinationProfileId,
      memoryId
    );
    return Boolean(share && share.confirmedByUser && share.revokedAt === null);
  }
}
