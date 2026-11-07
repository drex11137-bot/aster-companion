/**
 * Aster Companion Backend - Master API & Edge Functions Entrypoint
 * Unifies Voice Broker, Frame Ingest, Action Dispatcher, and Proactivity Engine.
 */

import http from 'node:http';
import { VoiceBroker, defaultVoiceBroker } from './realtime/voice_broker.js';
import { FrameIngestPipeline, defaultFrameIngest } from './ingest/frame_ingest.js';
import { ActionDispatcher, defaultActionDispatcher } from './actions/action_dispatcher.js';
import { ProactivityEngine, defaultProactivityEngine } from './proactive/proactivity_engine.js';
import { defaultDbClient } from './db/supabase_client.js';

export {
  VoiceBroker,
  defaultVoiceBroker,
  FrameIngestPipeline,
  defaultFrameIngest,
  ActionDispatcher,
  defaultActionDispatcher,
  ProactivityEngine,
  defaultProactivityEngine,
};

export * from './types/index.js';

export function createHttpServer(options?: {
  voiceBroker?: VoiceBroker;
  frameIngest?: FrameIngestPipeline;
  actionDispatcher?: ActionDispatcher;
  proactivityEngine?: ProactivityEngine;
}): http.Server {
  const vb = options?.voiceBroker ?? defaultVoiceBroker;
  const fi = options?.frameIngest ?? defaultFrameIngest;
  const ad = options?.actionDispatcher ?? defaultActionDispatcher;
  const pe = options?.proactivityEngine ?? defaultProactivityEngine;

  return http.createServer(async (req, res) => {
    // Set CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Idempotency-Key');

    if (req.method === 'OPTIONS') {
      res.writeHead(204);
      res.end();
      return;
    }

    const url = new URL(req.url || '/', `http://${req.headers.host || 'localhost'}`);

    // Helper to read JSON body
    const readBody = async (): Promise<Record<string, unknown>> => {
      return new Promise((resolve, reject) => {
        let body = '';
        req.on('data', (chunk) => (body += chunk));
        req.on('end', () => {
          try {
            resolve(body ? JSON.parse(body) : {});
          } catch (err) {
            reject(new Error('Invalid JSON payload'));
          }
        });
        req.on('error', reject);
      });
    };

    try {
      // 1. Health check
      if (url.pathname === '/health' || url.pathname === '/') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(
          JSON.stringify({
            service: 'aster-companion-backend',
            status: 'HEALTHY',
            version: '1.1.0',
            liveDatabase: defaultDbClient.isLiveDatabase(),
            timestamp: new Date().toISOString(),
          })
        );
        return;
      }

      // 2. Real-Time Voice Ephemeral Session Dispenser
      if (url.pathname === '/api/realtime/session' && req.method === 'POST') {
        const body = await readBody();
        const session = await vb.createSession({
          userId: String(body['userId'] || 'anonymous_user'),
          profileId: String(body['profileId'] || 'default_profile'),
          deviceId: String(body['deviceId'] || 'default_device'),
          preferredProvider: body['preferredProvider'] as any,
          voiceName: body['voiceName'] as string,
          customInstructions: body['customInstructions'] as string,
        });

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(session));
        return;
      }

      // 3. Voice Interruption Signal Handler
      if (url.pathname === '/api/realtime/interrupt' && req.method === 'POST') {
        const body = await readBody();
        const result = await vb.handleInterruption({
          sessionId: String(body['sessionId']),
          signalType: body['signalType'] as any || 'response.cancel',
          timestamp: Number(body['timestamp'] || Date.now()),
          reason: String(body['reason'] || 'barge_in'),
        });

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(result));
        return;
      }

      // 4. Continuous Frame Ingestion
      if (url.pathname === '/api/ingest/frame' && req.method === 'POST') {
        const body = await readBody();
        const result = await fi.ingestFrame(body as any);

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(result));
        return;
      }

      // 5. Agentic Action Dispatcher
      if (url.pathname === '/api/actions/dispatch' && req.method === 'POST') {
        const body = await readBody();
        const idempotencyKey =
          (req.headers['x-idempotency-key'] as string) || (body['idempotencyKey'] as string);

        const result = await ad.dispatchAction({
          actionName: String(body['actionName']),
          profileId: String(body['profileId']),
          userId: String(body['userId']),
          deviceId: String(body['deviceId'] || 'web'),
          idempotencyKey,
          arguments: (body['arguments'] as Record<string, unknown>) || {},
          userConfirmed: Boolean(body['userConfirmed']),
          biometricToken: body['biometricToken'] as string,
        });

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(result));
        return;
      }

      // 6. Action Undo / Rollback
      if (url.pathname === '/api/actions/undo' && req.method === 'POST') {
        const body = await readBody();
        const result = await ad.undoAction(
          String(body['actionId']),
          String(body['profileId'])
        );

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(result));
        return;
      }

      // 7. Proactivity Scoring & Evaluation
      if (url.pathname === '/api/proactive/evaluate' && req.method === 'POST') {
        const body = await readBody();
        const result = pe.evaluateCandidate(body as any);

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(result));
        return;
      }

      // Not Found
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Endpoint not found' }));
    } catch (err) {
      console.error('[BackendServer] Error handling request:', err);
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(
        JSON.stringify({
          error: err instanceof Error ? err.message : 'Internal Server Error',
        })
      );
    }
  });
}

// Start standalone server when executed directly
if (process.argv[1]?.endsWith('index.ts') || process.argv[1]?.endsWith('index.js')) {
  const PORT = Number(process.env.PORT || 8000);
  const server = createHttpServer();
  server.listen(PORT, () => {
    console.log(`[Aster Companion Backend] Server listening on port ${PORT}`);
  });
}
