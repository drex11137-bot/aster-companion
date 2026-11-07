// Supabase Edge Function: voice-broker
// Dispenses scoped short-lived ephemeral session tokens for OpenAI Realtime or Gemini Live.
// Follows PRD v1.1: master API keys are kept strictly server-side.

import { defaultVoiceBroker } from '../../../src/realtime/voice_broker.js';

Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, {
      status: 204,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      },
    });
  }

  try {
    const body = await req.json();
    const session = await defaultVoiceBroker.createSession({
      userId: body.userId,
      profileId: body.profileId,
      deviceId: body.deviceId,
      preferredProvider: body.preferredProvider,
      voiceName: body.voiceName,
      customInstructions: body.customInstructions,
    });

    return new Response(JSON.stringify(session), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
    });
  } catch (err: any) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 400,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
    });
  }
});
