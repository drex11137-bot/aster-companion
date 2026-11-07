/**
 * Aster Companion - Untrusted Content Sanitizer & Demarcation Engine
 * File: backend/src/security/untrusted_content_sanitizer.ts
 *
 * Implements defenses against indirect prompt injection (OWASP LLM01:2025)
 * for screen OCR, audio transcripts, notifications, and external payloads.
 */

import type {
  ContentTrustLevel,
  PerceptionPayload,
  PerceptionSource,
  SanitizedObservation,
} from './types.ts';

interface ThreatPattern {
  name: string;
  category: 'instruction_override' | 'role_spoofing' | 'tool_injection' | 'memory_sabotage' | 'exfiltration';
  pattern: RegExp;
  description: string;
}

export const PROMPT_INJECTION_PATTERNS: ThreatPattern[] = [
  {
    name: 'Instruction Override',
    category: 'instruction_override',
    pattern: /\b(ignore\s+(all\s+)?(previous|prior|above)\s+instructions|disregard\s+(all\s+)?(previous|prior)\s+rules|system\s+override|forget\s+(all\s+)?prior\s+instructions|you\s+are\s+now\s+in\s+developer\s+mode|dan\s+mode\s+enabled|new\s+system\s+directive:?)\b/gi,
    description: 'Attempts to erase prior instructions or force a rogue persona',
  },
  {
    name: 'Role Spoofing Delimiter',
    category: 'role_spoofing',
    pattern: /(<\|im_start\|>|<\|im_end\|>|\[INST\]|\[\/INST\]|<<SYS>>|<\/SYS>|<system>|<\/system>|\b(System|Human|Assistant|User)\s*:)/gi,
    description: 'Attempts to fake chat conversation turns or system prompt boundaries',
  },
  {
    name: 'Tool Command Syntax Injection',
    category: 'tool_injection',
    pattern: /(<tool_call>|<\/tool_call>|{\s*"action"\s*:|{\s*"tool"\s*:|"action_name"\s*:|execute_action\(|call_tool\(|invoke_tool\()/gi,
    description: 'Attempts to synthesize tool command invocations inside text',
  },
  {
    name: 'Memory Sabotage Directive',
    category: 'memory_sabotage',
    pattern: /\b(delete\s+(all\s+)?memories|wipe\s+(the\s+)?database|purge\s+all\s+user\s+data|clear\s+all\s+companion\s+memories|drop\s+table\s+memories)\b/gi,
    description: 'Malicious instructions to erase or compromise companion memory store',
  },
  {
    name: 'Data Exfiltration Trigger',
    category: 'exfiltration',
    pattern: /(exfiltrate|send\s+(all\s+)?(memories|passwords|tokens|keys)\s+to\s+http|curl\s+https?:\/\/|fetch\(["']https?:\/\/|https?:\/\/[^\s"'<>]+|webhook\.site)/gi,
    description: 'Attempts to transmit sensitive context to external endpoints',
  },
];

export class UntrustedContentSanitizer {
  /**
   * Sanitizes perception payload (screen OCR, audio transcript, clipboard)
   * tagging it as UNTRUSTED_OBSERVATION and detecting adversarial injections.
   */
  public static sanitizeObservation(payload: PerceptionPayload): SanitizedObservation {
    const raw = payload.content ?? '';
    const detectedThreats: string[] = [];

    // Scan for adversarial patterns
    for (const threat of PROMPT_INJECTION_PATTERNS) {
      threat.pattern.lastIndex = 0;
      if (threat.pattern.test(raw)) {
        detectedThreats.push(`${threat.name}: ${threat.description}`);
      }
    }

    // Escape nested demarcation delimiters to prevent container escape
    const escaped = raw
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');

    // Neutralize dangerous tokens
    let sanitizedContent = raw;
    for (const threat of PROMPT_INJECTION_PATTERNS) {
      threat.pattern.lastIndex = 0;
      sanitizedContent = sanitizedContent.replace(
        threat.pattern,
        (match) => {
          if (/https?:\/\//i.test(match) || /webhook\.site/i.test(match)) {
            return '[UNTRUSTED_URL_REDACTED]';
          }
          return `[UNTRUSTED_${threat.category.toUpperCase()}_REDACTED]`;
        }
      );
    }

    // Strict demarcation sandbox wrapper
    const demarcatedContent = 
      `<untrusted_observation origin="${payload.source}" trust_level="UNTRUSTED_OBSERVATION">\n` +
      `${escaped}\n` +
      `</untrusted_observation>`;

    return {
      source: payload.source,
      trustLevel: 'UNTRUSTED_OBSERVATION',
      safeContent: sanitizedContent,
      originalLength: raw.length,
      injectionDetected: detectedThreats.length > 0,
      detectedThreats,
      demarcatedContent,
    };
  }

  /**
   * Resolves the default trust level based on observation source.
   */
  public static resolveTrustLevel(source: PerceptionSource): ContentTrustLevel {
    switch (source) {
      case 'user_chat':
      case 'verified_user_voice':
        return 'AUTHENTICATED_USER_INTENT';
      case 'screen_ocr':
      case 'audio_transcript':
      case 'clipboard':
      case 'external_api':
      case 'system_notification':
      default:
        return 'UNTRUSTED_OBSERVATION';
    }
  }
}
