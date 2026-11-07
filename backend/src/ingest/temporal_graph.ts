/**
 * Aster Companion Backend - Temporal Event Graph
 * Links continuous frame metadata to active session context across time.
 * Preserves chronological order, time deltas, and multi-modal citations.
 */

import crypto from 'node:crypto';
import { TemporalGraphNode, VisualUnderstandingMetadata } from '../types/frame.js';

export class TemporalEventGraph {
  // SessionId -> Array of TemporalGraphNodes (ordered chronologically)
  private sessionNodes = new Map<string, TemporalGraphNode[]>();
  private readonly maxNodesPerSession: number;

  constructor(maxNodesPerSession = 500) {
    this.maxNodesPerSession = maxNodesPerSession;
  }

  /**
   * Appends an analyzed frame node to the session's temporal timeline graph.
   */
  public linkFrame(params: {
    frameId: string;
    sessionId: string;
    profileId: string;
    deviceId: string;
    sequenceNumber: number;
    timestamp: number;
    activeApp?: string;
    metadata: VisualUnderstandingMetadata;
    isSceneChange: boolean;
  }): TemporalGraphNode {
    let nodes = this.sessionNodes.get(params.sessionId);
    if (!nodes) {
      nodes = [];
      this.sessionNodes.set(params.sessionId, nodes);
    }

    const previousNode = nodes.length > 0 ? nodes[nodes.length - 1] : undefined;
    const timeDeltaFromPreviousMs = previousNode
      ? Math.max(0, params.timestamp - previousNode.timestamp)
      : 0;

    let transitionType: TemporalGraphNode['transitionType'] = 'continuity';
    if (!previousNode) {
      transitionType = 'continuity';
    } else if (params.activeApp && previousNode.activeApp && params.activeApp !== previousNode.activeApp) {
      transitionType = 'app_switch';
    } else if (params.isSceneChange) {
      transitionType = 'tab_switch';
    }

    const nodeId = `tnode_${crypto.randomUUID()}`;
    const node: TemporalGraphNode = {
      nodeId,
      frameId: params.frameId,
      sessionId: params.sessionId,
      profileId: params.profileId,
      deviceId: params.deviceId,
      sequenceNumber: params.sequenceNumber,
      timestamp: params.timestamp,
      activeApp: params.activeApp,
      sceneSummary: params.metadata.sceneDescription,
      metadata: params.metadata,
      previousNodeId: previousNode?.nodeId,
      timeDeltaFromPreviousMs,
      transitionType,
    };

    nodes.push(node);

    // Bounded buffer pruning to prevent memory exhaustion
    if (nodes.length > this.maxNodesPerSession) {
      nodes.splice(0, nodes.length - this.maxNodesPerSession);
    }

    return node;
  }

  /**
   * Retrieves temporal event context for conversational reasoning.
   * e.g. "What was on the user's screen during the last 60 seconds?"
   */
  public queryRecentContext(sessionId: string, windowMs = 60_000): TemporalGraphNode[] {
    const nodes = this.sessionNodes.get(sessionId);
    if (!nodes || nodes.length === 0) return [];

    const latestTimestamp = nodes[nodes.length - 1]?.timestamp ?? Date.now();
    const cutoff = latestTimestamp - windowMs;

    return nodes.filter((n) => n.timestamp >= cutoff);
  }

  /**
   * Search historical visual metadata in session by text keyword or category.
   */
  public searchTimeline(
    sessionId: string,
    query: string
  ): Array<{ node: TemporalGraphNode; score: number }> {
    const nodes = this.sessionNodes.get(sessionId);
    if (!nodes) return [];

    const lowerQuery = query.toLowerCase();
    const matches: Array<{ node: TemporalGraphNode; score: number }> = [];

    for (const node of nodes) {
      let score = 0;
      if (node.sceneSummary.toLowerCase().includes(lowerQuery)) score += 0.5;
      if (node.activeApp?.toLowerCase().includes(lowerQuery)) score += 0.3;
      
      const textMatch = node.metadata.extractedText.some((t) =>
        t.toLowerCase().includes(lowerQuery)
      );
      if (textMatch) score += 0.6;

      if (score > 0) {
        matches.push({ node, score: Math.min(1.0, score) });
      }
    }

    return matches.sort((a, b) => b.score - a.score);
  }

  /**
   * Clear session nodes on session termination.
   */
  public clearSession(sessionId: string): void {
    this.sessionNodes.delete(sessionId);
  }
}
