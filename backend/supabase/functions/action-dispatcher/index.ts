// Supabase Edge Function: action-dispatcher
// Dispatches agentic actions with strict 4-tier risk classification,
// idempotency enforcement, and post-action verification.

import { defaultActionDispatcher } from '../../../src/actions/action_dispatcher.js';

Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, {
      status: 204,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Idempotency-Key',
      },
    });
  }

  try {
    const body = await req.json();
    const idempotencyKey = req.headers.get('x-idempotency-key') || body.idempotencyKey;

    const result = await defaultActionDispatcher.dispatchAction({
      actionName: body.actionName,
      profileId: body.profileId,
      userId: body.userId,
      deviceId: body.deviceId || 'device_edge',
      idempotencyKey,
      arguments: body.arguments || {},
      userConfirmed: body.userConfirmed,
      biometricToken: body.biometricToken,
    });

    return new Response(JSON.stringify(result), {
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
