/**
 * Aster Companion - External Integrations & OAuth Service
 * Test Suite
 * integrations.test.ts
 */

import { describe, it } from 'vitest';
import assert from 'node:assert/strict';

import {
  generateCodeVerifier,
  generateCodeChallenge,
  generatePKCEPair,
  verifyCodeChallenge,
  TokenEncryptionService,
  OAuthStateStore,
  TokenRotationManager,
  OAuthPKCEHandler,
  TokenReuseDetectedError,
  OAuthSecurityError,
} from '../oauth_pkce_handler';

import {
  GOOGLE_SCOPES,
  CASA_RESTRICTED_SCOPES,
  GooglePhotosService,
  GoogleDriveService,
  GmailService,
  GoogleCalendarService,
  GoogleContactsService,
  ApprovalRequiredError,
  ActionApprovalTicket,
} from '../google_integrations';

import {
  ShopifyStorefrontClient,
  ShopifyError,
  CartLineItemInput,
} from '../shopify_integration';

import {
  IntegrationManager,
  PROVIDER_REQUIRED_SCOPES,
} from '../integration_manager';

describe('OAuth 2.0 PKCE Handler (RFC 7636 & RFC 9700)', () => {
  it('should generate valid high-entropy code_verifier within length limits', () => {
    const verifier = generateCodeVerifier(64);
    assert.equal(verifier.length, 64);
    assert.match(verifier, /^[A-Za-z0-9\-._~]+$/);

    // Verify boundary constraints
    assert.throws(() => generateCodeVerifier(42), /INVALID_VERIFIER_LENGTH/);
    assert.throws(() => generateCodeVerifier(129), /INVALID_VERIFIER_LENGTH/);
  });

  it('should compute RFC 7636 S256 code_challenge and verify correctly', () => {
    const pkce = generatePKCEPair(64);
    assert.equal(pkce.codeChallengeMethod, 'S256');
    assert.ok(pkce.codeChallenge.length > 0);
    // Base64url should not have +, /, or =
    assert.doesNotMatch(pkce.codeChallenge, /[+/=]/);

    const isValid = verifyCodeChallenge(pkce.codeVerifier, pkce.codeChallenge);
    assert.equal(isValid, true);

    const isInvalid = verifyCodeChallenge(pkce.codeVerifier, 'tampered_challenge');
    assert.equal(isInvalid, false);
  });

  it('should generate and atomically validate/consume state against CSRF', () => {
    const store = new OAuthStateStore();
    const state = store.createState('prof_1', 'google_gmail', 'test_verifier', 'https://app/callback', ['email']);

    assert.ok(state.stateToken);
    assert.ok(state.nonce);
    assert.equal(state.profileId, 'prof_1');

    // Consuming state succeeds the first time
    const consumed = store.validateAndConsume(state.stateToken, state.nonce);
    assert.equal(consumed.profileId, 'prof_1');

    // Immediate replay must fail (preventing CSRF and replay)
    assert.throws(() => {
      store.validateAndConsume(state.stateToken);
    }, /INVALID_STATE/);
  });

  it('should encrypt and decrypt refresh tokens using AES-256-GCM', () => {
    const service = new TokenEncryptionService();
    const originalToken = 'rt_secret_google_refresh_token_xyz123';
    const aad = 'profile_1:google_drive';

    const encrypted = service.encrypt(originalToken, aad);
    assert.equal(encrypted.algorithm, 'aes-256-gcm');
    assert.equal(encrypted.iv.length, 24); // 12 bytes hex = 24 chars
    assert.equal(encrypted.authTag.length, 32); // 16 bytes hex = 32 chars
    assert.notEqual(encrypted.ciphertext, originalToken);

    const decrypted = service.decrypt(encrypted, aad);
    assert.equal(decrypted, originalToken);

    // Mismatched AAD must fail
    assert.throws(() => {
      service.decrypt(encrypted, 'profile_2:google_drive');
    }, /DECRYPTION_FAILED/);

    // Tampered ciphertext must fail auth tag validation
    const tampered = { ...encrypted, ciphertext: 'aa' + encrypted.ciphertext.substring(2) };
    assert.throws(() => {
      service.decrypt(tampered, aad);
    }, /DECRYPTION_FAILED/);
  });

  it('should handle token rotation and DETECT token reuse attack', () => {
    const encService = new TokenEncryptionService();
    const rotationManager = new TokenRotationManager(encService);

    // 1. Initial token
    const initial = rotationManager.registerInitialToken('profile_A', 'google_photos', 'initial_refresh_token_0');
    assert.equal(initial.generation, 0);

    // Active token decrypts correctly
    const active0 = rotationManager.getActiveDecryptedToken(initial.familyId);
    assert.equal(active0, 'initial_refresh_token_0');

    // 2. Normal rotation: Gen 0 -> Gen 1
    const rotated = rotationManager.rotateToken(
      'initial_refresh_token_0',
      'rotated_refresh_token_1',
      'profile_A',
      'google_photos'
    );
    assert.equal(rotated.generation, 1);
    assert.equal(rotationManager.getActiveDecryptedToken(initial.familyId), 'rotated_refresh_token_1');

    // 3. REUSE ATTACK: Attacker presents compromised predecessor token (Gen 0)
    assert.throws(() => {
      rotationManager.rotateToken(
        'initial_refresh_token_0',
        'attacker_token',
        'profile_A',
        'google_photos'
      );
    }, (err: unknown) => {
      return err instanceof TokenReuseDetectedError && err.generation === 0;
    });

    // 4. Family must now be completely revoked
    assert.throws(() => {
      rotationManager.getActiveDecryptedToken(initial.familyId);
    }, /FAMILY_REVOKED/);
  });

  it('should build proper OAuth authorization URL with PKCE parameters', () => {
    const handler = new OAuthPKCEHandler();
    const config = {
      providerId: 'google_gmail',
      clientId: 'google_client_id_test',
      authorizationEndpoint: 'https://accounts.google.com/o/oauth2/v2/auth',
      tokenEndpoint: 'https://oauth2.googleapis.com/token',
      defaultScopes: [GOOGLE_SCOPES.GMAIL_READONLY],
      redirectUri: 'https://aster.app/oauth/callback',
    };

    const res = handler.buildAuthorizationUrl(config, {
      profileId: 'prof_test',
    });

    const parsed = new URL(res.authorizationUrl);
    assert.equal(parsed.searchParams.get('client_id'), 'google_client_id_test');
    assert.equal(parsed.searchParams.get('response_type'), 'code');
    assert.equal(parsed.searchParams.get('code_challenge_method'), 'S256');
    assert.equal(parsed.searchParams.get('code_challenge'), res.codeChallenge);
    assert.equal(parsed.searchParams.get('access_type'), 'offline');
    assert.equal(parsed.searchParams.get('prompt'), 'consent');
  });
});

describe('Google Integrations', () => {
  it('should enforce minimal scopes on Google Photos Picker API', async () => {
    const mockFetch = (async (url: string, init?: RequestInit) => {
      if (url.includes('/sessions')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            id: 'sess_123',
            pickerUri: 'https://photos.google.com/picker/sess_123',
            expireTime: '2026-11-01T12:00:00Z',
            mediaItemsSet: false,
          }),
        } as unknown as Response;
      }
      if (url.includes('/mediaItems')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            mediaItems: [
              {
                id: 'media_1',
                filename: 'photo1.jpg',
                mimeType: 'image/jpeg',
                baseUrl: 'https://lh3.googleusercontent.com/test1',
              },
            ],
          }),
        } as unknown as Response;
      }
      throw new Error(`Unexpected url: ${url}`);
    }) as typeof fetch;

    const photos = new GooglePhotosService(mockFetch);
    const session = await photos.createPickerSession('mock_token');
    assert.equal(session.sessionId, 'sess_123');

    const items = await photos.getSessionMediaItems('mock_token', session.sessionId);
    assert.equal(items.length, 1);
    assert.equal(items[0].filename, 'photo1.jpg');
  });

  it('should parse Android SAF / Photo Picker content URIs safely', () => {
    const photos = new GooglePhotosService();
    const result = photos.parseAndroidPickerResult([
      { uri: 'content://media/picker/0/com.android.providers.media.photopicker/media/1000' },
    ]);
    assert.equal(result.length, 1);
    assert.ok(result[0].id.startsWith('android_picker_'));
    assert.equal(result[0].baseUrl, 'content://media/picker/0/com.android.providers.media.photopicker/media/1000');

    // Invalid non-content URI must fail
    assert.throws(() => {
      photos.parseAndroidPickerResult([{ uri: 'file:///private/unauthorized.jpg' }]);
    }, /Invalid Photo Picker URI/);
  });

  it('should enforce size guards on Google Drive file downloads', async () => {
    const mockFetch = (async (url: string) => {
      if (url.includes('fields=id,name,mimeType,size')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            id: 'file_large',
            name: 'massive.zip',
            size: 25 * 1024 * 1024, // 25MB exceeds 15MB limit
          }),
        } as unknown as Response;
      }
      throw new Error(`Unexpected url: ${url}`);
    }) as typeof fetch;

    const drive = new GoogleDriveService(mockFetch);
    await assert.rejects(
      async () => drive.getFileContent('mock_token', 'file_large'),
      /exceeds maximum safe download guard/
    );
  });

  it('should create Gmail drafts without approval, but MANDATE approval to send', async () => {
    let sendCalled = false;
    const mockFetch = (async (url: string, init?: RequestInit) => {
      if (url.includes('/drafts')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({ id: 'draft_456', message: { id: 'msg_789' } }),
        } as unknown as Response;
      }
      if (url.includes('/messages/send')) {
        sendCalled = true;
        return {
          ok: true,
          status: 200,
          json: async () => ({ id: 'sent_msg_1', threadId: 'thread_1' }),
        } as unknown as Response;
      }
      throw new Error(`Unexpected url: ${url}`);
    }) as typeof fetch;

    const gmail = new GmailService(mockFetch);
    const draftPayload = {
      to: 'recipient@example.com',
      subject: 'Hello from Aster',
      bodyText: 'Let us meet tomorrow.',
    };

    // 1. Creating draft is safe and executes
    const draftResult = await gmail.createEmailDraft('mock_token', draftPayload);
    assert.equal(draftResult.draftId, 'draft_456');
    assert.equal(sendCalled, false);

    // 2. Attempting to send with an unapproved ticket must throw ApprovalRequiredError
    const unapprovedTicket: ActionApprovalTicket = {
      ticketId: 'tkt_1',
      profileId: 'p1',
      actionType: 'GMAIL_SEND',
      actionHash: 'wrong_hash',
      confirmationToken: 'tok',
      approved: false,
      expiresAt: Date.now() + 60000,
      summary: 'Send email',
      payload: draftPayload,
    };

    await assert.rejects(
      async () => gmail.sendEmailWithApproval('mock_token', unapprovedTicket, draftPayload),
      (err: unknown) => err instanceof ApprovalRequiredError
    );
    assert.equal(sendCalled, false);
  });

  it('should require two-step confirmation for Google Calendar events', async () => {
    let postEventCalled = false;
    const mockFetch = (async (url: string, init?: RequestInit) => {
      if (url.includes('/events') && init?.method === 'POST') {
        postEventCalled = true;
        return {
          ok: true,
          status: 200,
          json: async () => ({
            id: 'event_committed_1',
            summary: 'Sync Meeting',
            start: { dateTime: '2026-11-02T10:00:00Z' },
            end: { dateTime: '2026-11-02T11:00:00Z' },
          }),
        } as unknown as Response;
      }
      throw new Error(`Unexpected url: ${url}`);
    }) as typeof fetch;

    const calendar = new GoogleCalendarService(mockFetch);
    const eventPayload = {
      summary: 'Sync Meeting',
      start: { dateTime: '2026-11-02T10:00:00Z' },
      end: { dateTime: '2026-11-02T11:00:00Z' },
    };

    // Step 1: Draft proposal
    const proposal = calendar.createDraftEventProposal(eventPayload);
    assert.ok(proposal.proposalId);
    assert.ok(proposal.confirmationToken);
    assert.equal(postEventCalled, false);

    // Step 2: Commit confirmed event with valid confirmation token
    const committed = await calendar.commitConfirmedEvent(
      'mock_token',
      proposal,
      proposal.confirmationToken
    );
    assert.equal(committed.id, 'event_committed_1');
    assert.equal(postEventCalled, true);

    // Invalid confirmation token must fail
    await assert.rejects(
      async () => calendar.commitConfirmedEvent('mock_token', proposal, 'bad_token'),
      /Invalid confirmation token/
    );
  });
});

describe('Shopify Storefront Integration', () => {
  it('should search products with GraphQL read-only query', async () => {
    const mockFetch = (async (url: string, init?: RequestInit) => {
      const body = JSON.parse(String(init?.body || '{}'));
      assert.ok(body.query.includes('SearchProducts'));

      return {
        ok: true,
        status: 200,
        json: async () => ({
          data: {
            products: {
              edges: [
                {
                  node: {
                    id: 'gid://shopify/Product/1',
                    title: 'Aster Minimalist Mug',
                    handle: 'aster-minimalist-mug',
                    description: 'Ceramic coffee mug',
                    availableForSale: true,
                    priceRange: {
                      minVariantPrice: { amount: '18.00', currencyCode: 'USD' },
                      maxVariantPrice: { amount: '18.00', currencyCode: 'USD' },
                    },
                    images: { edges: [] },
                    variants: {
                      edges: [
                        {
                          node: {
                            id: 'gid://shopify/ProductVariant/101',
                            title: 'Black',
                            availableForSale: true,
                            price: { amount: '18.00', currencyCode: 'USD' },
                          },
                        },
                      ],
                    },
                  },
                },
              ],
            },
          },
        }),
      } as unknown as Response;
    }) as typeof fetch;

    const client = new ShopifyStorefrontClient(
      { shopDomain: 'shop.aster.com', storefrontAccessToken: 'sf_token_123' },
      mockFetch
    );

    const products = await client.searchProducts('mug');
    assert.equal(products.length, 1);
    assert.equal(products[0].title, 'Aster Minimalist Mug');
    assert.equal(products[0].minPrice.amount, '18.00');
  });

  it('should draft a purchase proposal without auto-charging', async () => {
    const mockFetch = (async (url: string, init?: RequestInit) => {
      const body = JSON.parse(String(init?.body || '{}'));
      assert.ok(body.query.includes('CartCreate'));

      return {
        ok: true,
        status: 200,
        json: async () => ({
          data: {
            cartCreate: {
              cart: {
                id: 'cart_xyz_789',
                checkoutUrl: 'https://shop.aster.com/checkouts/cn/c1-abc123456',
                cost: {
                  subtotalAmount: { amount: '36.00', currencyCode: 'USD' },
                },
                lines: {
                  edges: [
                    {
                      node: {
                        id: 'line_1',
                        quantity: 2,
                        merchandise: {
                          id: 'gid://shopify/ProductVariant/101',
                          title: 'Black Mug',
                          price: { amount: '18.00', currencyCode: 'USD' },
                        },
                      },
                    },
                  ],
                },
              },
              userErrors: [],
            },
          },
        }),
      } as unknown as Response;
    }) as typeof fetch;

    const client = new ShopifyStorefrontClient(
      { shopDomain: 'shop.aster.com', storefrontAccessToken: 'sf_token_123' },
      mockFetch
    );

    const items: CartLineItemInput[] = [
      { merchandiseId: 'gid://shopify/ProductVariant/101', quantity: 2 },
    ];

    const proposal = await client.draftPurchaseProposal(items);
    assert.ok(proposal.proposalId);
    assert.ok(proposal.checkoutUrl);
    assert.equal(proposal.confirmed, false);
    assert.equal(proposal.estimatedCost.subtotalAmount.amount, '36.00');

    // Confirm proposal with token
    const result = client.verifyAndConfirmPurchaseProposal(proposal, proposal.confirmationToken);
    assert.equal(result.confirmed, true);
    assert.equal(result.checkoutUrl, proposal.checkoutUrl);
  });
});

describe('Integration Manager Orchestration', () => {
  it('should audit scopes and detect missing or CASA restricted scopes', () => {
    const manager = new IntegrationManager();
    const profileId = 'prof_audit_1';

    // Register Gmail with only read scope (missing compose)
    manager.registerConnection(
      profileId,
      'google_gmail',
      { accessToken: 'at_1', tokenType: 'Bearer', expiresIn: 3600, obtainedAt: Date.now() },
      [GOOGLE_SCOPES.GMAIL_READONLY]
    );

    const audit = manager.auditScopes(profileId, 'google_gmail');
    assert.equal(audit.isHealthy, false);
    assert.deepEqual(audit.missingScopes, [GOOGLE_SCOPES.GMAIL_COMPOSE]);
    assert.equal(audit.hasRestrictedCasaScopes, true);
    assert.equal(audit.recommendedAction, 'REAUTHENTICATE_MISSING_SCOPES');
  });

  it('should execute immediate RFC 7009 token revocation', async () => {
    let revocationEndpointCalled = false;
    const mockFetch = (async (url: string) => {
      if (url.includes('/revoke')) {
        revocationEndpointCalled = true;
        return { ok: true, status: 200, text: async () => '' } as unknown as Response;
      }
      throw new Error(`Unexpected url: ${url}`);
    }) as typeof fetch;

    const manager = new IntegrationManager(undefined, mockFetch);
    const profileId = 'prof_revoke_1';

    manager.registerConnection(
      profileId,
      'google_drive',
      { accessToken: 'at_to_revoke', tokenType: 'Bearer', expiresIn: 3600, obtainedAt: Date.now() },
      [GOOGLE_SCOPES.DRIVE_READONLY]
    );

    const result = await manager.revokeIntegration(profileId, 'google_drive');
    assert.equal(result.revoked, true);
    assert.equal(revocationEndpointCalled, true);

    const conn = manager.getConnection(profileId, 'google_drive');
    assert.equal(conn?.status, 'REVOKED');

    // Getting access token for revoked connection must fail
    await assert.rejects(
      async () => manager.getValidAccessToken(profileId, 'google_drive'),
      /is not connected/
    );
  });

  it('should manage staged action proposal lifecycle and prevent replay', () => {
    const manager = new IntegrationManager();
    const profileId = 'prof_action_1';

    const payload = { recipient: 'bob@example.com', subject: 'Report' };
    const staged = manager.stageActionProposal(
      profileId,
      'google_gmail',
      'GMAIL_SEND',
      'CONSEQUENTIAL',
      'Send quarterly report to Bob',
      payload
    );

    assert.equal(staged.status, 'PENDING');

    // Approve the ticket
    manager.approveProposal(staged.ticketId);
    assert.equal(staged.status, 'APPROVED');

    // Consume approval for execution
    const ticket = manager.validateAndConsumeApproval(
      staged.ticketId,
      staged.confirmationToken,
      payload
    );
    assert.equal(ticket.approved, true);
    assert.equal(staged.status, 'CONSUMED');

    // Attempting to consume again (replay attack) must fail
    assert.throws(() => {
      manager.validateAndConsumeApproval(staged.ticketId, staged.confirmationToken, payload);
    }, (err: unknown) => err instanceof ApprovalRequiredError);

    // Verify audit logs
    const logs = manager.getAuditLogsForProfile(profileId);
    assert.ok(logs.length >= 3);
  });
});
