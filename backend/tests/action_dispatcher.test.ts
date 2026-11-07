import { describe, it, expect, beforeEach } from 'vitest';
import { ActionDispatcher } from '../src/actions/action_dispatcher.js';
import { ActionRiskClassifier } from '../src/actions/risk_classifier.js';

describe('ActionDispatcher & Risk Classification Engine', () => {
  let dispatcher: ActionDispatcher;

  beforeEach(() => {
    dispatcher = new ActionDispatcher();
  });

  describe('Risk Classification Hierarchy', () => {
    it('should correctly classify the 4 operational risk tiers', () => {
      expect(ActionRiskClassifier.classify('search_photos').riskLevel).toBe('read_only');
      expect(ActionRiskClassifier.classify('view_calendar_events').riskLevel).toBe('read_only');

      expect(ActionRiskClassifier.classify('create_reminder_draft').riskLevel).toBe('reversible');
      expect(ActionRiskClassifier.classify('draft_calendar_event').riskLevel).toBe('reversible');

      expect(ActionRiskClassifier.classify('send_email').riskLevel).toBe('consequential');
      expect(ActionRiskClassifier.classify('delete_contact').riskLevel).toBe('consequential');

      expect(ActionRiskClassifier.classify('execute_shopify_purchase').riskLevel).toBe('irreversible');
      expect(ActionRiskClassifier.classify('delete_companion_profile').riskLevel).toBe('irreversible');
    });
  });

  describe('Read-Only Actions', () => {
    it('should automatically permit read-only actions without confirmation or biometric auth', async () => {
      const result = await dispatcher.dispatchAction({
        actionName: 'search_photos',
        profileId: 'prof_read',
        userId: 'user_read',
        deviceId: 'dev_1',
        idempotencyKey: 'idemp_photo_1',
        arguments: { query: 'coffee' },
      });

      expect(result.status).toBe('EXECUTED');
      expect(result.riskLevel).toBe('read_only');
      expect(result.cached).toBe(false);
      expect(result.verification.status).toBe('VERIFIED');
      expect((result.executionOutput?.['foundItems'] as any[]).length).toBeGreaterThan(0);
    });
  });

  describe('Reversible Actions & Undo Capability', () => {
    it('should automatically execute reversible actions, log undo token, and support rollback', async () => {
      const result = await dispatcher.dispatchAction({
        actionName: 'create_reminder_draft',
        profileId: 'prof_rev',
        userId: 'user_rev',
        deviceId: 'dev_1',
        idempotencyKey: 'idemp_rem_1',
        arguments: { title: 'Book dentist appointment', dueTime: 'Tomorrow 2 PM' },
      });

      expect(result.status).toBe('EXECUTED');
      expect(result.riskLevel).toBe('reversible');
      expect(result.undoable).toBe(true);
      expect(result.undoToken).toBe(result.actionId);
      expect(result.verification.status).toBe('VERIFIED');

      // Execute Rollback / Undo
      const undoResult = await dispatcher.undoAction(result.actionId, 'prof_rev');
      expect(undoResult.undone).toBe(true);
      expect(undoResult.restoredStateSummary).toContain('Successfully reversed create_reminder_draft');

      // Attempting cross-profile rollback must be rejected
      const illegalUndo = await dispatcher.undoAction(result.actionId, 'prof_unauthorized');
      expect(illegalUndo.undone).toBe(false);
      expect(illegalUndo.error).toContain('Profile mismatch');
    });
  });

  describe('Consequential Actions & User Confirmation Gates', () => {
    it('should halt consequential actions when unconfirmed and provide a confirmation preview', async () => {
      const result = await dispatcher.dispatchAction({
        actionName: 'send_email',
        profileId: 'prof_mail',
        userId: 'user_mail',
        deviceId: 'dev_1',
        idempotencyKey: 'idemp_mail_unconfirmed',
        arguments: {
          recipient: 'partner@example.com',
          subject: 'Flight itinerary',
          body: 'Here is the flight booking details.',
        },
        userConfirmed: false,
      });

      expect(result.status).toBe('PENDING_USER_CONFIRMATION');
      expect(result.riskLevel).toBe('consequential');
      expect(result.preview).toBeDefined();
      expect(result.preview?.confirmationPrompt).toContain('partner@example.com');
      expect(result.preview?.requiresConfirmation).toBe(true);
      expect(result.executionOutput).toBeUndefined();
    });

    it('should execute consequential actions once user confirms explicitly', async () => {
      const result = await dispatcher.dispatchAction({
        actionName: 'send_email',
        profileId: 'prof_mail',
        userId: 'user_mail',
        deviceId: 'dev_1',
        idempotencyKey: 'idemp_mail_confirmed',
        arguments: {
          recipient: 'partner@example.com',
          subject: 'Flight itinerary',
          body: 'Here is the flight booking details.',
        },
        userConfirmed: true,
      });

      expect(result.status).toBe('EXECUTED');
      expect(result.verification.status).toBe('VERIFIED');
      expect(result.executionOutput?.['sentStatus']).toBe('delivered');
      expect(result.executionOutput?.['messageId']).toBeDefined();
    });
  });

  describe('Irreversible / High-Risk Actions & Biometric Authentication', () => {
    it('should require strong biometric authorization for irreversible purchases', async () => {
      const resultNoBio = await dispatcher.dispatchAction({
        actionName: 'execute_shopify_purchase',
        profileId: 'prof_shop',
        userId: 'user_shop',
        deviceId: 'dev_1',
        idempotencyKey: 'idemp_shop_nobio',
        arguments: { productId: 'prod_sneaker_1', amount: 129.99, currency: 'USD' },
      });

      expect(resultNoBio.status).toBe('PENDING_BIOMETRIC_AUTH');
      expect(resultNoBio.preview?.requiresBiometric).toBe(true);
      expect(resultNoBio.preview?.confirmationPrompt).toContain('Confirm biometric authorization');

      // Provide valid WebAuthn/Passkey biometric token
      const resultWithBio = await dispatcher.dispatchAction({
        actionName: 'execute_shopify_purchase',
        profileId: 'prof_shop',
        userId: 'user_shop',
        deviceId: 'dev_1',
        idempotencyKey: 'idemp_shop_withbio',
        arguments: { productId: 'prod_sneaker_1', amount: 129.99, currency: 'USD' },
        biometricToken: 'bio_passkey_assertion_sig987654321',
      });

      expect(resultWithBio.status).toBe('EXECUTED');
      expect(resultWithBio.verification.status).toBe('VERIFIED');
      expect(resultWithBio.executionOutput?.['transactionStatus']).toBe('settled');
      expect(resultWithBio.executionOutput?.['orderId']).toBeDefined();
    });
  });

  describe('Idempotency Enforcement', () => {
    it('should enforce idempotency by returning cached result without re-executing', async () => {
      const req = {
        actionName: 'create_reminder_draft',
        profileId: 'prof_idem',
        userId: 'user_idem',
        deviceId: 'dev_1',
        idempotencyKey: 'idemp_unique_key_4455',
        arguments: { title: 'Pick up parcel' },
      };

      const firstCall = await dispatcher.dispatchAction(req);
      expect(firstCall.status).toBe('EXECUTED');
      expect(firstCall.cached).toBe(false);

      const secondCall = await dispatcher.dispatchAction(req);
      expect(secondCall.status).toBe('EXECUTED');
      expect(secondCall.cached).toBe(true);
      expect(secondCall.actionId).toBe(firstCall.actionId);
      expect(secondCall.executionOutput).toEqual(firstCall.executionOutput);
    });
  });
});
