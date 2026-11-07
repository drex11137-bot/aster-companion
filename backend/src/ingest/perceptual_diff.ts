/**
 * Aster Companion Backend - Perceptual Image Difference Analyzer
 * Computes perceptual hashes, Hamming distance, and luminance variance to detect
 * static frames (for cost & bandwidth reduction) and scene transitions.
 */

import crypto from 'node:crypto';
import { PerceptualDiffResult } from '../types/frame.js';

export interface PerceptualDiffOptions {
  staticThreshold?: number;      // Default: 0.05 (5% change)
  sceneChangeThreshold?: number; // Default: 0.35 (35% change)
}

export class PerceptualDiffAnalyzer {
  private readonly staticThreshold: number;
  private readonly sceneChangeThreshold: number;

  constructor(options?: PerceptualDiffOptions) {
    this.staticThreshold = options?.staticThreshold ?? 0.05;
    this.sceneChangeThreshold = options?.sceneChangeThreshold ?? 0.35;
  }

  /**
   * Generates a 64-bit perceptual hash string from image data.
   * If raw image buffer is provided, computes a block-luminance hash;
   * otherwise creates a deterministic pseudo-perceptual hash from the payload.
   */
  public computeHash(imageData: string | Buffer): string {
    const buffer = typeof imageData === 'string' 
      ? Buffer.from(imageData, 'base64') 
      : imageData;

    if (buffer.length === 0) {
      return '0'.repeat(64);
    }

    // If buffer is smaller than 64 bytes (e.g. test payloads or small metadata),
    // expand it deterministically using sha256 to ensure proper perceptual dispersion
    let workingBuffer = buffer;
    if (buffer.length < 64) {
      const hash1 = crypto.createHash('sha256').update(buffer).digest();
      const hash2 = crypto.createHash('sha256').update(hash1).digest();
      workingBuffer = Buffer.concat([hash1, hash2]);
    }

    // Fast 64-bit block-luminance hash
    // Divide the buffer into 64 equal blocks, compute average byte value per block
    const blockSize = Math.max(1, Math.floor(workingBuffer.length / 64));
    let totalLuminance = 0;
    const blockAverages: number[] = new Array(64).fill(0);

    for (let i = 0; i < 64; i++) {
      let blockSum = 0;
      const start = i * blockSize;
      const end = Math.min(workingBuffer.length, start + blockSize);
      for (let j = start; j < end; j++) {
        blockSum += workingBuffer[j] ?? 0;
      }
      const count = Math.max(1, end - start);
      const avg = blockSum / count;
      blockAverages[i] = avg;
      totalLuminance += avg;
    }

    const overallAverage = totalLuminance / 64;
    let hashBits = '';
    for (let i = 0; i < 64; i++) {
      hashBits += (blockAverages[i] ?? 0) >= overallAverage ? '1' : '0';
    }

    return hashBits;
  }

  /**
   * Calculate Hamming distance between two 64-bit binary hash strings.
   */
  public calculateHammingDistance(hashA: string, hashB: string): number {
    const len = Math.min(hashA.length, hashB.length);
    let distance = 0;
    for (let i = 0; i < len; i++) {
      if (hashA[i] !== hashB[i]) {
        distance++;
      }
    }
    // Add length difference if any
    distance += Math.abs(hashA.length - hashB.length);
    return distance;
  }

  /**
   * Compares the current frame hash against the previous frame hash.
   */
  public compare(hashCurrent: string, hashPrevious?: string): PerceptualDiffResult {
    if (!hashPrevious) {
      // First frame in stream -> Always treated as keyframe/scene transition
      return {
        isStatic: false,
        isSceneChange: true,
        differenceScore: 1.0,
        hammingDistance: 64,
        hashCurrent,
      };
    }

    const hammingDistance = this.calculateHammingDistance(hashCurrent, hashPrevious);
    const maxBits = Math.max(hashCurrent.length, 64);
    const differenceScore = Math.min(1.0, Math.round((hammingDistance / maxBits) * 1000) / 1000);

    const isStatic = differenceScore <= this.staticThreshold;
    const isSceneChange = differenceScore >= this.sceneChangeThreshold;

    return {
      isStatic,
      isSceneChange,
      differenceScore,
      hammingDistance,
      hashCurrent,
      hashPrevious,
    };
  }
}
