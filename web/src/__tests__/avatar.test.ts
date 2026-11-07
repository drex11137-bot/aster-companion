/**
 * avatar.test.ts
 * Verification tests for VisemeLipSyncEngine, AvatarCanvas specifications, and Customization
 */

import { test, beforeEach } from 'vitest';
import assert from 'node:assert/strict';
import { VisemeLipSyncEngine } from '../components/avatar/VisemeLipSyncEngine';
import { HAIR_COLOR_MAP, EYE_COLOR_MAP } from '../components/avatar/AvatarCanvas';

beforeEach(() => {
  if (typeof globalThis.window === 'undefined') {
    // @ts-expect-error Mocking window in node
    globalThis.window = globalThis;
  }
  if (typeof globalThis.requestAnimationFrame === 'undefined') {
    globalThis.requestAnimationFrame = (cb: FrameRequestCallback) =>
      setTimeout(() => cb(performance.now()), 16) as unknown as number;
  }
  if (typeof globalThis.cancelAnimationFrame === 'undefined') {
    globalThis.cancelAnimationFrame = (id: number) => clearTimeout(id);
  }
});

test('VisemeLipSyncEngine: initialization and default state', () => {
  const engine = new VisemeLipSyncEngine();
  assert.ok(engine, 'Engine should be instantiated');

  let receivedState: any = null;
  const unsubscribe = engine.subscribe((state) => {
    receivedState = state;
  });

  assert.ok(typeof unsubscribe === 'function', 'Subscribe returns unsubscribe function');
  assert.ok(receivedState === null || typeof receivedState === 'object');
  engine.stop();
  unsubscribe();
});

test('VisemeLipSyncEngine: biometrics and viseme bounds', async () => {
  const engine = new VisemeLipSyncEngine();

  let lastState: any = null;
  const unsubscribe = engine.subscribe((state) => {
    lastState = state;
  });

  // Allow a few ticks of animation frame or manual update
  await new Promise((resolve) => setTimeout(resolve, 150));

  assert.ok(lastState, 'Should have received state updates');
  assert.ok(typeof lastState.visemes.jawOpen === 'number', 'jawOpen is number');
  assert.ok(lastState.visemes.jawOpen >= 0 && lastState.visemes.jawOpen <= 1, 'jawOpen in [0,1]');
  assert.ok(lastState.visemes.mouthRound >= 0 && lastState.visemes.mouthRound <= 1, 'mouthRound in [0,1]');
  assert.ok(lastState.visemes.mouthSmile >= 0 && lastState.visemes.mouthSmile <= 1, 'mouthSmile in [0,1]');
  assert.ok(lastState.visemes.mouthStretch >= 0 && lastState.visemes.mouthStretch <= 1, 'mouthStretch in [0,1]');

  assert.ok(lastState.blinkLeft >= 0 && lastState.blinkLeft <= 1, 'blinkLeft in [0,1]');
  assert.ok(lastState.blinkRight >= 0 && lastState.blinkRight <= 1, 'blinkRight in [0,1]');
  assert.ok(lastState.breathScale > 0.95 && lastState.breathScale < 1.05, 'breathScale oscillates near 1.0');

  engine.stop();
  unsubscribe();
});

test('VisemeLipSyncEngine: simulated speech activates speaking state', async () => {
  const engine = new VisemeLipSyncEngine();

  let wasSpeaking = false;
  const unsubscribe = engine.subscribe((state) => {
    if (state.isSpeaking || state.visemes.jawOpen > 0) {
      wasSpeaking = true;
    }
  });

  // Trigger speech simulation
  await engine.simulateSpeech('Testing speech viseme synthesis', 500, 'Warm voice');

  await new Promise((resolve) => setTimeout(resolve, 200));

  engine.stopSpeechSimulation();
  engine.stop();
  unsubscribe();

  assert.ok(wasSpeaking, 'Speech simulation should activate speaking or mouth movement');
});

test('AvatarCanvas Specifications: Hair Color Hex Codes Match PRD v1.1', () => {
  assert.equal(HAIR_COLOR_MAP.Auburn.hex, '#9E4A28');
  assert.equal(HAIR_COLOR_MAP.Black.hex, '#1A1A1A');
  assert.equal(HAIR_COLOR_MAP.Brown.hex, '#4A2E1B');
  assert.equal(HAIR_COLOR_MAP.Blonde.hex, '#D6BE88');
  assert.equal(HAIR_COLOR_MAP.Silver.hex, '#9E9E9E');
});

test('AvatarCanvas Specifications: Eye Color Hex Codes Match PRD v1.1', () => {
  assert.equal(EYE_COLOR_MAP.Hazel.hex, '#8D6E3F');
  assert.equal(EYE_COLOR_MAP.Brown.hex, '#3E2723');
  assert.equal(EYE_COLOR_MAP.Blue.hex, '#5C768D');
  assert.equal(EYE_COLOR_MAP.Green.hex, '#4E6B4E');
  assert.equal(EYE_COLOR_MAP.Grey.hex, '#78909C');
});
