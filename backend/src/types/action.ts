/**
 * Aster Companion Backend - Agentic Action Dispatcher Types
 * Risk Classification, Idempotency, User Confirmation, and Post-Action Verification
 */

export type ActionRiskLevel = 
  | 'read_only'       // Search photos, view calendar -> auto-permitted
  | 'reversible'      // Create draft reminder -> auto-permitted, logged with undo capability
  | 'consequential'   // Send email, delete contact -> requires explicit user confirmation
  | 'irreversible';   // Payment, Shopify purchase, delete profile -> requires biometric confirmation

export type ActionExecutionStatus = 
  | 'PENDING_USER_CONFIRMATION'
  | 'PENDING_BIOMETRIC_AUTH'
  | 'IN_PROGRESS'
  | 'EXECUTED'
  | 'FAILED'
  | 'REJECTED'
  | 'ROLLED_BACK';

export type PostActionVerificationStatus = 
  | 'VERIFIED'
  | 'VERIFICATION_FAILED'
  | 'UNVERIFIED'
  | 'NOT_APPLICABLE';

export interface ActionDefinition {
  name: string;
  category: 'calendar' | 'photos' | 'email' | 'contacts' | 'commerce' | 'device' | 'search';
  riskLevel: ActionRiskLevel;
  description: string;
  parametersSchema: Record<string, unknown>;
  supportsUndo: boolean;
  requiresBiometric: boolean;
}

export interface ActionDispatchRequest {
  actionName: string;
  profileId: string;
  userId: string;
  deviceId: string;
  idempotencyKey: string; // Mandatory idempotency key
  arguments: Record<string, unknown>;
  userConfirmed?: boolean;
  biometricToken?: string;
}

export interface ActionPreview {
  actionName: string;
  riskLevel: ActionRiskLevel;
  summary: string;
  affectedResources: string[];
  requiresConfirmation: boolean;
  requiresBiometric: boolean;
  parameters: Record<string, unknown>;
  confirmationPrompt: string;
  expiresAt: string; // ISO timestamp
}

export interface PostActionVerification {
  status: PostActionVerificationStatus;
  verifiedAt: string;
  verificationEvidence?: Record<string, unknown>;
  errorMessage?: string;
}

export interface ActionDispatchResult {
  actionId: string;
  actionName: string;
  riskLevel: ActionRiskLevel;
  status: ActionExecutionStatus;
  idempotencyKey: string;
  cached: boolean; // True if this was an idempotent return of a previously computed action
  preview?: ActionPreview;
  executionOutput?: Record<string, unknown>;
  error?: string;
  verification: PostActionVerification;
  undoable: boolean;
  undoToken?: string;
  executedAt?: string;
}

export interface ActionUndoResult {
  actionId: string;
  undone: boolean;
  restoredStateSummary: string;
  undoTimestamp: string;
  error?: string;
}
