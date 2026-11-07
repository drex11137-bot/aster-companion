/**
 * Aster Companion - Sensitive Inference Detection & Guard
 * File: backend/src/memory/sensitive_inference_guard.ts
 *
 * Implements PRD v1.1 Section 14.4 & Section 16 requirements:
 * Strict distinction between explicitly stated user facts and model inferences.
 * Refuses sensitive inferences (e.g., religion, health/medical speculations,
 * political leanings, sexual orientation, genetic/biometric data)
 * without an affirmative, explicit user statement.
 */

import {
  CandidateMemoryInput,
  FactType,
  SensitivityLevel,
  SensitiveInferenceRefusedError,
} from './types.js';

export interface SensitiveDomainRule {
  domain: string;
  category: 'religion' | 'health_medical' | 'political' | 'sexual_orientation' | 'biometric_genetic' | 'financial_secrets';
  patterns: RegExp[];
  recommendedSensitivity: SensitivityLevel;
  explanation: string;
}

export const SENSITIVE_DOMAINS: SensitiveDomainRule[] = [
  {
    domain: 'Religion and Spiritual Beliefs',
    category: 'religion',
    patterns: [
      /\b(religion|religious|faith|spirituality|christian|christianity|catholic|protestant|orthodox|baptist|evangelical)\b/i,
      /\b(muslim|islam|islamic|sunni|shia|quran|koran|mosque|halal|ramadan)\b/i,
      /\b(jewish|judaism|torah|talmud|synagogue|kosher|rabbi|shabbat|yom kippur)\b/i,
      /\b(hindu|hinduism|vedas|temple|puja|brahmin|krishna|shiva)\b/i,
      /\b(buddhist|buddhism|zen|dharma|monastery|karma)\b/i,
      /\b(atheist|atheism|agnostic|agnosticism|scientology|pagan|wicca)\b/i,
    ],
    recommendedSensitivity: 'high',
    explanation: 'Religious and philosophical beliefs are sensitive personal data under GDPR/NDPA.',
  },
  {
    domain: 'Health, Disease, and Medical Speculation',
    category: 'health_medical',
    patterns: [
      /\b(diagnosis|diagnosed|symptom|illness|disease|infection|syndrome|disorder|pathology)\b/i,
      /\b(depression|depressed|anxiety|bipolar|schizophrenia|adhd|autism|ptsd|ocd|dementia|alzheimer)\b/i,
      /\b(cancer|tumor|chemotherapy|oncology|leukemia|carcinoma)\b/i,
      /\b(diabetes|diabetic|insulin|blood sugar|glucose|metformin)\b/i,
      /\b(hypertension|heart disease|cardiac|stroke|blood pressure|asthma|inhaler)\b/i,
      /\b(hiv|aids|std|sti|hepatitis|pregnant|pregnancy|fertility|miscarriage|abortion)\b/i,
      /\b(prescription|antidepressant|medication|dosage|psychiatrist|therapy session)\b/i,
      /\b(suicidal|suicide|self-harm|overdose|substance abuse|addiction|alcoholic)\b/i,
    ],
    recommendedSensitivity: 'restricted',
    explanation: 'Health condition or medical speculation is strictly protected health data.',
  },
  {
    domain: 'Political Opinions and Affiliations',
    category: 'political',
    patterns: [
      /\b(democrat|republican|gop|socialist|conservative|labour|liberal|libertarian|communist|marxist)\b/i,
      /\b(political party|voter|ballot|presidential candidate|campaign donor|political protest)\b/i,
    ],
    recommendedSensitivity: 'high',
    explanation: 'Political opinions and voting leanings are protected personal beliefs.',
  },
  {
    domain: 'Sexual Orientation and Sex Life',
    category: 'sexual_orientation',
    patterns: [
      /\b(sexual orientation|homosexual|heterosexual|gay|lesbian|bisexual|queer|asexual|pansexual)\b/i,
      /\b(sexuality|sex life|intimate partner preference)\b/i,
    ],
    recommendedSensitivity: 'restricted',
    explanation: 'Sexual orientation and private intimate life are sensitive categories.',
  },
  {
    domain: 'Genetic, Biometric and Racial Data',
    category: 'biometric_genetic',
    patterns: [
      /\b(genetic data|dna profile|biometric identification|ethnic origin|racial identity)\b/i,
    ],
    recommendedSensitivity: 'restricted',
    explanation: 'Biometric and genetic inferences carry severe privacy and discrimination risk.',
  },
  {
    domain: 'Financial Credentials and Passwords',
    category: 'financial_secrets',
    patterns: [
      /\b(credit card number|cvv|pin code|security code|bank account password|secret seed phrase|private key)\b/i,
    ],
    recommendedSensitivity: 'restricted',
    explanation: 'Raw credentials and financial secrets must not be stored in long-term memory.',
  },
];

export interface ValidationResult {
  isAllowed: boolean;
  sensitiveCategoryDetected?: string;
  matchedDomain?: string;
  sensitivityLevel: SensitivityLevel;
  refusalReason?: string;
}

export class SensitiveInferenceGuard {
  /**
   * Evaluates a candidate memory against PRD v1.1 epistemic rules.
   * Throws SensitiveInferenceRefusedError if the memory is an unverified inference
   * into a sensitive domain without an explicit user statement.
   */
  public static validate(candidate: CandidateMemoryInput): ValidationResult {
    const text = candidate.content.trim();
    const factType: FactType = candidate.factType;

    for (const rule of SENSITIVE_DOMAINS) {
      const isMatched = rule.patterns.some((pattern) => pattern.test(text));

      if (isMatched) {
        if (factType === 'inference') {
          // Speculative inference into sensitive topics is strictly prohibited by PRD v1.1
          const error = new SensitiveInferenceRefusedError(
            `Cannot record inferred memory concerning "${rule.domain}". ${rule.explanation}`,
            rule.category,
            text
          );
          throw error;
        }

        // Explicit user statements are allowed, but elevated to higher sensitivity
        const effectiveSensitivity: SensitivityLevel =
          candidate.sensitivityLevel === 'restricted'
            ? 'restricted'
            : rule.recommendedSensitivity;

        return {
          isAllowed: true,
          sensitiveCategoryDetected: rule.category,
          matchedDomain: rule.domain,
          sensitivityLevel: effectiveSensitivity,
        };
      }
    }

    // Default: non-sensitive domain
    return {
      isAllowed: true,
      sensitivityLevel: candidate.sensitivityLevel || 'standard',
    };
  }

  /**
   * Helper to check if a given content string matches sensitive keywords
   */
  public static detectSensitiveCategory(content: string): string | null {
    for (const rule of SENSITIVE_DOMAINS) {
      if (rule.patterns.some((pattern) => pattern.test(content))) {
        return rule.category;
      }
    }
    return null;
  }
}
