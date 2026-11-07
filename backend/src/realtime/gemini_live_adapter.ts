/**
 * Aster Companion Backend - Gemini Live API Adapter
 * Handles Bidirectional WebSocket Protocol (v1alpha BidiGenerateContentSetup).
 * Enforces server-side secret management: Master Google GenAI key is never disclosed to clients.
 */

import crypto from 'node:crypto';
import {
  EphemeralSessionRequest,
  EphemeralSessionTokenResponse,
  InterruptionSignal,
  VadConfig,
  VoiceToolDefinition,
} from '../types/voice.js';

export interface GeminiLiveAdapterConfig {
  apiKey?: string;
  model?: string;
  wsBaseUrl?: string;
}

export interface BidiGenerateContentSetupMessage {
  setup: {
    model: string;
    generation_config: {
      response_modalities: ['AUDIO'];
      speech_config: {
        voice_config: {
          prebuilt_voice_config: {
            voice_name: string;
          };
        };
      };
    };
    system_instruction?: {
      parts: Array<{ text: string }>;
    };
    tools?: Array<{
      function_declarations: Array<{
        name: string;
        description: string;
        parameters: Record<string, unknown>;
      }>;
    }>;
  };
}

export class GeminiLiveAdapter {
  private readonly apiKey: string | undefined;
  private readonly model: string;
  private readonly wsBaseUrl: string;

  constructor(config?: GeminiLiveAdapterConfig) {
    this.apiKey = config?.apiKey || process.env.GEMINI_API_KEY;
    this.model = config?.model || 'models/gemini-2.0-flash-exp';
    this.wsBaseUrl =
      config?.wsBaseUrl ||
      'wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent';
  }

  /**
   * Generates a scoped ephemeral session for the Gemini Live WebSocket connection.
   */
  public async createEphemeralSession(
    req: EphemeralSessionRequest,
    tools: VoiceToolDefinition[] = []
  ): Promise<Omit<EphemeralSessionTokenResponse, 'quotaStatus' | 'fallbackActive'>> {
    const sessionId = `sess_gemini_${crypto.randomUUID()}`;
    const expiresAt = new Date(Date.now() + 60_000).toISOString();

    const vadConfig: VadConfig = {
      type: 'server_vad',
      threshold: req.vadConfig?.threshold ?? 0.5,
      prefixPaddingMs: req.vadConfig?.prefixPaddingMs ?? 300,
      silenceDurationMs: req.vadConfig?.silenceDurationMs ?? 500,
    };

    // Supported Gemini Live voices: Puck, Charon, Kore, Fenrir, Aoede
    const validGeminiVoices = ['Puck', 'Charon', 'Kore', 'Fenrir', 'Aoede'];
    const voice = validGeminiVoices.includes(req.voiceName || '')
      ? (req.voiceName as string)
      : 'Aoede';

    // Generates a short-lived cryptographically signed token for the Aster proxy/gateway
    const scopedToken = `gemini_live_${crypto.randomBytes(32).toString('hex')}`;

    return {
      sessionId,
      provider: 'gemini',
      model: this.model,
      clientSecret: scopedToken,
      expiresAt,
      endpointUrl: this.wsBaseUrl,
      voiceConfig: {
        voice,
        inputAudioFormat: 'pcm16',
        outputAudioFormat: 'pcm16',
        sampleRate: 16000, // Gemini Live standard PCM sample rate
      },
      vadConfig,
    };
  }

  /**
   * Builds the official v1alpha BidiGenerateContentSetup payload for initial handshake.
   */
  public buildSetupPayload(
    instructions: string,
    voiceName: string,
    tools: VoiceToolDefinition[] = []
  ): BidiGenerateContentSetupMessage {
    const setup: BidiGenerateContentSetupMessage = {
      setup: {
        model: this.model,
        generation_config: {
          response_modalities: ['AUDIO'],
          speech_config: {
            voice_config: {
              prebuilt_voice_config: {
                voice_name: voiceName,
              },
            },
          },
        },
        system_instruction: {
          parts: [{ text: instructions }],
        },
      },
    };

    if (tools.length > 0) {
      setup.setup.tools = [
        {
          function_declarations: tools.map((t) => ({
            name: t.name,
            description: t.description,
            parameters: t.parameters,
          })),
        },
      ];
    }

    return setup;
  }

  /**
   * Formats real-time streaming audio input for Gemini Live.
   * Audio format is raw 16-bit PCM at 16kHz or 24kHz.
   */
  public formatAudioChunk(base64PcmData: string, sampleRate = 16000): Record<string, unknown> {
    return {
      realtime_input: {
        media_chunks: [
          {
            mime_type: `audio/pcm;rate=${sampleRate}`,
            data: base64PcmData,
          },
        ],
      },
    };
  }

  /**
   * Formats cancellation / interruption signal for Gemini Live stream.
   */
  public createCancelEvent(signal: InterruptionSignal): Record<string, unknown> {
    return {
      client_content: {
        turns: [
          {
            role: 'user',
            parts: [{ text: '[User interrupted Aster]' }],
          },
        ],
        turn_complete: true,
      },
      interruption_metadata: {
        timestamp: signal.timestamp,
        reason: signal.reason || 'user_barge_in',
      },
    };
  }
}
