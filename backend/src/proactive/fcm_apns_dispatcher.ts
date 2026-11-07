/**
 * Aster Companion - Proactive Intelligence Engine
 * Push Notification Dispatcher (FCM v1 & APNs HTTP/2)
 *
 * Implements:
 * 1. Firebase Cloud Messaging (FCM v1 HTTP API) dispatcher for Android devices.
 * 2. Apple Push Notification service (APNs HTTP/2 with p8 EC private key auth) for iOS devices.
 * 3. Rich interactive payloads with standardized action buttons ("Snooze 15m", "View Details", "Dismiss").
 * 4. Citation linkage: transparently binds source memory ID or screen event timestamp to payloads.
 */

import * as crypto from 'node:crypto';
import * as http2 from 'node:http2';
import {
  DeviceRegistration,
  DispatchResult,
  NotificationAction,
  ProactiveCandidate,
  ScoringDecision,
} from './types.js';

// Default interactive action buttons per PRD v1.1
export const DEFAULT_PROACTIVE_ACTIONS: NotificationAction[] = [
  {
    id: 'snooze_15m',
    title: 'Snooze 15m',
    type: 'snooze',
    payload: { durationMinutes: 15 },
  },
  {
    id: 'view_details',
    title: 'View Details',
    type: 'navigate',
  },
  {
    id: 'dismiss',
    title: 'Dismiss',
    type: 'dismiss',
    isDestructive: false,
  },
];

// Configuration for Firebase Cloud Messaging (FCM v1)
export interface FcmConfig {
  projectId: string;
  clientEmail: string;
  privateKey: string; // PEM-formatted RSA private key
  accessTokenProvider?: () => Promise<string>;
  customTransport?: (
    url: string,
    options: { method: string; headers: Record<string, string>; body: string }
  ) => Promise<{ status: number; body: string }>;
}

// Configuration for Apple Push Notification service (APNs)
export interface ApnsConfig {
  keyId: string; // 10-character Key ID from Apple Developer Portal
  teamId: string; // 10-character Team ID
  bundleId: string; // e.g. "com.aster.companion"
  privateKey: string; // PEM-formatted PKCS#8 EC private key (.p8)
  isProduction?: boolean; // Default: true (set false for sandbox)
  customTransport?: (
    host: string,
    path: string,
    headers: Record<string, string>,
    body: string
  ) => Promise<{ status: number; headers: Record<string, string | string[]>; body: string }>;
}

/**
 * FCM v1 HTTP API Dispatcher
 */
export class FcmV1Dispatcher {
  private readonly config: FcmConfig;
  private cachedAccessToken?: { token: string; expiresAt: number };

  constructor(config: FcmConfig) {
    this.config = config;
  }

  /**
   * Builds the standardized FCM v1 REST payload.
   */
  public buildPayload(
    candidate: ProactiveCandidate,
    deviceToken: string,
    score: number
  ): Record<string, unknown> {
    const actions = candidate.actions && candidate.actions.length > 0
      ? candidate.actions
      : DEFAULT_PROACTIVE_ACTIONS;

    const dataPayload: Record<string, string> = {
      notification_id: candidate.id,
      profile_id: candidate.profileId,
      category: candidate.category,
      score: score.toFixed(3),
      actions: JSON.stringify(actions),
    };

    // Attach citation linkage if present
    if (candidate.citation) {
      if (candidate.citation.sourceMemoryId) {
        dataPayload.source_memory_id = candidate.citation.sourceMemoryId;
      }
      if (candidate.citation.screenEventTimestamp) {
        dataPayload.screen_event_timestamp = candidate.citation.screenEventTimestamp;
      }
      dataPayload.citation_type = candidate.citation.sourceType;
      if (candidate.citation.snippet) {
        dataPayload.citation_snippet = candidate.citation.snippet;
      }
      if (candidate.citation.confidenceScore !== undefined) {
        dataPayload.citation_confidence = candidate.citation.confidenceScore.toFixed(2);
      }
    }

    const isHighUrgency = candidate.urgency >= 0.7 || candidate.category === 'emergency';

    return {
      message: {
        token: deviceToken,
        notification: {
          title: candidate.title,
          body: candidate.body,
        },
        android: {
          priority: isHighUrgency ? 'HIGH' : 'NORMAL',
          notification: {
            channel_id: candidate.category === 'emergency' ? 'aster_emergency' : 'aster_proactive',
            tag: `aster_${candidate.category}_${candidate.profileId}`,
            click_action: 'OPEN_PROACTIVE_DETAIL',
            default_sound: true,
            notification_priority: isHighUrgency ? 'PRIORITY_HIGH' : 'PRIORITY_DEFAULT',
          },
        },
        data: dataPayload,
      },
    };
  }

  /**
   * Dispatches a notification to an Android device using the FCM v1 REST API.
   */
  public async dispatch(
    candidate: ProactiveCandidate,
    deviceToken: string,
    score: number
  ): Promise<DispatchResult> {
    const startTime = new Date();
    try {
      const accessToken = await this.getAccessToken();
      const payload = this.buildPayload(candidate, deviceToken, score);
      const url = `https://fcm.googleapis.com/v1/projects/${this.config.projectId}/messages:send`;
      const body = JSON.stringify(payload);

      let status = 200;
      let responseBody = '';

      if (this.config.customTransport) {
        const res = await this.config.customTransport(url, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
          body,
        });
        status = res.status;
        responseBody = res.body;
      } else {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
          body,
        });
        status = response.status;
        responseBody = await response.text();
      }

      if (status >= 200 && status < 300) {
        let messageId: string | undefined;
        try {
          const parsed = JSON.parse(responseBody);
          messageId = parsed.name; // e.g. "projects/{projectId}/messages/{messageId}"
        } catch {
          // ignore parse error on messageId
        }

        return {
          notificationId: candidate.id,
          platform: 'android',
          deviceToken,
          success: true,
          messageId,
          statusCode: status,
          sentAt: startTime,
        };
      }

      // Handle FCM Error codes (e.g. UNREGISTERED token)
      const shouldUnregister =
        status === 404 ||
        responseBody.includes('UNREGISTERED') ||
        responseBody.includes('INVALID_ARGUMENT');

      return {
        notificationId: candidate.id,
        platform: 'android',
        deviceToken,
        success: false,
        statusCode: status,
        error: responseBody || `FCM request failed with status ${status}`,
        shouldUnregisterToken: shouldUnregister,
        sentAt: startTime,
      };
    } catch (err) {
      return {
        notificationId: candidate.id,
        platform: 'android',
        deviceToken,
        success: false,
        error: err instanceof Error ? err.message : String(err),
        sentAt: startTime,
      };
    }
  }

  /**
   * Retrieves or mints a Google OAuth2 Bearer token for FCM v1.
   */
  private async getAccessToken(): Promise<string> {
    if (this.config.accessTokenProvider) {
      return this.config.accessTokenProvider();
    }

    const nowSeconds = Math.floor(Date.now() / 1000);
    if (this.cachedAccessToken && this.cachedAccessToken.expiresAt > nowSeconds + 60) {
      return this.cachedAccessToken.token;
    }

    // Mint RS256 JWT assertion for Google Service Account
    const jwt = this.signGoogleServiceAccountJwt(nowSeconds);
    const tokenUrl = 'https://oauth2.googleapis.com/token';
    const params = new URLSearchParams({
      grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
      assertion: jwt,
    });

    let resData: { access_token: string; expires_in: number };

    if (this.config.customTransport) {
      const res = await this.config.customTransport(tokenUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: params.toString(),
      });
      resData = JSON.parse(res.body);
    } else {
      const res = await fetch(tokenUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: params.toString(),
      });
      if (!res.ok) {
        throw new Error(`Google OAuth2 token exchange failed with status ${res.status}: ${await res.text()}`);
      }
      resData = await res.json() as { access_token: string; expires_in: number };
    }

    this.cachedAccessToken = {
      token: resData.access_token,
      expiresAt: nowSeconds + (resData.expires_in || 3600),
    };

    return this.cachedAccessToken.token;
  }

  private signGoogleServiceAccountJwt(nowSeconds: number): string {
    const header = { alg: 'RS256', typ: 'JWT' };
    const claim = {
      iss: this.config.clientEmail,
      scope: 'https://www.googleapis.com/auth/firebase.messaging',
      aud: 'https://oauth2.googleapis.com/token',
      exp: nowSeconds + 3600,
      iat: nowSeconds,
    };

    const encodedHeader = Buffer.from(JSON.stringify(header)).toString('base64url');
    const encodedClaim = Buffer.from(JSON.stringify(claim)).toString('base64url');
    const signatureInput = `${encodedHeader}.${encodedClaim}`;

    const signer = crypto.createSign('RSA-SHA256');
    signer.update(signatureInput);
    signer.end();
    const signature = signer.sign(this.config.privateKey, 'base64url');

    return `${signatureInput}.${signature}`;
  }
}

/**
 * Apple Push Notification service (APNs) HTTP/2 Dispatcher
 */
export class ApnsHttp2Dispatcher {
  private readonly config: ApnsConfig;
  private cachedJwt?: { token: string; mintedAt: number };

  constructor(config: ApnsConfig) {
    this.config = config;
  }

  /**
   * Builds the standardized Apple Push Notification payload.
   */
  public buildPayload(
    candidate: ProactiveCandidate,
    score: number
  ): Record<string, unknown> {
    const actions = candidate.actions && candidate.actions.length > 0
      ? candidate.actions
      : DEFAULT_PROACTIVE_ACTIONS;

    const asterPayload: Record<string, unknown> = {
      notification_id: candidate.id,
      profile_id: candidate.profileId,
      category: candidate.category,
      score,
      actions,
    };

    if (candidate.citation) {
      asterPayload.citation = {
        source_memory_id: candidate.citation.sourceMemoryId,
        screen_event_timestamp: candidate.citation.screenEventTimestamp,
        source_type: candidate.citation.sourceType,
        snippet: candidate.citation.snippet,
        confidence_score: candidate.citation.confidenceScore,
      };
    }

    return {
      aps: {
        alert: {
          title: candidate.title,
          subtitle: candidate.subtitle,
          body: candidate.body,
        },
        sound: candidate.category === 'emergency' ? 'emergency.caf' : 'default',
        badge: 1,
        category: 'ASTER_ACTIONABLE_PROACTIVE',
        'thread-id': `aster_${candidate.category}_${candidate.profileId}`,
      },
      aster: asterPayload,
    };
  }

  /**
   * Dispatches a notification to an iOS device using APNs HTTP/2 with token auth.
   */
  public async dispatch(
    candidate: ProactiveCandidate,
    deviceToken: string,
    score: number
  ): Promise<DispatchResult> {
    const startTime = new Date();
    try {
      const jwt = this.getOrMintApnsJwt();
      const payload = this.buildPayload(candidate, score);
      const payloadString = JSON.stringify(payload);

      const host = this.config.isProduction === false
        ? 'api.sandbox.push.apple.com'
        : 'api.push.apple.com';
      const path = `/3/device/${deviceToken}`;

      const isHighUrgency = candidate.urgency >= 0.7 || candidate.category === 'emergency';
      const headers: Record<string, string> = {
        ':method': 'POST',
        ':path': path,
        authorization: `bearer ${jwt}`,
        'apns-topic': this.config.bundleId,
        'apns-push-type': 'alert',
        'apns-priority': isHighUrgency ? '10' : '5',
        'apns-expiration': String(Math.floor(Date.now() / 1000) + 86400),
        'apns-collapse-id': `aster_${candidate.category}_${candidate.id}`.slice(0, 64),
      };

      if (this.config.customTransport) {
        const res = await this.config.customTransport(host, path, headers, payloadString);
        return this.processApnsResponse(
          candidate.id,
          deviceToken,
          res.status,
          res.headers['apns-id'] as string | undefined,
          res.body,
          startTime
        );
      }

      // Native Node.js HTTP/2 Client Request
      return await new Promise<DispatchResult>((resolve) => {
        const client = http2.connect(`https://${host}`);
        client.on('error', (err) => {
          resolve({
            notificationId: candidate.id,
            platform: 'ios',
            deviceToken,
            success: false,
            error: `APNs connection error: ${err.message}`,
            sentAt: startTime,
          });
        });

        const req = client.request(headers);
        let status = 0;
        let apnsId: string | undefined;
        let responseData = '';

        req.on('response', (headers) => {
          status = Number(headers[':status']);
          apnsId = headers['apns-id'] as string | undefined;
        });

        req.setEncoding('utf8');
        req.on('data', (chunk) => {
          responseData += chunk;
        });

        req.on('end', () => {
          client.close();
          resolve(this.processApnsResponse(candidate.id, deviceToken, status, apnsId, responseData, startTime));
        });

        req.on('error', (err) => {
          client.close();
          resolve({
            notificationId: candidate.id,
            platform: 'ios',
            deviceToken,
            success: false,
            error: `APNs request error: ${err.message}`,
            sentAt: startTime,
          });
        });

        req.write(payloadString);
        req.end();
      });
    } catch (err) {
      return {
        notificationId: candidate.id,
        platform: 'ios',
        deviceToken,
        success: false,
        error: err instanceof Error ? err.message : String(err),
        sentAt: startTime,
      };
    }
  }

  private processApnsResponse(
    notificationId: string,
    deviceToken: string,
    status: number,
    apnsId: string | undefined,
    responseBody: string,
    sentAt: Date
  ): DispatchResult {
    if (status === 200) {
      return {
        notificationId,
        platform: 'ios',
        deviceToken,
        success: true,
        messageId: apnsId,
        statusCode: status,
        sentAt,
      };
    }

    // 410 = Unregistered (app uninstalled), 400 = BadDeviceToken
    const shouldUnregister = status === 410 || (status === 400 && responseBody.includes('BadDeviceToken'));

    return {
      notificationId,
      platform: 'ios',
      deviceToken,
      success: false,
      statusCode: status,
      error: responseBody || `APNs error status ${status}`,
      shouldUnregisterToken: shouldUnregister,
      sentAt,
    };
  }

  /**
   * Mints an ES256 JWT using the Apple PKCS#8 (.p8) private key.
   * Apple permits tokens to be valid for up to 60 minutes; we cache for 50 minutes.
   */
  public getOrMintApnsJwt(): string {
    const nowSeconds = Math.floor(Date.now() / 1000);
    if (this.cachedJwt && nowSeconds - this.cachedJwt.mintedAt < 3000) {
      return this.cachedJwt.token;
    }

    const header = { alg: 'ES256', kid: this.config.keyId };
    const claim = { iss: this.config.teamId, iat: nowSeconds };

    const encodedHeader = Buffer.from(JSON.stringify(header)).toString('base64url');
    const encodedClaim = Buffer.from(JSON.stringify(claim)).toString('base64url');
    const signatureInput = `${encodedHeader}.${encodedClaim}`;

    const signer = crypto.createSign('SHA256');
    signer.update(signatureInput);
    signer.end();
    const signature = signer.sign({
      key: this.config.privateKey,
      dsaEncoding: 'ieee-p1363', // Required by Apple APNs for ES256
    }, 'base64url');

    const token = `${signatureInput}.${signature}`;
    this.cachedJwt = { token, mintedAt: nowSeconds };
    return token;
  }
}

/**
 * Unified Dispatcher: Coordinates delivery to Android (FCM) and iOS (APNs)
 * with strict scoring gate verification.
 */
export class UnifiedNotificationDispatcher {
  private readonly fcmDispatcher?: FcmV1Dispatcher;
  private readonly apnsDispatcher?: ApnsHttp2Dispatcher;

  constructor(options: { fcm?: FcmV1Dispatcher; apns?: ApnsHttp2Dispatcher }) {
    this.fcmDispatcher = options.fcm;
    this.apnsDispatcher = options.apns;
  }

  /**
   * Dispatches proactive notification candidate to registered user devices.
   */
  public async dispatchCandidate(
    candidate: ProactiveCandidate,
    decision: ScoringDecision,
    devices: DeviceRegistration[],
    forceBypassDecision = false
  ): Promise<DispatchResult[]> {
    if (!decision.shouldDeliver && !forceBypassDecision) {
      return [];
    }

    const results: DispatchResult[] = [];
    const score = decision.scoreBreakdown.finalScore;

    for (const device of devices) {
      if (candidate.targetPlatform && candidate.targetPlatform !== 'all') {
        if (candidate.targetPlatform !== device.platform) {
          continue;
        }
      }

      if (device.platform === 'android') {
        if (!this.fcmDispatcher) {
          results.push({
            notificationId: candidate.id,
            platform: 'android',
            deviceToken: device.deviceToken,
            success: false,
            error: 'FCM dispatcher not configured on server',
            sentAt: new Date(),
          });
          continue;
        }
        const res = await this.fcmDispatcher.dispatch(candidate, device.deviceToken, score);
        results.push(res);
      } else if (device.platform === 'ios') {
        if (!this.apnsDispatcher) {
          results.push({
            notificationId: candidate.id,
            platform: 'ios',
            deviceToken: device.deviceToken,
            success: false,
            error: 'APNs dispatcher not configured on server',
            sentAt: new Date(),
          });
          continue;
        }
        const res = await this.apnsDispatcher.dispatch(candidate, device.deviceToken, score);
        results.push(res);
      }
    }

    return results;
  }
}
