import { describe, it, expect, beforeEach } from 'vitest';
import { FrameIngestPipeline } from '../src/ingest/frame_ingest.js';
import { PerceptualDiffAnalyzer } from '../src/ingest/perceptual_diff.js';

describe('FrameIngestPipeline & Visual Perception Pipeline', () => {
  let pipeline: FrameIngestPipeline;

  beforeEach(() => {
    pipeline = new FrameIngestPipeline();
  });

  describe('Monotonic Sequence & Packet Drop Gap Detection', () => {
    it('should ingest sequential frames without gaps when sequence_number == last_sequence + 1', async () => {
      const baseTime = Date.now();
      const frame1 = await pipeline.ingestFrame({
        deviceId: 'dev_phone_1',
        sessionId: 'sess_vis_1',
        profileId: 'prof_1',
        sequenceNumber: 1,
        captureTimestamp: baseTime,
        uploadTimestamp: baseTime + 10,
        dimensions: { width: 1080, height: 2400 },
        orientation: 'portrait',
        imageData: Buffer.from('image_frame_data_sequence_1').toString('base64'),
      });

      expect(frame1.status).toBe('ANALYZED');
      expect(frame1.sequenceNumber).toBe(1);
      expect(frame1.gapInfo).toBeUndefined();

      const frame2 = await pipeline.ingestFrame({
        deviceId: 'dev_phone_1',
        sessionId: 'sess_vis_1',
        profileId: 'prof_1',
        sequenceNumber: 2,
        captureTimestamp: baseTime + 33, // ~30 FPS
        uploadTimestamp: baseTime + 43,
        dimensions: { width: 1080, height: 2400 },
        orientation: 'portrait',
        imageData: Buffer.from('image_frame_data_sequence_2_updated').toString('base64'),
      });

      expect(frame2.status).toBe('ANALYZED');
      expect(frame2.sequenceNumber).toBe(2);
      expect(frame2.gapInfo).toBeUndefined();
    });

    it('should detect dropped packets when sequence_number > last_sequence + 1 and mark gap interval', async () => {
      const baseTime = Date.now();

      // Send frame 1
      await pipeline.ingestFrame({
        deviceId: 'dev_phone_gap',
        sessionId: 'sess_gap_1',
        profileId: 'prof_1',
        sequenceNumber: 1,
        captureTimestamp: baseTime,
        uploadTimestamp: baseTime + 5,
        dimensions: { width: 1080, height: 2400 },
        orientation: 'portrait',
        imageData: Buffer.from('frame_1').toString('base64'),
      });

      // Frame 2 and 3 dropped on network; frame 4 arrives
      const frame4 = await pipeline.ingestFrame({
        deviceId: 'dev_phone_gap',
        sessionId: 'sess_gap_1',
        profileId: 'prof_1',
        sequenceNumber: 4,
        captureTimestamp: baseTime + 100,
        uploadTimestamp: baseTime + 110,
        dimensions: { width: 1080, height: 2400 },
        orientation: 'portrait',
        imageData: Buffer.from('frame_4_new').toString('base64'),
      });

      expect(frame4.gapInfo).toBeDefined();
      expect(frame4.gapInfo?.detected).toBe(true);
      expect(frame4.gapInfo?.expectedSequence).toBe(2);
      expect(frame4.gapInfo?.receivedSequence).toBe(4);
      expect(frame4.gapInfo?.lostFramesCount).toBe(2);
      expect(frame4.gapInfo?.missingInterval).toEqual([2, 3]);
      expect(frame4.metrics.totalGapsDetected).toBe(1);
      expect(frame4.metrics.totalLostFrames).toBe(2);
      expect(frame4.metrics.continuityRatio).toBeLessThan(1.0);
    });

    it('should reject duplicate frames with identical or lower sequence numbers', async () => {
      const baseTime = Date.now();
      await pipeline.ingestFrame({
        deviceId: 'dev_dup',
        sessionId: 'sess_dup',
        profileId: 'prof_1',
        sequenceNumber: 5,
        captureTimestamp: baseTime,
        uploadTimestamp: baseTime + 5,
        dimensions: { width: 1080, height: 2400 },
        orientation: 'portrait',
        imageData: Buffer.from('frame_5').toString('base64'),
      });

      // Duplicate delivery
      const dup = await pipeline.ingestFrame({
        deviceId: 'dev_dup',
        sessionId: 'sess_dup',
        profileId: 'prof_1',
        sequenceNumber: 5,
        captureTimestamp: baseTime,
        uploadTimestamp: baseTime + 5,
        dimensions: { width: 1080, height: 2400 },
        orientation: 'portrait',
        imageData: Buffer.from('frame_5').toString('base64'),
      });

      expect(dup.status).toBe('DUPLICATE_REJECTED');
    });
  });

  describe('Perceptual Difference & Static Frame Skipping', () => {
    it('should classify identical frames as STATIC_SKIPPED to conserve bandwidth and inference cost', async () => {
      const baseTime = Date.now();
      const identicalPayload = Buffer.from('constant_static_screen_content').toString('base64');

      const initial = await pipeline.ingestFrame({
        deviceId: 'dev_static',
        sessionId: 'sess_static',
        profileId: 'prof_1',
        sequenceNumber: 1,
        captureTimestamp: baseTime,
        uploadTimestamp: baseTime + 5,
        dimensions: { width: 1080, height: 2400 },
        orientation: 'portrait',
        imageData: identicalPayload,
      });

      expect(initial.status).toBe('ANALYZED');

      // Next sequential frame with identical screen content
      const staticFrame = await pipeline.ingestFrame({
        deviceId: 'dev_static',
        sessionId: 'sess_static',
        profileId: 'prof_1',
        sequenceNumber: 2,
        captureTimestamp: baseTime + 33,
        uploadTimestamp: baseTime + 38,
        dimensions: { width: 1080, height: 2400 },
        orientation: 'portrait',
        imageData: identicalPayload,
      });

      expect(staticFrame.status).toBe('STATIC_SKIPPED');
      expect(staticFrame.diffResult.isStatic).toBe(true);
      expect(staticFrame.diffResult.differenceScore).toBe(0);
      expect(staticFrame.metrics.totalSkippedStaticFrames).toBe(1);
    });
  });

  describe('Temporal Event Graph & OCR Linking', () => {
    it('should extract visual metadata, link temporal graph node, and support timeline context querying', async () => {
      const baseTime = Date.now();
      const result = await pipeline.ingestFrame({
        deviceId: 'dev_graph',
        sessionId: 'sess_graph_1',
        profileId: 'prof_1',
        sequenceNumber: 1,
        captureTimestamp: baseTime,
        uploadTimestamp: baseTime + 5,
        dimensions: { width: 1080, height: 2400 },
        orientation: 'portrait',
        imageData: Buffer.from('shopping_shopify_sneakers_screen').toString('base64'),
        activeApp: {
          packageName: 'com.shopify.arrive',
          windowTitle: 'Shopify Shopping',
        },
      });

      expect(result.status).toBe('ANALYZED');
      expect(result.visualMetadata?.primaryCategory).toBe('shopping');
      expect(result.visualMetadata?.sceneDescription).toContain('shopping');
      expect(result.temporalNode?.activeApp).toBe('com.shopify.arrive');

      const graph = pipeline.getTemporalGraph();
      const recent = graph.queryRecentContext('sess_graph_1', 60_000);
      expect(recent.length).toBe(1);
      expect(recent[0]?.nodeId).toBe(result.temporalNode?.nodeId);

      const searchResults = graph.searchTimeline('sess_graph_1', 'shopify');
      expect(searchResults.length).toBeGreaterThan(0);
      expect(searchResults[0]?.node.nodeId).toBe(result.temporalNode?.nodeId);
    });
  });

  describe('FPS Instrumentation (PRD §5.3)', () => {
    it('should measure capture FPS, upload FPS, ingest FPS, and analysis FPS separately', async () => {
      const baseTime = Date.now();

      // Feed 4 successive frames at simulated ~30 FPS intervals (33ms)
      for (let i = 1; i <= 4; i++) {
        await pipeline.ingestFrame({
          deviceId: 'dev_fps',
          sessionId: 'sess_fps',
          profileId: 'prof_1',
          sequenceNumber: i,
          captureTimestamp: baseTime + (i - 1) * 33,
          uploadTimestamp: baseTime + (i - 1) * 33 + 10,
          dimensions: { width: 1080, height: 2400 },
          orientation: 'portrait',
          imageData: Buffer.from(`unique_frame_content_${i}`).toString('base64'),
        });
      }

      const streamKey = 'dev_fps:sess_fps';
      // Ingest 5th frame to check FPS calculations
      const fifth = await pipeline.ingestFrame({
        deviceId: 'dev_fps',
        sessionId: 'sess_fps',
        profileId: 'prof_1',
        sequenceNumber: 5,
        captureTimestamp: baseTime + 4 * 33,
        uploadTimestamp: baseTime + 4 * 33 + 10,
        dimensions: { width: 1080, height: 2400 },
        orientation: 'portrait',
        imageData: Buffer.from('unique_frame_content_5').toString('base64'),
      });

      // Capture rate should approximate ~30 FPS (1000 / 33.3ms)
      expect(fifth.metrics.captureFps).toBeGreaterThan(25);
      expect(fifth.metrics.captureFps).toBeLessThan(35);
      expect(fifth.metrics.uploadFps).toBeGreaterThan(0);
      expect(fifth.metrics.ingestFps).toBeGreaterThanOrEqual(0);
      expect(fifth.metrics.totalAnalyzedFrames).toBe(5);
    });
  });
});
