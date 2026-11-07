import { describe, it, expect, beforeEach } from 'vitest';
import { VoiceBroker } from '../src/realtime/voice_broker.js';
import { OpenAIRealtimeAdapter } from '../src/realtime/openai_adapter.js';
import { GeminiLiveAdapter } from '../src/realtime/gemini_live_adapter.js';
import { VoiceQuotaTracker } from '../src/realtime/quota_tracker.js';

describe('VoiceBroker & Dual-Adapter Abstraction', () => {
  let broker: VoiceBroker;

  beforeEach(() => {
    broker = new VoiceBroker({
      dailyMinuteLimit: 60,
      maxConcurrentSessions: 1,
    });
  });

  describe('OpenAI Realtime Adapter', () => {
    it('should dispense short-lived scoped ephemeral session token with gpt-4o-realtime-preview', async () => {
      const adapter = new OpenAIRealtimeAdapter();
      const session = await adapter.createEphemeralSession({
        userId: 'user_123',
        profileId: 'profile_aster',
        deviceId: 'device_pixel_9',
        voiceName: 'alloy',
        customInstructions: 'Be a warm and capable companion.',
        vadConfig: {
          threshold: 0.6,
          prefixPaddingMs: 300,
          silenceDurationMs: 500,
        },
      });

      expect(session.sessionId).toContain('sess_oai_');
      expect(session.provider).toBe('openai');
      expect(session.model).toBe('gpt-4o-realtime-preview');
      expect(session.clientSecret).toMatch(/^ek_live_/);
      // Ensure master API key is never exposed in the client secret
      expect(session.clientSecret).not.toContain('sk-');
      expect(session.voiceConfig.voice).toBe('alloy');
      expect(session.voiceConfig.sampleRate).toBe(24000);
      expect(session.vadConfig.type).toBe('server_vad');
      expect(session.vadConfig.threshold).toBe(0.6);
      expect(new Date(session.expiresAt).getTime()).toBeGreaterThan(Date.now());
    });

    it('should format interruption response.cancel and input_audio_buffer.clear events', () => {
      const adapter = new OpenAIRealtimeAdapter();
      const cancelEvt = adapter.createCancelEvent({
        sessionId: 'sess_123',
        signalType: 'response.cancel',
        timestamp: 1730440000000,
        reason: 'user_barge_in',
      });

      expect(cancelEvt['type']).toBe('response.cancel');
      expect(cancelEvt['event_id']).toBeDefined();
      expect(cancelEvt['client_timestamp']).toBe(1730440000000);

      const clearEvt = adapter.createClearBufferEvent();
      expect(clearEvt['type']).toBe('input_audio_buffer.clear');

      const truncEvt = adapter.createTruncateEvent('item_999', 1500);
      expect(truncEvt['type']).toBe('conversation.item.truncate');
      expect(truncEvt['item_id']).toBe('item_999');
      expect(truncEvt['audio_end_ms']).toBe(1500);
    });
  });

  describe('Gemini Live API Adapter', () => {
    it('should build valid v1alpha BidiGenerateContentSetup message with speech_config', () => {
      const adapter = new GeminiLiveAdapter();
      const setup = adapter.buildSetupPayload(
        'System prompt for Aster',
        'Puck',
        [
          {
            name: 'search_photos',
            description: 'Search user photos',
            parameters: { type: 'object' },
          },
        ]
      );

      expect(setup.setup.model).toBe('models/gemini-2.0-flash-exp');
      expect(setup.setup.generation_config.response_modalities).toEqual(['AUDIO']);
      expect(
        setup.setup.generation_config.speech_config.voice_config.prebuilt_voice_config.voice_name
      ).toBe('Puck');
      expect(setup.setup.system_instruction?.parts[0]?.text).toBe('System prompt for Aster');
      expect(setup.setup.tools?.[0]?.function_declarations[0]?.name).toBe('search_photos');
    });

    it('should dispense scoped proxy session for Gemini Live without exposing master key', async () => {
      const adapter = new GeminiLiveAdapter();
      const session = await adapter.createEphemeralSession({
        userId: 'user_123',
        profileId: 'profile_nova',
        deviceId: 'device_macbook',
        voiceName: 'Charon',
      });

      expect(session.sessionId).toContain('sess_gemini_');
      expect(session.provider).toBe('gemini');
      expect(session.clientSecret).toMatch(/^gemini_live_/);
      expect(session.voiceConfig.voice).toBe('Charon');
      expect(session.voiceConfig.sampleRate).toBe(16000);
    });
  });

  describe('Quota Tracking & Concurrency Enforcement', () => {
    it('should reject session creation when concurrent limit is exceeded on same profile', async () => {
      const tracker = new VoiceQuotaTracker({ maxConcurrentSessions: 1 });
      tracker.registerSession('u1', 'p1', 'session_active_1');

      const check = tracker.checkEligibility('u1', 'p1');
      expect(check.allowed).toBe(false);
      expect(check.reason).toContain('Concurrent session limit reached');

      // Releasing session allows new session
      tracker.releaseSession('u1', 'p1', 'session_active_1');
      const checkAfter = tracker.checkEligibility('u1', 'p1');
      expect(checkAfter.allowed).toBe(true);
    });

    it('should reject session creation when daily minute quota is exhausted', () => {
      const tracker = new VoiceQuotaTracker({ dailyMinuteLimit: 30 });
      tracker.addUsage('u1', 'p1', 30 * 60); // 30 minutes consumed

      const check = tracker.checkEligibility('u1', 'p1');
      expect(check.allowed).toBe(false);
      expect(check.reason).toContain('Daily quota exhausted');
      expect(check.quotaStatus.isThrottled).toBe(true);
      expect(check.quotaStatus.remainingMinutesToday).toBe(0);
    });

    it('should enforce sliding window rate limiting on rapid requests', () => {
      const tracker = new VoiceQuotaTracker({ maxRequestsPerWindow: 3, rateLimitWindowMs: 5000 });
      tracker.registerSession('u1', 'p1', 's1');
      tracker.releaseSession('u1', 'p1', 's1');
      tracker.registerSession('u1', 'p1', 's2');
      tracker.releaseSession('u1', 'p1', 's2');
      tracker.registerSession('u1', 'p1', 's3');
      tracker.releaseSession('u1', 'p1', 's3');

      const check = tracker.checkEligibility('u1', 'p1');
      expect(check.allowed).toBe(false);
      expect(check.reason).toContain('Rate limit exceeded');
    });
  });

  describe('Graceful Degradation Fallback', () => {
    it('should gracefully degrade to secondary provider if primary provider is marked unhealthy', async () => {
      broker.setProviderHealth('openai', false, 'OpenAI 503 Service Unavailable');

      const session = await broker.createSession({
        userId: 'u_fall',
        profileId: 'p_fall',
        deviceId: 'dev_fall',
        preferredProvider: 'openai',
      });

      expect(session.fallbackActive).toBe(true);
      expect(session.provider).toBe('gemini');
      expect(session.fallbackReason).toContain('OpenAI 503 Service Unavailable');
    });

    it('should process user interruption signal and measure handling latency', async () => {
      const session = await broker.createSession({
        userId: 'u_int',
        profileId: 'p_int',
        deviceId: 'dev_int',
        preferredProvider: 'openai',
      });

      const result = await broker.handleInterruption({
        sessionId: session.sessionId,
        signalType: 'response.cancel',
        timestamp: Date.now(),
        reason: 'user_barge_in',
      });

      expect(result.handled).toBe(true);
      expect(result.sessionId).toBe(session.sessionId);
      expect(result.cancelledResponseId).toBeDefined();
      expect(result.clearedBufferBytes).toBeGreaterThan(0);
      expect(result.elapsedMs).toBeGreaterThanOrEqual(1);
    });
  });
});
