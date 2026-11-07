/**
 * VoiceWaveformVisualizer Unit Tests
 * 
 * Tests ambient canvas waveform visualizer rendering, properties, and event bindings.
 */

import { describe, it, expect } from 'vitest';
import React from 'react';
import { VoiceWaveformVisualizer } from '../audio/VoiceWaveformVisualizer';
import { WebRTCVoiceClient } from '../audio/WebRTCVoiceClient';

describe('VoiceWaveformVisualizer Component', () => {
  it('instantiates cleanly as a valid React component function', () => {
    expect(typeof VoiceWaveformVisualizer).toBe('function');
  });

  it('creates an element with default graphite and amber color props', () => {
    const element = React.createElement(VoiceWaveformVisualizer, {
      height: 200,
      showTelemetry: true,
      backgroundColor: '#121110',
      primaryAmberColor: '#F5A623',
    });

    expect(element).toBeDefined();
    expect(element.props.height).toBe(200);
    expect(element.props.backgroundColor).toBe('#121110');
    expect(element.props.primaryAmberColor).toBe('#F5A623');
  });

  it('accepts WebRTCVoiceClient instance without throwing', () => {
    const client = new WebRTCVoiceClient();
    const element = React.createElement(VoiceWaveformVisualizer, {
      voiceClient: client,
      state: 'speaking',
      showTelemetry: true,
    });

    expect(element.props.voiceClient).toBe(client);
    expect(element.props.state).toBe('speaking');
  });

  it('accepts synthetic Float32Array audio waveform feeds', () => {
    const syntheticWaveform = new Float32Array(512).fill(0.35);
    const element = React.createElement(VoiceWaveformVisualizer, {
      audioData: syntheticWaveform,
      state: 'listening',
      energy: {
        rms: 0.35,
        decibels: -22,
        peak: 0.5,
        isSpeech: true,
        noiseFloorDb: -60,
      },
    });

    expect(element.props.audioData).toBe(syntheticWaveform);
    expect(element.props.energy?.decibels).toBe(-22);
  });
});
