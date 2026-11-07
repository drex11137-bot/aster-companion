/**
 * Aster Companion - External Integrations & OAuth Service
 * index.ts
 *
 * Unified export surface for all integration modules:
 * - OAuth 2.0 PKCE Flow & Refresh Token Encryption (RFC 7636, RFC 9700)
 * - Google Integrations (Photos Picker, Drive, Gmail, Calendar, Contacts)
 * - Shopify Storefront API GraphQL Client & Safe Non-Autonomous Checkout
 * - Centralized Integration Manager, Scope Auditing & RFC 7009 Revocation
 */

export * from './oauth_pkce_handler.js';
export * from './google_integrations.js';
export * from './shopify_integration.js';
export * from './integration_manager.js';
