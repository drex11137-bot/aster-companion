/**
 * Aster Companion Backend - Action Risk Classification Engine
 * Classifies all agentic actions into four strict tiers:
 * 1. read_only: Auto-permitted (no external state mutation)
 * 2. reversible: Auto-permitted with logged undo capability
 * 3. consequential: Requires explicit user confirmation
 * 4. irreversible: Requires strong biometric / WebAuthn confirmation
 */

import { ActionDefinition, ActionRiskLevel } from '../types/action.js';

export class ActionRiskClassifier {
  private static readonly ACTION_REGISTRY = new Map<string, ActionDefinition>([
    // Tier 1: Read-Only Actions
    [
      'search_photos',
      {
        name: 'search_photos',
        category: 'photos',
        riskLevel: 'read_only',
        description: 'Search user photo library by keyword, location, or visual description',
        parametersSchema: { query: 'string' },
        supportsUndo: false,
        requiresBiometric: false,
      },
    ],
    [
      'view_calendar_events',
      {
        name: 'view_calendar_events',
        category: 'calendar',
        riskLevel: 'read_only',
        description: 'Read upcoming events on user calendar',
        parametersSchema: { startDate: 'string', endDate: 'string' },
        supportsUndo: false,
        requiresBiometric: false,
      },
    ],
    [
      'search_shopify_products',
      {
        name: 'search_shopify_products',
        category: 'commerce',
        riskLevel: 'read_only',
        description: 'Search Shopify store catalog for products and prices',
        parametersSchema: { query: 'string' },
        supportsUndo: false,
        requiresBiometric: false,
      },
    ],
    [
      'read_contact',
      {
        name: 'read_contact',
        category: 'contacts',
        riskLevel: 'read_only',
        description: 'Read contact information from address book',
        parametersSchema: { name: 'string' },
        supportsUndo: false,
        requiresBiometric: false,
      },
    ],

    // Tier 2: Reversible Actions (Auto-permitted, logged with undo capability)
    [
      'create_reminder_draft',
      {
        name: 'create_reminder_draft',
        category: 'device',
        riskLevel: 'reversible',
        description: 'Create a draft reminder in local or cloud task list',
        parametersSchema: { title: 'string', dueTime: 'string' },
        supportsUndo: true,
        requiresBiometric: false,
      },
    ],
    [
      'draft_calendar_event',
      {
        name: 'draft_calendar_event',
        category: 'calendar',
        riskLevel: 'reversible',
        description: 'Create a tentative calendar entry',
        parametersSchema: { title: 'string', start: 'string', end: 'string' },
        supportsUndo: true,
        requiresBiometric: false,
      },
    ],
    [
      'save_bookmark',
      {
        name: 'save_bookmark',
        category: 'search',
        riskLevel: 'reversible',
        description: 'Save a link or product to reading/shopping list',
        parametersSchema: { url: 'string', title: 'string' },
        supportsUndo: true,
        requiresBiometric: false,
      },
    ],

    // Tier 3: Consequential Actions (Requires explicit user confirmation)
    [
      'send_email',
      {
        name: 'send_email',
        category: 'email',
        riskLevel: 'consequential',
        description: 'Dispatch an email message from user connected Gmail',
        parametersSchema: { recipient: 'string', subject: 'string', body: 'string' },
        supportsUndo: false,
        requiresBiometric: false,
      },
    ],
    [
      'delete_contact',
      {
        name: 'delete_contact',
        category: 'contacts',
        riskLevel: 'consequential',
        description: 'Permanently remove a contact from address book',
        parametersSchema: { contactId: 'string' },
        supportsUndo: false,
        requiresBiometric: false,
      },
    ],
    [
      'cancel_calendar_event',
      {
        name: 'cancel_calendar_event',
        category: 'calendar',
        riskLevel: 'consequential',
        description: 'Cancel an existing event and notify invitees',
        parametersSchema: { eventId: 'string' },
        supportsUndo: false,
        requiresBiometric: false,
      },
    ],
    [
      'share_memory_between_profiles',
      {
        name: 'share_memory_between_profiles',
        category: 'device',
        riskLevel: 'consequential',
        description: 'Explicitly copy a private memory item to another companion profile',
        parametersSchema: { memoryId: 'string', targetProfileId: 'string' },
        supportsUndo: true,
        requiresBiometric: false,
      },
    ],

    // Tier 4: Irreversible Actions (Requires biometric / strong authorization)
    [
      'execute_shopify_purchase',
      {
        name: 'execute_shopify_purchase',
        category: 'commerce',
        riskLevel: 'irreversible',
        description: 'Authorize and charge payment for a Shopify order',
        parametersSchema: { productId: 'string', amount: 'number', currency: 'string' },
        supportsUndo: false,
        requiresBiometric: true,
      },
    ],
    [
      'delete_companion_profile',
      {
        name: 'delete_companion_profile',
        category: 'device',
        riskLevel: 'irreversible',
        description: 'Permanently erase a companion profile and all isolated memories',
        parametersSchema: { profileId: 'string' },
        supportsUndo: false,
        requiresBiometric: true,
      },
    ],
  ]);

  /**
   * Classify an action by its registered name or default to consequential for unknown tools.
   */
  public static classify(actionName: string): ActionDefinition {
    const existing = this.ACTION_REGISTRY.get(actionName);
    if (existing) {
      return existing;
    }

    // Default-deny policy: Unrecognized external actions default to consequential risk
    return {
      name: actionName,
      category: 'device',
      riskLevel: 'consequential',
      description: `Unrecognized custom action: ${actionName}`,
      parametersSchema: {},
      supportsUndo: false,
      requiresBiometric: false,
    };
  }

  public static isReadOnly(actionName: string): boolean {
    return this.classify(actionName).riskLevel === 'read_only';
  }

  public static isReversible(actionName: string): boolean {
    return this.classify(actionName).riskLevel === 'reversible';
  }

  public static requiresConfirmation(actionName: string): boolean {
    const level = this.classify(actionName).riskLevel;
    return level === 'consequential' || level === 'irreversible';
  }

  public static requiresBiometric(actionName: string): boolean {
    return this.classify(actionName).riskLevel === 'irreversible';
  }
}
