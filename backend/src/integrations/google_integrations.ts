/**
 * Aster Companion - External Integrations & OAuth Service
 * google_integrations.ts
 *
 * Comprehensive Google Workspace & Services integration:
 * 1. Google Photos: Android Photo Picker contract / Google Photos Picker API;
 *    least-privilege scopes; strictly inspects user-selected photos only.
 * 2. Google Drive: Scoped querying using drive.file / drive.readonly.
 * 3. Gmail: CASA Tier 2 restricted scopes guidelines; drafting and search;
 *    requires explicit user approval before sending.
 * 4. Google Calendar: Queries events and creates draft events (with two-step confirmation).
 * 5. Google Contacts/People: Read-only contacts search for phone numbers and email lookups.
 */

import { createHash, randomBytes, timingSafeEqual } from 'node:crypto';

// ============================================================================
// Google OAuth Scopes (Least Privilege & CASA Classification)
// ============================================================================

export const GOOGLE_SCOPES = {
  // Photos: Minimal Picker scope (strictly user-selected items)
  PHOTOS_PICKER: 'https://www.googleapis.com/auth/photopicker.mediaitems.readonly',
  // Drive: Scoped access only
  DRIVE_FILE: 'https://www.googleapis.com/auth/drive.file',
  DRIVE_READONLY: 'https://www.googleapis.com/auth/drive.readonly',
  // Gmail: CASA Tier 2 restricted scopes
  GMAIL_READONLY: 'https://www.googleapis.com/auth/gmail.readonly',
  GMAIL_COMPOSE: 'https://www.googleapis.com/auth/gmail.compose',
  // Calendar: Readonly and event creation
  CALENDAR_READONLY: 'https://www.googleapis.com/auth/calendar.events.readonly',
  CALENDAR_EVENTS: 'https://www.googleapis.com/auth/calendar.events',
  // Contacts: Readonly contact directory search
  CONTACTS_READONLY: 'https://www.googleapis.com/auth/contacts.readonly',
} as const;

// Scopes classified as Restricted under Google CASA (Cloud Application Security Assessment Tier 2)
export const CASA_RESTRICTED_SCOPES = [
  GOOGLE_SCOPES.GMAIL_READONLY,
  GOOGLE_SCOPES.GMAIL_COMPOSE,
  GOOGLE_SCOPES.DRIVE_READONLY,
];

// ============================================================================
// Common Types & Approval Models
// ============================================================================

export interface ActionApprovalTicket {
  ticketId: string;
  profileId: string;
  actionType: 'GMAIL_SEND' | 'CALENDAR_EVENT_COMMIT' | 'FILE_DELETE';
  actionHash: string; // SHA-256 of the proposed payload
  confirmationToken: string;
  approved: boolean;
  approvedAt?: number;
  expiresAt: number;
  summary: string;
  payload: Record<string, unknown>;
}

export class ApprovalRequiredError extends Error {
  public readonly actionType: string;
  public readonly ticketId: string;

  constructor(actionType: string, ticketId: string) {
    super(
      `Action '${actionType}' requires explicit user confirmation. Approval ticket: ${ticketId}`
    );
    this.actionType = actionType;
    this.ticketId = ticketId;
    this.name = 'ApprovalRequiredError';
  }
}

export class ScopeRequiredError extends Error {
  public readonly requiredScope: string;
  public readonly grantedScopes: string[];

  constructor(requiredScope: string, grantedScopes: string[]) {
    super(
      `Required OAuth scope '${requiredScope}' has not been granted. Granted: ${grantedScopes.join(', ')}`
    );
    this.requiredScope = requiredScope;
    this.grantedScopes = grantedScopes;
    this.name = 'ScopeRequiredError';
  }
}

// ============================================================================
// 1. Google Photos Integration (Photo Picker Contract)
// ============================================================================

export interface SelectedPhotoItem {
  id: string;
  filename: string;
  mimeType: string;
  baseUrl: string;
  createTime?: string;
  width?: number;
  height?: number;
  cameraMake?: string;
  cameraModel?: string;
}

export interface PhotoPickerSession {
  sessionId: string;
  pickerUri: string;
  expireTime: string;
  mediaItemsSet: boolean;
  selectedItems: SelectedPhotoItem[];
}

export class GooglePhotosService {
  private readonly baseUrl = 'https://photospicker.googleapis.com/v1';
  private readonly fetchFn: typeof fetch;

  constructor(fetchFn: typeof fetch = fetch) {
    this.fetchFn = fetchFn;
  }

  /**
   * Creates a new secure Photo Picker session using the Google Photos Picker API.
   * This guarantees zero access to the user's unselected library.
   */
  public async createPickerSession(accessToken: string): Promise<PhotoPickerSession> {
    const response = await this.fetchFn(`${this.baseUrl}/sessions`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({}),
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Failed to create Google Photos picker session (${response.status}): ${err}`);
    }

    const data = (await response.json()) as {
      id: string;
      pickerUri: string;
      expireTime: string;
      mediaItemsSet?: boolean;
    };

    return {
      sessionId: data.id,
      pickerUri: data.pickerUri,
      expireTime: data.expireTime,
      mediaItemsSet: Boolean(data.mediaItemsSet),
      selectedItems: [],
    };
  }

  /**
   * Retrieves strictly the user-selected photos from an active picker session.
   * Respects least-privilege boundary: returns only items explicitly confirmed by user.
   */
  public async getSessionMediaItems(
    accessToken: string,
    sessionId: string,
    pageSize = 20
  ): Promise<SelectedPhotoItem[]> {
    const url = new URL(`${this.baseUrl}/mediaItems`);
    url.searchParams.set('sessionId', sessionId);
    url.searchParams.set('pageSize', String(pageSize));

    const response = await this.fetchFn(url.toString(), {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        Accept: 'application/json',
      },
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Failed to query picker session media items (${response.status}): ${err}`);
    }

    const data = (await response.json()) as {
      mediaItems?: Array<{
        id: string;
        filename?: string;
        mimeType?: string;
        baseUrl?: string;
        createTime?: string;
        mediaFile?: {
          width?: number;
          height?: number;
          cameraMake?: string;
          cameraModel?: string;
        };
      }>;
    };

    if (!data.mediaItems) {
      return [];
    }

    return data.mediaItems.map((item) => ({
      id: item.id,
      filename: item.filename || 'unknown.jpg',
      mimeType: item.mimeType || 'image/jpeg',
      baseUrl: item.baseUrl || '',
      createTime: item.createTime,
      width: item.mediaFile?.width,
      height: item.mediaFile?.height,
      cameraMake: item.mediaFile?.cameraMake,
      cameraModel: item.mediaFile?.cameraModel,
    }));
  }

  /**
   * Android Photo Picker Contract parser:
   * Handles local SAF / Android 13+ Photo Picker intent URIs passed from the Android client.
   * Ensures Aster only inspects URIs delivered via ActivityResultContracts.PickVisualMedia.
   */
  public parseAndroidPickerResult(
    selectedUris: Array<{ uri: string; displayName?: string; mimeType?: string; sizeBytes?: number }>
  ): SelectedPhotoItem[] {
    return selectedUris.map((u, index) => {
      // Must be a valid content URI from system photo picker
      if (!u.uri.startsWith('content://')) {
        throw new Error(`Invalid Photo Picker URI: ${u.uri}. Must be a secure content:// URI`);
      }
      return {
        id: `android_picker_${index}_${createHash('sha256').update(u.uri).digest('hex').substring(0, 16)}`,
        filename: u.displayName || `picked_photo_${index}.jpg`,
        mimeType: u.mimeType || 'image/jpeg',
        baseUrl: u.uri,
      };
    });
  }
}

// ============================================================================
// 2. Google Drive Integration (drive.file / drive.readonly)
// ============================================================================

export interface DriveFileMetadata {
  id: string;
  name: string;
  mimeType: string;
  size?: number;
  modifiedTime?: string;
  webViewLink?: string;
  thumbnailLink?: string;
}

export interface DriveSearchOptions {
  nameContains?: string;
  mimeType?: string;
  trashed?: boolean;
  pageSize?: number;
  orderBy?: string;
}

export class GoogleDriveService {
  private readonly baseUrl = 'https://www.googleapis.com/drive/v3';
  private readonly maxDownloadBytes = 15 * 1024 * 1024; // 15MB size guard
  private readonly fetchFn: typeof fetch;

  constructor(fetchFn: typeof fetch = fetch) {
    this.fetchFn = fetchFn;
  }

  /**
   * Queries Google Drive files with structured query sanitization.
   */
  public async searchFiles(
    accessToken: string,
    options: DriveSearchOptions = {}
  ): Promise<DriveFileMetadata[]> {
    const queryParts: string[] = [];

    // Ensure we never query trashed files unless requested
    queryParts.push(`trashed = ${options.trashed ? 'true' : 'false'}`);

    if (options.nameContains) {
      // Escape single quotes to prevent Drive query injection
      const sanitizedName = options.nameContains.replace(/'/g, "\\'");
      queryParts.push(`name contains '${sanitizedName}'`);
    }

    if (options.mimeType) {
      queryParts.push(`mimeType = '${options.mimeType}'`);
    }

    const q = queryParts.join(' and ');
    const url = new URL(`${this.baseUrl}/files`);
    url.searchParams.set('q', q);
    url.searchParams.set('pageSize', String(options.pageSize || 20));
    url.searchParams.set(
      'fields',
      'files(id, name, mimeType, size, modifiedTime, webViewLink, thumbnailLink)'
    );
    if (options.orderBy) {
      url.searchParams.set('orderBy', options.orderBy);
    }

    const response = await this.fetchFn(url.toString(), {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        Accept: 'application/json',
      },
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Google Drive API search failed (${response.status}): ${err}`);
    }

    const data = (await response.json()) as { files?: DriveFileMetadata[] };
    return data.files || [];
  }

  /**
   * Retrieves file metadata and content with memory-safe size guards.
   */
  public async getFileContent(
    accessToken: string,
    fileId: string
  ): Promise<{ metadata: DriveFileMetadata; content: Buffer }> {
    // 1. Fetch metadata first to enforce size guard
    const metaUrl = `${this.baseUrl}/files/${encodeURIComponent(fileId)}?fields=id,name,mimeType,size,modifiedTime`;
    const metaResponse = await this.fetchFn(metaUrl, {
      method: 'GET',
      headers: { Authorization: `Bearer ${accessToken}` },
    });

    if (!metaResponse.ok) {
      const err = await metaResponse.text();
      throw new Error(`Failed to fetch Drive file metadata (${metaResponse.status}): ${err}`);
    }

    const metadata = (await metaResponse.json()) as DriveFileMetadata;

    if (metadata.size && metadata.size > this.maxDownloadBytes) {
      throw new Error(
        `File size (${metadata.size} bytes) exceeds maximum safe download guard (${this.maxDownloadBytes} bytes)`
      );
    }

    // 2. Fetch binary content
    const downloadUrl = `${this.baseUrl}/files/${encodeURIComponent(fileId)}?alt=media`;
    const downloadResponse = await this.fetchFn(downloadUrl, {
      method: 'GET',
      headers: { Authorization: `Bearer ${accessToken}` },
    });

    if (!downloadResponse.ok) {
      const err = await downloadResponse.text();
      throw new Error(`Failed to download Drive file content (${downloadResponse.status}): ${err}`);
    }

    const arrayBuffer = await downloadResponse.arrayBuffer();
    return {
      metadata,
      content: Buffer.from(arrayBuffer),
    };
  }
}

// ============================================================================
// 3. Gmail Integration (Drafting, Search & Safety Approval Gate)
// ============================================================================

export interface GmailMessageSummary {
  id: string;
  threadId: string;
  snippet: string;
  subject: string;
  from: string;
  to: string;
  date: string;
}

export interface EmailDraftPayload {
  to: string;
  subject: string;
  bodyText: string;
  cc?: string;
  bcc?: string;
}

export interface CreatedDraftResult {
  draftId: string;
  messageId: string;
  to: string;
  subject: string;
  bodySnippet: string;
}

export class GmailService {
  private readonly baseUrl = 'https://gmail.googleapis.com/gmail/v1/users/me';
  private readonly fetchFn: typeof fetch;

  constructor(fetchFn: typeof fetch = fetch) {
    this.fetchFn = fetchFn;
  }

  /**
   * Search messages using Gmail standard search query syntax.
   */
  public async searchMessages(
    accessToken: string,
    query: string,
    maxResults = 10
  ): Promise<GmailMessageSummary[]> {
    const listUrl = new URL(`${this.baseUrl}/messages`);
    listUrl.searchParams.set('q', query);
    listUrl.searchParams.set('maxResults', String(maxResults));

    const listRes = await this.fetchFn(listUrl.toString(), {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        Accept: 'application/json',
      },
    });

    if (!listRes.ok) {
      const err = await listRes.text();
      throw new Error(`Gmail search failed (${listRes.status}): ${err}`);
    }

    const listData = (await listRes.json()) as { messages?: Array<{ id: string; threadId: string }> };
    if (!listData.messages || listData.messages.length === 0) {
      return [];
    }

    // Fetch individual headers for the matched messages
    const summaries: GmailMessageSummary[] = [];
    for (const msg of listData.messages.slice(0, maxResults)) {
      const detailUrl = `${this.baseUrl}/messages/${msg.id}?format=metadata&metadataHeaders=Subject&metadataHeaders=From&metadataHeaders=To&metadataHeaders=Date`;
      const detailRes = await this.fetchFn(detailUrl, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });

      if (detailRes.ok) {
        const detail = (await detailRes.json()) as {
          id: string;
          threadId: string;
          snippet?: string;
          payload?: {
            headers?: Array<{ name: string; value: string }>;
          };
        };

        const headers = detail.payload?.headers || [];
        const findHeader = (name: string) =>
          headers.find((h) => h.name.toLowerCase() === name.toLowerCase())?.value || '';

        summaries.push({
          id: detail.id,
          threadId: detail.threadId,
          snippet: detail.snippet || '',
          subject: findHeader('Subject'),
          from: findHeader('From'),
          to: findHeader('To'),
          date: findHeader('Date'),
        });
      }
    }

    return summaries;
  }

  /**
   * Helper to format an RFC 2822 email message encoded in base64url.
   */
  public encodeRfc2822(draft: EmailDraftPayload): string {
    const lines = [
      `To: ${draft.to}`,
      `Subject: ${draft.subject}`,
      'MIME-Version: 1.0',
      'Content-Type: text/plain; charset=UTF-8',
    ];
    if (draft.cc) lines.push(`Cc: ${draft.cc}`);
    if (draft.bcc) lines.push(`Bcc: ${draft.bcc}`);
    lines.push('', draft.bodyText);

    const raw = lines.join('\r\n');
    return Buffer.from(raw, 'utf8')
      .toString('base64')
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=+$/, '');
  }

  /**
   * Creates a draft email in Gmail.
   * Safe action: Storing a draft does not transmit external communication.
   */
  public async createEmailDraft(
    accessToken: string,
    draft: EmailDraftPayload
  ): Promise<CreatedDraftResult> {
    const rawEncoded = this.encodeRfc2822(draft);

    const response = await this.fetchFn(`${this.baseUrl}/drafts`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: { raw: rawEncoded },
      }),
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Failed to create Gmail draft (${response.status}): ${err}`);
    }

    const data = (await response.json()) as {
      id: string;
      message: { id: string };
    };

    return {
      draftId: data.id,
      messageId: data.message.id,
      to: draft.to,
      subject: draft.subject,
      bodySnippet: draft.bodyText.substring(0, 100),
    };
  }

  /**
   * Sends an email via Gmail API with MANDATORY Action Approval Ticket validation.
   * Respects CASA Tier 2 guidelines and Aster Companion Human-in-the-Loop requirement:
   * Will throw ApprovalRequiredError if an unconfirmed ticket is presented.
   */
  public async sendEmailWithApproval(
    accessToken: string,
    ticket: ActionApprovalTicket,
    draft: EmailDraftPayload
  ): Promise<{ messageId: string; threadId: string }> {
    // 1. Verify approval ticket validity
    if (!ticket.approved) {
      throw new ApprovalRequiredError('GMAIL_SEND', ticket.ticketId);
    }
    if (Date.now() > ticket.expiresAt) {
      throw new Error(`Action approval ticket ${ticket.ticketId} has expired.`);
    }

    // 2. Cryptographic payload integrity verification
    const computedHash = createHash('sha256')
      .update(JSON.stringify({ to: draft.to, subject: draft.subject, bodyText: draft.bodyText }))
      .digest('hex');

    if (computedHash !== ticket.actionHash) {
      throw new Error('Action payload hash does not match approved ticket hash. Aborting send.');
    }

    // 3. Send email
    const rawEncoded = this.encodeRfc2822(draft);
    const response = await this.fetchFn(`${this.baseUrl}/messages/send`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ raw: rawEncoded }),
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Failed to send email via Gmail API (${response.status}): ${err}`);
    }

    const data = (await response.json()) as { id: string; threadId: string };
    return {
      messageId: data.id,
      threadId: data.threadId,
    };
  }
}

// ============================================================================
// 4. Google Calendar Integration (Two-Step Confirmation)
// ============================================================================

export interface CalendarEventSummary {
  id: string;
  summary: string;
  description?: string;
  location?: string;
  start: { dateTime?: string; date?: string; timeZone?: string };
  end: { dateTime?: string; date?: string; timeZone?: string };
  htmlLink?: string;
}

export interface CalendarEventPayload {
  summary: string;
  description?: string;
  location?: string;
  start: { dateTime: string; timeZone?: string };
  end: { dateTime: string; timeZone?: string };
  attendees?: Array<{ email: string; displayName?: string }>;
}

export interface DraftCalendarProposal {
  proposalId: string;
  confirmationToken: string;
  event: CalendarEventPayload;
  actionHash: string;
  expiresAt: number;
}

export class GoogleCalendarService {
  private readonly baseUrl = 'https://www.googleapis.com/calendar/v3';
  private readonly fetchFn: typeof fetch;

  constructor(fetchFn: typeof fetch = fetch) {
    this.fetchFn = fetchFn;
  }

  /**
   * Queries calendar events within a specified time range.
   */
  public async listEvents(
    accessToken: string,
    calendarId = 'primary',
    timeMin?: string,
    timeMax?: string,
    maxResults = 20
  ): Promise<CalendarEventSummary[]> {
    const url = new URL(`${this.baseUrl}/calendars/${encodeURIComponent(calendarId)}/events`);
    url.searchParams.set('maxResults', String(maxResults));
    url.searchParams.set('singleEvents', 'true');
    url.searchParams.set('orderBy', 'startTime');

    if (timeMin) url.searchParams.set('timeMin', timeMin);
    if (timeMax) url.searchParams.set('timeMax', timeMax);

    const response = await this.fetchFn(url.toString(), {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        Accept: 'application/json',
      },
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Google Calendar API list events failed (${response.status}): ${err}`);
    }

    const data = (await response.json()) as { items?: CalendarEventSummary[] };
    return data.items || [];
  }

  /**
   * Step 1: Creates a draft event proposal for user review and approval.
   * Generates a cryptographic single-use confirmation token.
   */
  public createDraftEventProposal(
    event: CalendarEventPayload,
    ttlMs = 15 * 60 * 1000
  ): DraftCalendarProposal {
    const proposalId = `cal_prop_${randomBytes(12).toString('hex')}`;
    const confirmationToken = randomBytes(24).toString('base64url');
    const actionHash = createHash('sha256')
      .update(JSON.stringify(event))
      .digest('hex');

    return {
      proposalId,
      confirmationToken,
      event,
      actionHash,
      expiresAt: Date.now() + ttlMs,
    };
  }

  /**
   * Step 2: Commits the draft event to the user's Google Calendar after user confirmation.
   */
  public async commitConfirmedEvent(
    accessToken: string,
    proposal: DraftCalendarProposal,
    providedConfirmationToken: string,
    calendarId = 'primary'
  ): Promise<CalendarEventSummary> {
    if (Date.now() > proposal.expiresAt) {
      throw new Error(`Calendar event proposal ${proposal.proposalId} has expired.`);
    }

    const bufA = Buffer.from(proposal.confirmationToken, 'utf8');
    const bufB = Buffer.from(providedConfirmationToken, 'utf8');
    if (bufA.length !== bufB.length || !timingSafeEqual(bufA, bufB)) {
      throw new Error('Invalid confirmation token for calendar event commit.');
    }

    const url = `${this.baseUrl}/calendars/${encodeURIComponent(calendarId)}/events`;
    const response = await this.fetchFn(url, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(proposal.event),
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Failed to commit Google Calendar event (${response.status}): ${err}`);
    }

    return (await response.json()) as CalendarEventSummary;
  }
}

// ============================================================================
// 5. Google Contacts / People Integration (Read-Only Search)
// ============================================================================

export interface ContactLookupResult {
  resourceName: string;
  etag: string;
  displayName: string;
  emailAddresses: string[];
  phoneNumbers: string[];
  photoUrl?: string;
}

export class GoogleContactsService {
  private readonly baseUrl = 'https://people.googleapis.com/v1';
  private readonly fetchFn: typeof fetch;

  constructor(fetchFn: typeof fetch = fetch) {
    this.fetchFn = fetchFn;
  }

  /**
   * Read-only contacts search for phone numbers and email lookups.
   */
  public async searchContacts(
    accessToken: string,
    query: string,
    pageSize = 10
  ): Promise<ContactLookupResult[]> {
    const url = new URL(`${this.baseUrl}/people:searchContacts`);
    url.searchParams.set('query', query);
    url.searchParams.set('pageSize', String(pageSize));
    url.searchParams.set('readMask', 'names,emailAddresses,phoneNumbers,photos');

    const response = await this.fetchFn(url.toString(), {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        Accept: 'application/json',
      },
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Google People API contacts search failed (${response.status}): ${err}`);
    }

    const data = (await response.json()) as {
      results?: Array<{
        person?: {
          resourceName?: string;
          etag?: string;
          names?: Array<{ displayName?: string }>;
          emailAddresses?: Array<{ value?: string }>;
          phoneNumbers?: Array<{ value?: string }>;
          photos?: Array<{ url?: string }>;
        };
      }>;
    };

    if (!data.results) return [];

    return data.results.map((r) => {
      const p = r.person || {};
      const displayName = p.names?.[0]?.displayName || 'Unnamed Contact';
      const emailAddresses = (p.emailAddresses || []).map((e) => e.value || '').filter(Boolean);
      const phoneNumbers = (p.phoneNumbers || []).map((pn) => pn.value || '').filter(Boolean);
      const photoUrl = p.photos?.[0]?.url;

      return {
        resourceName: p.resourceName || '',
        etag: p.etag || '',
        displayName,
        emailAddresses,
        phoneNumbers,
        photoUrl,
      };
    });
  }

  /**
   * Lists connections from user contacts directory (read-only).
   */
  public async listContacts(
    accessToken: string,
    pageSize = 50
  ): Promise<ContactLookupResult[]> {
    const url = new URL(`${this.baseUrl}/people/me/connections`);
    url.searchParams.set('pageSize', String(pageSize));
    url.searchParams.set('personFields', 'names,emailAddresses,phoneNumbers,photos');

    const response = await this.fetchFn(url.toString(), {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        Accept: 'application/json',
      },
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Google People API list contacts failed (${response.status}): ${err}`);
    }

    const data = (await response.json()) as {
      connections?: Array<{
        resourceName?: string;
        etag?: string;
        names?: Array<{ displayName?: string }>;
        emailAddresses?: Array<{ value?: string }>;
        phoneNumbers?: Array<{ value?: string }>;
        photos?: Array<{ url?: string }>;
      }>;
    };

    if (!data.connections) return [];

    return data.connections.map((p) => ({
      resourceName: p.resourceName || '',
      etag: p.etag || '',
      displayName: p.names?.[0]?.displayName || 'Unnamed Contact',
      emailAddresses: (p.emailAddresses || []).map((e) => e.value || '').filter(Boolean),
      phoneNumbers: (p.phoneNumbers || []).map((pn) => pn.value || '').filter(Boolean),
      photoUrl: p.photos?.[0]?.url,
    }));
  }
}
