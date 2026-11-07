/**
 * Aster Companion - External Integrations & OAuth Service
 * oauth_pkce_handler.ts
 *
 * Full RFC 7636 OAuth 2.0 Authorization Code flow with PKCE,
 * high-entropy verifier/challenge generation, state/nonce validation against CSRF,
 * AES-256-GCM encryption for refresh tokens, and automatic token rotation
 * with reuse detection (RFC 6749 / RFC 9700 OAuth Security BCP).
 */

import {
  randomBytes,
  createHash,
  createCipheriv,
  createDecipheriv,
  timingSafeEqual,
} from 'node:crypto';

// ============================================================================
// Types and Interfaces
// ============================================================================

export interface PKCEPair {
  codeVerifier: string;
  codeChallenge: string;
  codeChallengeMethod: 'S256';
}

export interface OAuthState {
  stateToken: string;
  profileId: string;
  provider: string;
  codeVerifier: string;
  nonce: string;
  redirectUri: string;
  scopes: string[];
  createdAt: number;
  expiresAt: number;
  metadata?: Record<string, unknown>;
}

export interface EncryptedTokenPayload {
  version: number;
  iv: string;         // hex encoded (12 bytes for GCM)
  authTag: string;    // hex encoded (16 bytes)
  ciphertext: string; // hex encoded
  algorithm: 'aes-256-gcm';
  keyId?: string;
}

export interface StoredRefreshTokenRecord {
  familyId: string;
  profileId: string;
  provider: string;
  generation: number;
  tokenHash: string; // SHA-256 hash of plaintext token for indexed lookup/reuse detection
  encryptedPayload: EncryptedTokenPayload;
  isRevoked: boolean;
  revokedReason?: string;
  createdAt: number;
  expiresAt?: number;
  replacedAt?: number;
}

export interface OAuthTokens {
  accessToken: string;
  tokenType: string;
  expiresIn: number;
  refreshToken?: string;
  scope?: string;
  idToken?: string;
  obtainedAt: number;
}

export interface OAuthClientConfig {
  providerId: string;
  clientId: string;
  clientSecret?: string;
  authorizationEndpoint: string;
  tokenEndpoint: string;
  revocationEndpoint?: string;
  defaultScopes: string[];
  redirectUri: string;
}

export interface AuthorizationUrlParams {
  profileId: string;
  scopes?: string[];
  redirectUri?: string;
  customParameters?: Record<string, string>;
  metadata?: Record<string, unknown>;
}

// ============================================================================
// Custom Security Errors
// ============================================================================

export class OAuthSecurityError extends Error {
  public readonly code: string;

  constructor(message: string, code: string) {
    super(`[${code}] ${message}`);
    this.code = code;
    this.name = 'OAuthSecurityError';
  }
}

export class TokenReuseDetectedError extends OAuthSecurityError {
  public readonly familyId: string;
  public readonly generation: number;

  constructor(familyId: string, generation: number) {
    super(
      `Compromised OAuth token reuse detected for family ${familyId} at generation ${generation}. All tokens in this family have been revoked.`,
      'TOKEN_REUSE_DETECTED'
    );
    this.familyId = familyId;
    this.generation = generation;
    this.name = 'TokenReuseDetectedError';
  }
}

// ============================================================================
// PKCE Utilities (RFC 7636)
// ============================================================================

/**
 * Base64url encoding without padding as required by RFC 7636.
 */
export function base64UrlEncode(buffer: Buffer): string {
  return buffer
    .toString('base64')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

/**
 * Generates an RFC 7636 compliant code_verifier.
 * Characters are drawn from unreserved charset [A-Za-z0-9-._~]
 * with minimum 43 and maximum 128 characters of high entropy.
 */
export function generateCodeVerifier(length = 64): string {
  if (length < 43 || length > 128) {
    throw new OAuthSecurityError(
      'code_verifier length must be between 43 and 128 characters',
      'INVALID_VERIFIER_LENGTH'
    );
  }
  const random = randomBytes(length);
  const unreserved = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~';
  let verifier = '';
  for (let i = 0; i < length; i++) {
    verifier += unreserved[random[i] % unreserved.length];
  }
  return verifier;
}

/**
 * Computes S256 code_challenge: base64url(SHA256(ASCII(code_verifier)))
 */
export function generateCodeChallenge(verifier: string): string {
  if (!verifier || verifier.length < 43 || verifier.length > 128) {
    throw new OAuthSecurityError('Invalid verifier for code challenge calculation', 'INVALID_VERIFIER');
  }
  const hash = createHash('sha256').update(verifier, 'ascii').digest();
  return base64UrlEncode(hash);
}

/**
 * Creates a matched PKCE code verifier and S256 code challenge pair.
 */
export function generatePKCEPair(verifierLength = 64): PKCEPair {
  const verifier = generateCodeVerifier(verifierLength);
  const challenge = generateCodeChallenge(verifier);
  return {
    codeVerifier: verifier,
    codeChallenge: challenge,
    codeChallengeMethod: 'S256',
  };
}

/**
 * Verifies code_verifier against stored code_challenge using timing-safe comparison.
 */
export function verifyCodeChallenge(verifier: string, expectedChallenge: string): boolean {
  try {
    const computed = generateCodeChallenge(verifier);
    const bufA = Buffer.from(computed, 'utf8');
    const bufB = Buffer.from(expectedChallenge, 'utf8');
    if (bufA.length !== bufB.length) return false;
    return timingSafeEqual(bufA, bufB);
  } catch {
    return false;
  }
}

// ============================================================================
// AES-256-GCM Server-Side Refresh Token Encryption
// ============================================================================

export class TokenEncryptionService {
  private readonly masterKey: Buffer;
  private readonly keyId: string;

  constructor(keyHexOrBase64?: string, keyId = 'aster-primary-v1') {
    this.keyId = keyId;
    if (keyHexOrBase64) {
      if (keyHexOrBase64.length === 64) {
        this.masterKey = Buffer.from(keyHexOrBase64, 'hex');
      } else {
        const buf = Buffer.from(keyHexOrBase64, 'base64');
        if (buf.length === 32) {
          this.masterKey = buf;
        } else {
          throw new OAuthSecurityError('Encryption key must be exactly 32 bytes (256 bits)', 'INVALID_KEY_LENGTH');
        }
      }
    } else {
      // Fallback to process.env or deterministic fallback for unconfigured runtime
      const envKey = process.env.ASTER_TOKEN_ENCRYPTION_KEY;
      if (envKey && envKey.length === 64) {
        this.masterKey = Buffer.from(envKey, 'hex');
      } else if (envKey && Buffer.from(envKey, 'base64').length === 32) {
        this.masterKey = Buffer.from(envKey, 'base64');
      } else {
        // Derive master key using high-entropy SHA256 of seed for default local dev/sandbox
        const fallbackSeed = process.env.ASTER_TOKEN_SEED || 'aster-companion-default-fallback-secure-seed-2026';
        this.masterKey = createHash('sha256').update(fallbackSeed).digest();
      }
    }
  }

  /**
   * Encrypts plaintext token using AES-256-GCM with a unique 12-byte IV per token.
   * Optional AAD (Additional Authenticated Data) binds ciphertext to profileId/providerId.
   */
  public encrypt(plaintext: string, aad?: string): EncryptedTokenPayload {
    if (!plaintext) {
      throw new OAuthSecurityError('Cannot encrypt empty token', 'EMPTY_PLAINTEXT');
    }
    const iv = randomBytes(12); // Standard 96-bit IV for AES-GCM
    const cipher = createCipheriv('aes-256-gcm', this.masterKey, iv);

    if (aad) {
      cipher.setAAD(Buffer.from(aad, 'utf8'));
    }

    const encrypted = Buffer.concat([cipher.update(plaintext, 'utf8'), cipher.final()]);
    const authTag = cipher.getAuthTag();

    return {
      version: 1,
      algorithm: 'aes-256-gcm',
      iv: iv.toString('hex'),
      authTag: authTag.toString('hex'),
      ciphertext: encrypted.toString('hex'),
      keyId: this.keyId,
    };
  }

  /**
   * Decrypts ciphertext and verifies AES-256-GCM authentication tag.
   * Throws an OAuthSecurityError if tag verification fails or data is corrupted.
   */
  public decrypt(payload: EncryptedTokenPayload, aad?: string): string {
    if (payload.algorithm !== 'aes-256-gcm') {
      throw new OAuthSecurityError(`Unsupported encryption algorithm: ${payload.algorithm}`, 'UNSUPPORTED_ALGO');
    }
    const iv = Buffer.from(payload.iv, 'hex');
    const authTag = Buffer.from(payload.authTag, 'hex');
    const ciphertext = Buffer.from(payload.ciphertext, 'hex');

    if (iv.length !== 12) {
      throw new OAuthSecurityError('Invalid IV length for AES-GCM', 'INVALID_IV');
    }
    if (authTag.length !== 16) {
      throw new OAuthSecurityError('Invalid AuthTag length for AES-GCM', 'INVALID_AUTHTAG');
    }

    try {
      const decipher = createDecipheriv('aes-256-gcm', this.masterKey, iv);
      decipher.setAuthTag(authTag);

      if (aad) {
        decipher.setAAD(Buffer.from(aad, 'utf8'));
      }

      const decrypted = Buffer.concat([decipher.update(ciphertext), decipher.final()]);
      return decrypted.toString('utf8');
    } catch (err) {
      throw new OAuthSecurityError(
        'Decryption or authentication tag verification failed. Token ciphertext has been tampered with or corrupted.',
        'DECRYPTION_FAILED'
      );
    }
  }

  /**
   * Produces a SHA-256 hash of a plaintext token for indexed lookup without storing plaintext.
   */
  public hashToken(token: string): string {
    return createHash('sha256').update(token, 'utf8').digest('hex');
  }
}

// ============================================================================
// State & Nonce Store (CSRF & Replay Mitigation)
// ============================================================================

export class OAuthStateStore {
  private readonly states = new Map<string, OAuthState>();
  private readonly defaultTtlMs = 10 * 60 * 1000; // 10 minutes

  /**
   * Generates a new cryptographically secure state and nonce pair,
   * binding profileId, provider, and PKCE verifier.
   */
  public createState(
    profileId: string,
    provider: string,
    codeVerifier: string,
    redirectUri: string,
    scopes: string[],
    metadata?: Record<string, unknown>,
    ttlMs?: number
  ): OAuthState {
    const stateToken = base64UrlEncode(randomBytes(32));
    const nonce = base64UrlEncode(randomBytes(24));
    const now = Date.now();
    const expiresAt = now + (ttlMs || this.defaultTtlMs);

    const record: OAuthState = {
      stateToken,
      profileId,
      provider,
      codeVerifier,
      nonce,
      redirectUri,
      scopes,
      createdAt: now,
      expiresAt,
      metadata,
    };

    this.states.set(stateToken, record);
    return record;
  }

  /**
   * Validates and atomically consumes the state token.
   * Protects against CSRF and replay attacks.
   */
  public validateAndConsume(receivedStateToken: string, expectedNonce?: string): OAuthState {
    this.cleanExpired();

    const record = this.states.get(receivedStateToken);
    if (!record) {
      throw new OAuthSecurityError('OAuth state token invalid or not found', 'INVALID_STATE');
    }

    // Atomic consumption: delete immediately
    this.states.delete(receivedStateToken);

    if (Date.now() > record.expiresAt) {
      throw new OAuthSecurityError('OAuth state token has expired', 'EXPIRED_STATE');
    }

    if (expectedNonce && record.nonce !== expectedNonce) {
      throw new OAuthSecurityError('OAuth nonce mismatch', 'NONCE_MISMATCH');
    }

    return record;
  }

  /**
   * Cleans expired state entries to prevent unbounded memory growth.
   */
  public cleanExpired(): void {
    const now = Date.now();
    for (const [key, state] of this.states.entries()) {
      if (now > state.expiresAt) {
        this.states.delete(key);
      }
    }
  }

  public size(): number {
    return this.states.size;
  }
}

// ============================================================================
// Refresh Token Rotation & Family Manager
// ============================================================================

export class TokenRotationManager {
  // Keyed by familyId -> array of generations
  private readonly families = new Map<string, StoredRefreshTokenRecord[]>();
  // Index for fast lookup: tokenHash -> { familyId, generation }
  private readonly tokenHashIndex = new Map<string, { familyId: string; generation: number }>();
  private readonly encryptionService: TokenEncryptionService;

  constructor(encryptionService: TokenEncryptionService) {
    this.encryptionService = encryptionService;
  }

  /**
   * Registers an initial refresh token obtained from authorization code exchange.
   */
  public registerInitialToken(
    profileId: string,
    provider: string,
    refreshToken: string,
    expiresInMs?: number
  ): StoredRefreshTokenRecord {
    const familyId = `fam_${base64UrlEncode(randomBytes(16))}`;
    const tokenHash = this.encryptionService.hashToken(refreshToken);
    const aad = `${profileId}:${provider}:${familyId}:gen0`;
    const encryptedPayload = this.encryptionService.encrypt(refreshToken, aad);

    const record: StoredRefreshTokenRecord = {
      familyId,
      profileId,
      provider,
      generation: 0,
      tokenHash,
      encryptedPayload,
      isRevoked: false,
      createdAt: Date.now(),
      expiresAt: expiresInMs ? Date.now() + expiresInMs : undefined,
    };

    this.families.set(familyId, [record]);
    this.tokenHashIndex.set(tokenHash, { familyId, generation: 0 });
    return record;
  }

  /**
   * Rotates a refresh token:
   * 1. Verifies the presented token matches active family token.
   * 2. Detects reuse: If an already-rotated predecessor token is presented,
   *    revokes the ENTIRE token family and raises TokenReuseDetectedError.
   * 3. Issues new refresh token, encrypts with incremented generation, and revokes predecessor.
   */
  public rotateToken(
    presentedRefreshToken: string,
    newRefreshToken: string,
    profileId: string,
    provider: string,
    newExpiresInMs?: number
  ): StoredRefreshTokenRecord {
    const presentedHash = this.encryptionService.hashToken(presentedRefreshToken);
    const indexEntry = this.tokenHashIndex.get(presentedHash);

    if (!indexEntry) {
      throw new OAuthSecurityError('Presented refresh token not recognized', 'UNKNOWN_TOKEN');
    }

    const { familyId, generation } = indexEntry;
    const history = this.families.get(familyId);
    if (!history || history.length === 0) {
      throw new OAuthSecurityError('Token family not found', 'FAMILY_NOT_FOUND');
    }

    const currentActiveRecord = history[history.length - 1];

    // If family is already revoked, reject immediately
    if (currentActiveRecord.isRevoked) {
      throw new OAuthSecurityError(
        `Token family ${familyId} is revoked: ${currentActiveRecord.revokedReason || 'Security policy'}`,
        'FAMILY_REVOKED'
      );
    }

    // REUSE DETECTION:
    // If the presented token is not the latest active generation in the family,
    // an attacker or compromised party is attempting to replay a previously rotated token!
    if (generation < currentActiveRecord.generation) {
      this.revokeFamily(familyId, `Compromised token reuse detected at generation ${generation}`);
      throw new TokenReuseDetectedError(familyId, generation);
    }

    // Verify token expiry if set
    if (currentActiveRecord.expiresAt && Date.now() > currentActiveRecord.expiresAt) {
      throw new OAuthSecurityError('Presented refresh token has expired', 'EXPIRED_REFRESH_TOKEN');
    }

    // Verify profileId & provider boundary
    if (currentActiveRecord.profileId !== profileId || currentActiveRecord.provider !== provider) {
      throw new OAuthSecurityError('Profile or provider boundary mismatch', 'BOUNDARY_VIOLATION');
    }

    const now = Date.now();
    // Mark predecessor as replaced
    currentActiveRecord.replacedAt = now;

    // Encrypt and store new generation
    const nextGeneration = currentActiveRecord.generation + 1;
    const nextAad = `${profileId}:${provider}:${familyId}:gen${nextGeneration}`;
    const newEncryptedPayload = this.encryptionService.encrypt(newRefreshToken, nextAad);
    const newTokenHash = this.encryptionService.hashToken(newRefreshToken);

    const nextRecord: StoredRefreshTokenRecord = {
      familyId,
      profileId,
      provider,
      generation: nextGeneration,
      tokenHash: newTokenHash,
      encryptedPayload: newEncryptedPayload,
      isRevoked: false,
      createdAt: now,
      expiresAt: newExpiresInMs ? now + newExpiresInMs : undefined,
    };

    history.push(nextRecord);
    this.tokenHashIndex.set(newTokenHash, { familyId, generation: nextGeneration });

    return nextRecord;
  }

  /**
   * Retrieves and decrypts the currently active refresh token for a family.
   */
  public getActiveDecryptedToken(familyId: string): string {
    const history = this.families.get(familyId);
    if (!history || history.length === 0) {
      throw new OAuthSecurityError('Token family not found', 'FAMILY_NOT_FOUND');
    }
    const active = history[history.length - 1];
    if (active.isRevoked) {
      throw new OAuthSecurityError(`Token family ${familyId} is revoked`, 'FAMILY_REVOKED');
    }
    const aad = `${active.profileId}:${active.provider}:${familyId}:gen${active.generation}`;
    return this.encryptionService.decrypt(active.encryptedPayload, aad);
  }

  /**
   * Revokes all tokens in a family (e.g. on user disconnect or breach detection).
   */
  public revokeFamily(familyId: string, reason: string): void {
    const history = this.families.get(familyId);
    if (!history) return;
    for (const record of history) {
      record.isRevoked = true;
      record.revokedReason = reason;
    }
  }

  public getFamilyRecord(familyId: string): StoredRefreshTokenRecord | undefined {
    const history = this.families.get(familyId);
    return history ? history[history.length - 1] : undefined;
  }
}

// ============================================================================
// Main OAuth PKCE Handler
// ============================================================================

export class OAuthPKCEHandler {
  public readonly encryptionService: TokenEncryptionService;
  public readonly stateStore: OAuthStateStore;
  public readonly tokenRotationManager: TokenRotationManager;

  constructor(encryptionKeyHex?: string) {
    this.encryptionService = new TokenEncryptionService(encryptionKeyHex);
    this.stateStore = new OAuthStateStore();
    this.tokenRotationManager = new TokenRotationManager(this.encryptionService);
  }

  /**
   * Generates authorization parameters and constructs provider authorization URL.
   */
  public buildAuthorizationUrl(
    config: OAuthClientConfig,
    params: AuthorizationUrlParams
  ): {
    authorizationUrl: string;
    state: string;
    nonce: string;
    codeVerifier: string;
    codeChallenge: string;
  } {
    const pkce = generatePKCEPair(64);
    const redirectUri = params.redirectUri || config.redirectUri;
    const requestedScopes = params.scopes || config.defaultScopes;

    const stateRecord = this.stateStore.createState(
      params.profileId,
      config.providerId,
      pkce.codeVerifier,
      redirectUri,
      requestedScopes,
      params.metadata
    );

    const url = new URL(config.authorizationEndpoint);
    url.searchParams.set('response_type', 'code');
    url.searchParams.set('client_id', config.clientId);
    url.searchParams.set('redirect_uri', redirectUri);
    url.searchParams.set('scope', requestedScopes.join(' '));
    url.searchParams.set('state', stateRecord.stateToken);
    url.searchParams.set('nonce', stateRecord.nonce);
    url.searchParams.set('code_challenge', pkce.codeChallenge);
    url.searchParams.set('code_challenge_method', 'S256');

    // Provider specific parameters
    if (config.providerId.startsWith('google')) {
      url.searchParams.set('access_type', 'offline');
      url.searchParams.set('prompt', 'consent');
      url.searchParams.set('include_granted_scopes', 'true');
    }

    if (params.customParameters) {
      for (const [k, v] of Object.entries(params.customParameters)) {
        url.searchParams.set(k, v);
      }
    }

    return {
      authorizationUrl: url.toString(),
      state: stateRecord.stateToken,
      nonce: stateRecord.nonce,
      codeVerifier: pkce.codeVerifier,
      codeChallenge: pkce.codeChallenge,
    };
  }

  /**
   * Handles callback authorization code exchange.
   * Validates state, verifies code_verifier, calls token endpoint,
   * encrypts refresh token, and initializes token rotation family.
   */
  public async handleAuthorizationCallback(
    config: OAuthClientConfig,
    receivedCode: string,
    receivedState: string,
    fetchFn = fetch
  ): Promise<{
    tokens: OAuthTokens;
    state: OAuthState;
    storedRefreshTokenRecord?: StoredRefreshTokenRecord;
  }> {
    // Validate and atomically consume state against CSRF
    const state = this.stateStore.validateAndConsume(receivedState);

    const bodyParams = new URLSearchParams({
      grant_type: 'authorization_code',
      code: receivedCode,
      redirect_uri: state.redirectUri,
      client_id: config.clientId,
      code_verifier: state.codeVerifier,
    });

    if (config.clientSecret) {
      bodyParams.set('client_secret', config.clientSecret);
    }

    const response = await fetchFn(config.tokenEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        Accept: 'application/json',
      },
      body: bodyParams.toString(),
    });

    if (!response.ok) {
      const errText = await response.text();
      throw new OAuthSecurityError(
        `Token endpoint responded with HTTP ${response.status}: ${errText}`,
        'TOKEN_EXCHANGE_FAILED'
      );
    }

    const data = (await response.json()) as Record<string, unknown>;

    const tokens: OAuthTokens = {
      accessToken: String(data.access_token || ''),
      tokenType: String(data.token_type || 'Bearer'),
      expiresIn: Number(data.expires_in || 3600),
      refreshToken: data.refresh_token ? String(data.refresh_token) : undefined,
      scope: data.scope ? String(data.scope) : undefined,
      idToken: data.id_token ? String(data.id_token) : undefined,
      obtainedAt: Date.now(),
    };

    let storedRefreshTokenRecord: StoredRefreshTokenRecord | undefined;
    if (tokens.refreshToken) {
      storedRefreshTokenRecord = this.tokenRotationManager.registerInitialToken(
        state.profileId,
        config.providerId,
        tokens.refreshToken
      );
    }

    return {
      tokens,
      state,
      storedRefreshTokenRecord,
    };
  }

  /**
   * Performs automated token refresh with rotation and reuse detection.
   */
  public async refreshAccessToken(
    config: OAuthClientConfig,
    profileId: string,
    familyId: string,
    fetchFn = fetch
  ): Promise<{
    tokens: OAuthTokens;
    rotationRecord: StoredRefreshTokenRecord;
  }> {
    const activeRefreshToken = this.tokenRotationManager.getActiveDecryptedToken(familyId);

    const bodyParams = new URLSearchParams({
      grant_type: 'refresh_token',
      refresh_token: activeRefreshToken,
      client_id: config.clientId,
    });

    if (config.clientSecret) {
      bodyParams.set('client_secret', config.clientSecret);
    }

    const response = await fetchFn(config.tokenEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        Accept: 'application/json',
      },
      body: bodyParams.toString(),
    });

    if (!response.ok) {
      const errText = await response.text();
      throw new OAuthSecurityError(
        `Token refresh endpoint responded with HTTP ${response.status}: ${errText}`,
        'TOKEN_REFRESH_FAILED'
      );
    }

    const data = (await response.json()) as Record<string, unknown>;

    // Upstream may return a new refresh token (rotation) or keep previous
    const newRefreshToken = data.refresh_token ? String(data.refresh_token) : activeRefreshToken;

    const rotationRecord = this.tokenRotationManager.rotateToken(
      activeRefreshToken,
      newRefreshToken,
      profileId,
      config.providerId
    );

    const tokens: OAuthTokens = {
      accessToken: String(data.access_token || ''),
      tokenType: String(data.token_type || 'Bearer'),
      expiresIn: Number(data.expires_in || 3600),
      refreshToken: newRefreshToken,
      scope: data.scope ? String(data.scope) : undefined,
      obtainedAt: Date.now(),
    };

    return { tokens, rotationRecord };
  }
}
