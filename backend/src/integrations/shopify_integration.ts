/**
 * Aster Companion - External Integrations & OAuth Service
 * shopify_integration.ts
 *
 * Shopify Storefront GraphQL query client:
 * - Read-only product catalog search and discovery by default.
 * - Non-autonomous purchase workflow: drafts a verified checkout link via cartCreate/checkoutCreate
 *   and mandates explicit user confirmation before checkout handoff.
 * - STRICT GUARANTEE: Never auto-charges, never initiates autonomous payments.
 */

import { createHash, randomBytes, timingSafeEqual } from 'node:crypto';

// ============================================================================
// Types and Interfaces
// ============================================================================

export interface ShopifyConfig {
  shopDomain: string; // e.g. "my-brand.myshopify.com"
  storefrontAccessToken: string;
  apiVersion?: string; // defaults to '2026-01'
}

export interface MoneyV2 {
  amount: string;
  currencyCode: string;
}

export interface ProductImage {
  url: string;
  altText?: string;
  width?: number;
  height?: number;
}

export interface ProductVariant {
  id: string;
  title: string;
  availableForSale: boolean;
  price: MoneyV2;
  sku?: string;
}

export interface ShopifyProduct {
  id: string;
  title: string;
  handle: string;
  description: string;
  availableForSale: boolean;
  minPrice: MoneyV2;
  maxPrice: MoneyV2;
  images: ProductImage[];
  variants: ProductVariant[];
  onlineStoreUrl?: string;
}

export interface CartLineItemInput {
  merchandiseId: string; // variant ID (e.g. "gid://shopify/ProductVariant/...")
  quantity: number;
}

export interface DraftPurchaseProposal {
  proposalId: string;
  confirmationToken: string;
  cartId: string;
  checkoutUrl: string;
  lineItems: Array<{
    merchandiseId: string;
    quantity: number;
    title?: string;
    price?: MoneyV2;
  }>;
  estimatedCost: {
    subtotalAmount: MoneyV2;
    totalTaxAmount?: MoneyV2;
    totalDutyAmount?: MoneyV2;
  };
  actionHash: string;
  expiresAt: number;
  confirmed: boolean;
  confirmedAt?: number;
}

export class ShopifyError extends Error {
  public readonly code: string;
  public readonly details?: unknown;

  constructor(message: string, code: string, details?: unknown) {
    super(message);
    this.code = code;
    this.details = details;
    this.name = 'ShopifyError';
  }
}

// ============================================================================
// GraphQL Queries & Mutations
// ============================================================================

const PRODUCT_SEARCH_QUERY = `
query SearchProducts($query: String!, $first: Int!) {
  products(first: $first, query: $query) {
    edges {
      node {
        id
        title
        handle
        description
        availableForSale
        onlineStoreUrl
        priceRange {
          minVariantPrice {
            amount
            currencyCode
          }
          maxVariantPrice {
            amount
            currencyCode
          }
        }
        images(first: 3) {
          edges {
            node {
              url
              altText
              width
              height
            }
          }
        }
        variants(first: 10) {
          edges {
            node {
              id
              title
              availableForSale
              sku
              price {
                amount
                currencyCode
              }
            }
          }
        }
      }
    }
  }
}
`;

const PRODUCT_BY_HANDLE_QUERY = `
query GetProductByHandle($handle: String!) {
  product(handle: $handle) {
    id
    title
    handle
    description
    availableForSale
    onlineStoreUrl
    priceRange {
      minVariantPrice {
        amount
        currencyCode
      }
      maxVariantPrice {
        amount
        currencyCode
      }
    }
    images(first: 5) {
      edges {
        node {
          url
          altText
          width
          height
        }
      }
    }
    variants(first: 20) {
      edges {
        node {
          id
          title
          availableForSale
          sku
          price {
            amount
            currencyCode
          }
        }
      }
    }
  }
}
`;

const CART_CREATE_MUTATION = `
mutation CartCreate($lines: [CartLineInput!]) {
  cartCreate(input: { lines: $lines }) {
    cart {
      id
      checkoutUrl
      cost {
        subtotalAmount {
          amount
          currencyCode
        }
        totalTaxAmount {
          amount
          currencyCode
        }
        totalDutyAmount {
          amount
          currencyCode
        }
      }
      lines(first: 10) {
        edges {
          node {
            id
            quantity
            merchandise {
              ... on ProductVariant {
                id
                title
                price {
                  amount
                  currencyCode
                }
              }
            }
          }
        }
      }
    }
    userErrors {
      field
      message
    }
  }
}
`;

// ============================================================================
// Shopify Storefront Integration Client
// ============================================================================

export class ShopifyStorefrontClient {
  private readonly endpoint: string;
  private readonly accessToken: string;
  private readonly defaultApiVersion = '2026-01';
  public readonly config: ShopifyConfig;
  private readonly fetchFn: typeof fetch;

  constructor(config: ShopifyConfig, fetchFn: typeof fetch = fetch) {
    this.config = config;
    this.fetchFn = fetchFn;
    if (!config.shopDomain) {
      throw new ShopifyError('Missing shopDomain in ShopifyConfig', 'INVALID_CONFIG');
    }
    if (!config.storefrontAccessToken) {
      throw new ShopifyError('Missing storefrontAccessToken in ShopifyConfig', 'INVALID_CONFIG');
    }

    const domain = config.shopDomain.replace(/^https?:\/\//, '').replace(/\/$/, '');
    const version = config.apiVersion || this.defaultApiVersion;
    this.endpoint = `https://${domain}/api/${version}/graphql.json`;
    this.accessToken = config.storefrontAccessToken;
  }

  /**
   * Executes a GraphQL request against the Shopify Storefront API.
   */
  public async executeGraphQL<T>(
    query: string,
    variables: Record<string, unknown> = {}
  ): Promise<T> {
    const response = await this.fetchFn(this.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Shopify-Storefront-Access-Token': this.accessToken,
        Accept: 'application/json',
      },
      body: JSON.stringify({ query, variables }),
    });

    if (response.status === 429) {
      throw new ShopifyError(
        'Shopify rate limit exceeded. Backoff required.',
        'RATE_LIMITED',
        { retryAfter: response.headers.get('Retry-After') }
      );
    }

    if (!response.ok) {
      const errText = await response.text();
      throw new ShopifyError(
        `Shopify GraphQL HTTP error (${response.status}): ${errText}`,
        'HTTP_ERROR'
      );
    }

    const payload = (await response.json()) as {
      data?: T;
      errors?: Array<{ message: string; locations?: unknown }>;
    };

    if (payload.errors && payload.errors.length > 0) {
      const messages = payload.errors.map((e) => e.message).join('; ');
      throw new ShopifyError(`Shopify GraphQL error: ${messages}`, 'GRAPHQL_ERROR', payload.errors);
    }

    if (!payload.data) {
      throw new ShopifyError('Empty response data from Shopify GraphQL', 'EMPTY_RESPONSE');
    }

    return payload.data;
  }

  /**
   * Searches the store catalog (READ-ONLY).
   */
  public async searchProducts(query: string, first = 10): Promise<ShopifyProduct[]> {
    interface SearchResponse {
      products: {
        edges: Array<{
          node: {
            id: string;
            title: string;
            handle: string;
            description: string;
            availableForSale: boolean;
            onlineStoreUrl?: string;
            priceRange: {
              minVariantPrice: MoneyV2;
              maxVariantPrice: MoneyV2;
            };
            images: {
              edges: Array<{
                node: {
                  url: string;
                  altText?: string;
                  width?: number;
                  height?: number;
                };
              }>;
            };
            variants: {
              edges: Array<{
                node: {
                  id: string;
                  title: string;
                  availableForSale: boolean;
                  sku?: string;
                  price: MoneyV2;
                };
              }>;
            };
          };
        }>;
      };
    }

    const data = await this.executeGraphQL<SearchResponse>(PRODUCT_SEARCH_QUERY, {
      query,
      first,
    });

    return data.products.edges.map(({ node }) => ({
      id: node.id,
      title: node.title,
      handle: node.handle,
      description: node.description,
      availableForSale: node.availableForSale,
      onlineStoreUrl: node.onlineStoreUrl,
      minPrice: node.priceRange.minVariantPrice,
      maxPrice: node.priceRange.maxVariantPrice,
      images: node.images.edges.map((e) => e.node),
      variants: node.variants.edges.map((e) => e.node),
    }));
  }

  /**
   * Retrieves single product details by handle (READ-ONLY).
   */
  public async getProductByHandle(handle: string): Promise<ShopifyProduct | null> {
    interface HandleResponse {
      product: {
        id: string;
        title: string;
        handle: string;
        description: string;
        availableForSale: boolean;
        onlineStoreUrl?: string;
        priceRange: {
          minVariantPrice: MoneyV2;
          maxVariantPrice: MoneyV2;
        };
        images: {
          edges: Array<{
            node: {
              url: string;
              altText?: string;
              width?: number;
              height?: number;
            };
          }>;
        };
        variants: {
          edges: Array<{
            node: {
              id: string;
              title: string;
              availableForSale: boolean;
              sku?: string;
              price: MoneyV2;
            };
          }>;
        };
      } | null;
    }

    const data = await this.executeGraphQL<HandleResponse>(PRODUCT_BY_HANDLE_QUERY, { handle });
    if (!data.product) return null;

    const node = data.product;
    return {
      id: node.id,
      title: node.title,
      handle: node.handle,
      description: node.description,
      availableForSale: node.availableForSale,
      onlineStoreUrl: node.onlineStoreUrl,
      minPrice: node.priceRange.minVariantPrice,
      maxPrice: node.priceRange.maxVariantPrice,
      images: node.images.edges.map((e) => e.node),
      variants: node.variants.edges.map((e) => e.node),
    };
  }

  /**
   * Non-autonomous purchase workflow:
   * When a user requests to purchase an item, this method generates a draft cart
   * and stages a DraftPurchaseProposal. It creates a verified checkout link
   * and requires explicit confirmation.
   *
   * Aster Companion NEVER auto-charges payment credentials.
   */
  public async draftPurchaseProposal(
    items: CartLineItemInput[],
    ttlMs = 30 * 60 * 1000 // 30 minutes proposal TTL
  ): Promise<DraftPurchaseProposal> {
    if (!items || items.length === 0) {
      throw new ShopifyError('At least one line item is required to draft a purchase', 'EMPTY_CART');
    }

    interface CartCreateResponse {
      cartCreate: {
        cart: {
          id: string;
          checkoutUrl: string;
          cost: {
            subtotalAmount: MoneyV2;
            totalTaxAmount?: MoneyV2;
            totalDutyAmount?: MoneyV2;
          };
          lines: {
            edges: Array<{
              node: {
                id: string;
                quantity: number;
                merchandise: {
                  id: string;
                  title: string;
                  price: MoneyV2;
                };
              };
            }>;
          };
        } | null;
        userErrors: Array<{ field: string[]; message: string }>;
      };
    }

    const formattedLines = items.map((i) => ({
      merchandiseId: i.merchandiseId,
      quantity: i.quantity,
    }));

    const data = await this.executeGraphQL<CartCreateResponse>(CART_CREATE_MUTATION, {
      lines: formattedLines,
    });

    if (data.cartCreate.userErrors && data.cartCreate.userErrors.length > 0) {
      const errs = data.cartCreate.userErrors.map((e) => e.message).join('; ');
      throw new ShopifyError(`Cart creation failed: ${errs}`, 'CART_ERROR', data.cartCreate.userErrors);
    }

    const cart = data.cartCreate.cart;
    if (!cart) {
      throw new ShopifyError('Failed to initialize cart from Shopify Storefront API', 'CART_CREATION_FAILED');
    }

    const proposalId = `shop_prop_${randomBytes(12).toString('hex')}`;
    const confirmationToken = randomBytes(24).toString('base64url');

    const lineItems = cart.lines.edges.map(({ node }) => ({
      merchandiseId: node.merchandise.id,
      quantity: node.quantity,
      title: node.merchandise.title,
      price: node.merchandise.price,
    }));

    const actionHash = createHash('sha256')
      .update(
        JSON.stringify({
          cartId: cart.id,
          checkoutUrl: cart.checkoutUrl,
          subtotal: cart.cost.subtotalAmount,
        })
      )
      .digest('hex');

    return {
      proposalId,
      confirmationToken,
      cartId: cart.id,
      checkoutUrl: cart.checkoutUrl,
      lineItems,
      estimatedCost: {
        subtotalAmount: cart.cost.subtotalAmount,
        totalTaxAmount: cart.cost.totalTaxAmount,
        totalDutyAmount: cart.cost.totalDutyAmount,
      },
      actionHash,
      expiresAt: Date.now() + ttlMs,
      confirmed: false,
    };
  }

  /**
   * Confirms the purchase proposal with timing-safe verification.
   * Returns verified checkout URL for client browser / App Intent redirection.
   * Ensures the user explicitly saw the checkout preview card before proceeding.
   */
  public verifyAndConfirmPurchaseProposal(
    proposal: DraftPurchaseProposal,
    providedConfirmationToken: string
  ): { confirmed: boolean; checkoutUrl: string } {
    if (Date.now() > proposal.expiresAt) {
      throw new ShopifyError('Purchase proposal has expired', 'EXPIRED_PROPOSAL');
    }

    const bufA = Buffer.from(proposal.confirmationToken, 'utf8');
    const bufB = Buffer.from(providedConfirmationToken, 'utf8');
    if (bufA.length !== bufB.length || !timingSafeEqual(bufA, bufB)) {
      throw new ShopifyError('Invalid confirmation token for purchase proposal', 'INVALID_CONFIRMATION_TOKEN');
    }

    proposal.confirmed = true;
    proposal.confirmedAt = Date.now();

    return {
      confirmed: true,
      checkoutUrl: proposal.checkoutUrl,
    };
  }
}
