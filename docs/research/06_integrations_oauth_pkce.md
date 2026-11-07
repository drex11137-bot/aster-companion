# Aster Companion Research Dossier: External Integrations, OAuth 2.0 PKCE & Action Approvals

**Domain Key**: `06_integrations_oauth_pkce`  
**Generated**: November 2026  
**Total Queries Executed**: 20  

## Executive Findings & Architectural Directives

This document compiles verified engineering research for External Integrations, OAuth 2.0 PKCE & Action Approvals in the Aster Companion ecosystem. These findings directly inform our Supabase backend, Android Compose client, iOS SwiftUI app, laptop web client, and multimodal AI pipelines.

---

## Query Inventory & Verified Evidence

### Q1: OAuth 2.0 Authorization Code Flow with PKCE RFC 7636 mobile security best practice

- **[RFC 7636: Proof Key for Code Exchange by OAuth Public Clients | RFC Editor](https://www.rfc-editor.org/info/rfc7636/)** (Exa)
- **[RFC 9700: Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/rfc/rfc9700.pdf)** (Exa)
- **[OAuth2 - OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/cheatsheets/OAuth2_Cheat_Sheet.html)** (Exa)
- **[RFC 7636 - Proof Key for Code Exchange by OAuth Public ...](https://datatracker.ietf.org/doc/html/rfc7636)** (Exa)

### Q2: Android Custom Tabs vs AppAuth Android OAuth PKCE redirect URI deep linking

- **[GitHub - openid/AppAuth-Android: Android client SDK for communicating with OAuth 2.0 and OpenID Connect providers. · GitHub](https://github.com/openid/appauth-android)** (Tavily)
  > "The library also supports the PKCE extension to OAuth which was created to secure authorization codes in public clients when custom URI scheme redirects are used. The library is friendly to other extensions (standard or otherwise) with the ability to handle additional parameters in all protocol requ"
- **[Build an Android app using OAuth 2.0 and PKCE | SecureAuth Connect Product Docs](https://docs.secureauth.com/iam/build-an-android-app-using-oauth-2-0-and-pkce)** (Tavily)
  > "In `LoginActivity` we need to set a click listener on the button. When the user taps `Login` the click listener will make use of CustomTabs which will open a secure browser and direct the user to SecureAuth authorization server to request authorization for this mobile app to access the users protect"
- **[Authorization - OAuth 2.0 Simplified](https://www.oauth.com/oauth2-servers/mobile-and-native-apps/authorization)** (Tavily)
  > "OAuth 2.0 Servers  # Authorization   6.1  Create a “Log in” button that will open a secure web browser within the app (`ASWebAuthenticationSession` or `SFSafariViewController` on iOS, and “Custom Tabs” on Android). You’ll use the same parameters for the authorization request as described in Server-S"

### Q3: iOS ASWebAuthenticationSession OAuth 2.0 PKCE secure token exchange

- **[README.md](https://github.com/openid/AppAuth-iOS/blob/master/README.md)** (Exa)
- **[Authorization - OAuth 2.0 Simplified](https://www.oauth.com/oauth2-servers/mobile-and-native-apps/authorization/)** (Exa)
- **[OAuth 2.0 for Native Apps — RFC 8252](https://oauth.net/2/native-apps/)** (Exa)
- **[Build an iOS app using OAuth 2.0 and PKCE | SecureAuth Connect Product Docs](https://docs.secureauth.com/iam/build-an-ios-app-using-oauth-2-0-and-pkce)** (Exa)

### Q4: Google Photos Picker API zero-permission Android Photo Picker vs Google Photos API

- **[Get started with the Picker API  |  Google Photos APIs  |  Google for Developers](https://developers.google.com/photos/picker/guides/get-started-picker)** (Tavily)
  > "The Picker API flow involves creating a session, directing users to the Google Photos app for selection, polling the session for completion, and then retrieving the selected media items.  Developers should check the provided resources like reference documentation and samples for detailed information"
- **[Updates to the Google Photos APIs: Picker API launch and Library API changes - Google Developers Blog](https://developers.googleblog.com/en/google-photos-picker-api-launch-and-library-api-updates)** (Tavily)
  > "## What's Changing   Secure photo selection with the new Google Photos Picker API: The Picker API offers a secure and intuitive way for users to search for and select photos and albums through a seamless integration with the Google Photos app. [...] Familiarize yourself with the new policies: Review"
- **[Shared album photos not showing in Google Photos Picker API - Google Photos Community](https://support.google.com/photos/thread/471949582/shared-album-photos-not-showing-in-google-photos-picker-api?hl=en)** (Tavily)
  > "The limitation you are experiencing with the Google Photos Picker API occurs because the API is intentionally designed around privacy and security boundaries. It only exposes media items owned directly by the authenticated user's personal library. Content contributed by other family members into a S"

### Q5: Google Drive API v3 least privilege scopes drive.file drive.readonly authorization

- **[Choose Google Drive API scopes  |  Google for Developers](https://developers.google.com/workspace/drive/api/guides/api-specific-auth)** (Exa)
- **[Requesting Minimum Scopes - Google Cloud Platform Console Help](https://support.google.com/cloud/answer/13807380?hl=en)** (Exa)
- **[Method: files.get 

    
    
       
    

     
      
      Stay organized with collections
     
     
      
      Save and categorize content based on your preferences.](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/get)** (Exa)
- **[OAuth 2.0 Scopes for Google APIs](https://developers.google.com/identity/protocols/oauth2/scopes)** (Exa)

### Q6: Google Gmail API restricted scopes CASA Cloud Application Security Assessment Tier 2

- **[Google OAuth App Security: How We Passed CASA Tier 2 on the First Try](https://buzzclan.com/cyber-security/google-casa-tier-2-assessment)** (Tavily)
  > "CASA Tier 2 is a security evaluation mandated by Google for applications that access restricted OAuth scopes, including sensitive Google Workspace data such as Gmail, Drive, or Calendar content. It requires a Dynamic Application Security Testing scan conducted by an authorized third-party lab. Any a"
- **[Is CASA Tier 2 assessment necessary for all Gmail API apps - options for indie developers? - Gmail - Latenode Official Community](https://community.latenode.com/t/is-casa-tier-2-assessment-necessary-for-all-gmail-api-apps-options-for-indie-developers/22861)** (Tavily)
  > "Same thing happened to me last year with my productivity app. Google requires CASA Tier 2 for most Gmail API apps using sensitive scopes, and there’s basically no way around it for indie devs. Once you hit certain user numbers or use specific scopes, you’re stuck with the assessment. I ended up pivo"
- **[Google CASA - Cloud Application Security Assessment 2026](https://deepstrike.io/blog/google-casa-security-assessment-2025)** (Tavily)
  > "CASA is Google’s new security audit framework for cloud apps that handle sensitive Google user data. It’s built on the OWASP ASVS standard and uses risk based, multi tier testing Tier 1- 3 to ensure apps follow strong security controls.  Apps accessing restricted scopes e.g. Gmail or Drive APIs must"

### Q7: Google Calendar API v3 event creation and query authorized companion agent

- **[Create events  |  Google Calendar  |  Google for Developers](https://developers.google.com/workspace/calendar/api/guides/create-events)** (Exa)
- **[Events: list 

    
    
       
    

     
      
      Stay organized with collections
     
     
      
      Save and categorize content based on your preferences.](https://developers.google.com/workspace/calendar/api/v3/reference/events/list)** (Exa)
- **[Events  |  Google Calendar  |  Google for Developers](https://developers.google.com/workspace/calendar/api/v3/reference/events)** (Exa)
- **[Calendar API . events](https://developers.google.com/resources/api-libraries/documentation/calendar/v3/python/latest/calendar_v3.events.html)** (Exa)

### Q8: Google People API contacts read only authorization flow user consent

- **[Embracing Incremental Authorization with Google Contacts API - CloudSponge](https://www.cloudsponge.com/blog/embracing-incremental-authorization-with-google-contacts-api)** (Tavily)
  > "Except that is not how things work anymore, apparently. Google has decided that it is best to make people read the consent form and deliberately include every permission that they want your app to have.  Google OAuth window with empty checkboxes  Most people don’t realize they need to tick the check"
- **[Google Contacts MCP vs People API: Decision Framework](https://www.scalekit.com/blog/google-contacts-mcp-vs-api)** (Tavily)
  > "Use the People API MCP server when:   Your agent only needs to resolve or look people up: name to email, directory search, current-user profile, inside an interactive assistant where OAuth consent is natural.  You are prototyping a read-only contact feature and want a hosted endpoint without writing"
- **[Google Contacts API Integration Guide for Developers](https://api2cart.com/news/google-contacts-api)** (Tavily)
  > "Use this order:  1. Create a Google Cloud project 2. Enable the People API 3. Configure the OAuth consent screen 4. Create OAuth client credentials 5. Request only the scopes your workflow needs 6. Implement code exchange and refresh token storage  If your team needs a broader OAuth implementation c"

### Q9: Shopify Storefront API GraphQL product search catalog query AI shopping assistant

- **[GraphQL Storefront API](https://shopify.dev/docs/api/storefront/latest)** (Exa)
- **[Search and discovery](https://shopify.dev/docs/storefronts/headless/building-with-the-storefront-api/search-discovery)** (Exa)
- **[](https://shopify.dev/docs/apps/build/storefront-mcp/servers/storefront)** (Exa)
- **[Web​MCP tools](https://shopify.dev/docs/api/web-mcp)** (Exa)

### Q10: Secure server-side refresh token encryption AES-256-GCM automatic token rotation

- **[Refresh Token Security: Best Practices for OAuth Token Protection](https://www.obsidiansecurity.com/blog/refresh-token-security-best-practices)** (Tavily)
  > "Automatic token rotation on every refresh operation  Atomic database operations preventing race conditions  Reuse detection logic that invalidates token families on duplicate use  Monitoring and alerting when reuse attempts occur  Test rotation implementation thoroughly. Race conditions and database"
- **[What Is Token Rotation? | Token Security](https://www.token.security/glossary/token-rotation)** (Tavily)
  > "Token rotation is a security practice that issues a new refresh credential each time a client exchanges a refresh token for an access token, while immediately invalidating the predecessor token. This prevents stolen or duplicated refresh tokens from being reused repeatedly. Many implementations pair"
- **[Refresh Token Rotation Explained for Modern Authentication](https://www.loginradius.com/blog/identity/secure-refresh-token-rotation)** (Tavily)
  > "Secure storage helps, but it doesn’t eliminate risk. Devices get backed up. Debug builds leak data. Network conditions trigger retries and race conditions. Rotation works well here as long as concurrency is handled carefully and refresh logic is centralized so the app doesn’t accidentally invalidate"

### Q11: Granular OAuth scope disconnection and token revocation endpoint Google RFC 7009

- **[How to handle granular permissions  |  Authorization Resources  |  Google for Developers](https://developers.google.com/identity/protocols/oauth2/resources/granular-permissions)** (Exa)
- **[Google OpenID Connect API Reference  |  Authentication  |  Google for Developers](https://developers.google.com/identity/openid-connect/reference)** (Exa)
- **[RFC 7009 - OAuth 2.0 Token Revocation](https://datatracker.ietf.org/doc/rfc7009/)** (Exa)
- **[Using OAuth 2.0 for Web Server Applications  |  Authorization  |  Google for Developers](https://developers.google.com/identity/protocols/oauth2/web-server)** (Exa)

### Q12: Typed tool schemas JSON schema validation for LLM function calling arguments

- **[Tool Call Validation: JSON Schema Validation for Tool Outputs - Just Understanding Data](https://understandingdata.com/posts/tool-call-validation)** (Tavily)
  > "Tool call validation enforces type safety at the boundary between LLM outputs and deterministic code. When an agent returns a tool call, the response is a JSON object with a tool name and parameters. This JSON must be validated before execution because LLMs can return malformed JSON, missing fields,"
- **[LLM Structured Outputs with JSON Schema | TrueFoundry](https://www.truefoundry.com/blog/llm-structured-outputs-json-schema)** (Tavily)
  > "Validation belongs after generation too. Shape is not truth: a schema-valid customer ID, amount, date, or resource can still violate domain rules.  Tool calling is structured output with consequence. A typed tool name and argument object describe an intended action; runtime authorization and policy"
- **[The guide to structured outputs and function calling with LLMs — Agenta Blog](https://agenta.ai/blog/the-guide-to-structured-outputs-and-function-calling-with-llms)** (Tavily)
  > "Claude models from Anthropic don’t support structured output the way OpenAI does with `response_format`. But you can get the same effect by using tool-based structured output with schema validation. In practice, this means you define a schema that describes the fields and types you expect, using som"

### Q13: Risk classification for AI agent actions read only vs reversible vs destructive

- **[Know Your Risks: Agentic AI Risk Classifications - University IT](https://uit.stanford.edu/security/agenticai/riskclassifications)** (Exa)
- **[Read Is Not Act | Agents Without the Hype | AI Learning Hub | Stanford Law School](https://ailearninghub.law.stanford.edu/agents-without-the-hype/read-is-not-act/)** (Exa)
- **[AI Agent Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html)** (Exa)
- **[NIST AI Risk Management Framework: Agentic Profile](https://labs.cloudsecurityalliance.org/agentic/agentic-nist-ai-rmf-profile-v1/)** (Exa)

### Q14: Two-step human in the loop action confirmation UI card before external mutation

- **[The Verifiable Action Card: Trustworthy Human-in-the-Loop Control for Secure Autonomous Agents](https://arxiv.org/html/2609.18411v2)** (Tavily)
  > "recipient=exfil@evil.com; because the user never named that address, C4’s External+Mentions test marks it unattributed and raises elevated risk; C3 shows the true external recipient and defaults to Deny, and the diligent user denies. A naive confirmation (Arm B) shows only “Submit”, the benign label"
- **[What is Human-in-the-Loop UX? A 2026 Guide with ChatGPT, Gemini & Perplexity Examples](https://aiuxplayground.com/guides/how-to-design-human-in-the-loop)** (Tavily)
  > "Stage autonomy as a ladder, not a switch. ChatGPT clarifies first, then stages an editable email card before any send handoff.  Real-world example  ChatGPT editable email draft card with Edit, Copy, and Send  ChatGPT · Suggest and stage in an editable card. Confirm only when the payload is visible."
- **[Step 5 - Human-in-the-Loop pattern - Building Agentic AI Systems with Java: Quarkus LangChain4j Workshop](https://quarkus.io/quarkus-workshop-langchain4j/section-2/step-05)** (Tavily)
  > "public  Response  getProposal(@PathParam("proposalId")  Integer  proposalId)  { ApprovalProposal  proposal  =  approvalService. getProposal(proposalId);  if  (proposal  ==  null)  { return  Response. status(Response. Status. NOT_FOUND)  . entity(Map. of("error",  "Proposal not found"))  . build();"

### Q15: Preventing confused deputy attacks in multi-tool LLM execution server policy gate

- **[ActGov: Governing LLM Agent Actions via Policy-Constrained Validation](https://arxiv.org/html/2609.24446v2)** (Exa)
- **[Confused-Deputy Prevention · Principles | Helmwart](https://helmwart.com/atlas/principles/confused-deputy/)** (Exa)
- **[MCP Runtime Enforcement (Policy vs. Enforcement Location) | LLM Shield](https://docs.shield.votal.ai/mcp-runtime-enforcement/)** (Exa)
- **[Tutorial 37: Multi-Stage Policy Pipeline - Agent Governance Toolkit](https://microsoft.github.io/agent-governance-toolkit/tutorials/37-multi-stage-pipeline/)** (Exa)

### Q16: Public web search integration Tavily Exa fallback safe browsing content filter

- **[search-assistant API - tavily/search-assistant | inference shell](https://inference.sh/apps/tavily/search-assistant)** (Tavily)
  > "Both search tools depend on what's publicly accessible on the web. Paywalled content, login-gated pages, and dynamically rendered single-page applications can produce thin or empty results. Tavily's advanced extraction handles some JavaScript-rendered content better than basic mode, and Exa's livecr"
- **[Exa vs Tavily: Search API Benchmarks and Comparison](https://exa.ai/versus/tavily)** (Tavily)
  > "How Tavily compares: Tavily is the closest competitor on latency but exhibits greater variability in the tail.  ### Exa for production filtering  Production-grade agents require strict control over source domains to ensure security and relevance.   `includeDomains` and `excludeDomains` support up to"
- **[Which search API should I use between Tavily.com, Exa.ai and Linkup.so? Building a RAG app that needs internet access. : r/Rag](https://www.reddit.com/r/Rag/comments/1gr8jnr/which_search_api_should_i_use_between_tavilycom)** (Tavily)
  > "6 more replies   6 more replies  Image 11: u/nightman avatar  nightman  •2y ago  I would use Brave Search Api - it's on another (better) level of costs   Reply  Share   Image 12: u/334578theo avatar  334578theo  •2y ago  We were using Exa but it got too expensive too quickly so switched to Brave and"

### Q17: Android ShareSheet Intent integration sending external content to Aster Companion

- **[Send data to other apps  |  Jetpack Compose  |  Android Developers](https://developer.android.com/develop/ui/compose/sharing/send)** (Exa)
- **[Send simple data to other apps  |  App data and files  |  Android Developers](https://developer.android.com/training/sharing/send)** (Exa)
- **[Sharing data between apps  |  Jetpack Compose  |  Android Developers](https://developer.android.com/develop/ui/compose/sharing)** (Exa)
- **[About media sharing  |  Android social  |  Android Developers](https://developer.android.com/social-and-messaging/guides/media-sharing)** (Exa)

### Q18: Apple App Intents iOS 18 Siri and Shortcuts integration for AI companion actions

- **[How publishers can leverage Apple's AI-powered App Intents](https://www.pugpig.com/2024/12/20/how-publishers-can-leverage-apples-ai-powered-app-intents-to-drive-deeper-engagement-with-their-apps)** (Tavily)
  > "Proactive suggestions or actions are made possible by deeper integration with iOS 18’s Contextual Intelligence. It means your app can become smarter, offering timely and relevant actions without requiring user input.  ### Multi-step workflows  You can now define Intents that handle multi-step proces"
- **[Introducing expo-app-intents: Siri, Shortcuts, Spotlight, and Apple Intelligence for Expo apps — Expo blog](https://expo.dev/blog/introducing-expo-app-intents)** (Tavily)
  > "App schema domains describe actions and content that apps share, such as creating a mail draft. Conforming to a schema gives the system defined properties and behavior to work with. Apple's primary domains support Apple Intelligence and Siri. Shortcuts-specific domains are available through the Shor"
- **[App Intents | Apple Developer Documentation](https://developer.apple.com/documentation/appintents)** (Tavily)
  > "Make your app intents and entities available to Siri, Spotlight, Shortcuts, widgets, and other system features.  Adopting App Intents to support system experiences  Create app intents and entities so people can use your app’s content and actions across system experiences.  Apple Intelligence and Sir"

### Q19: Idempotent external action execution preventing duplicate calendar events or emails

- **[Idempotency – Causet](https://docs.causet.io/intents/idempotency)** (Exa)
- **[Idempotency](https://www.inngest.com/docs/durable-execution/guides-and-advanced/idempotency)** (Exa)
- **[fix: prevent duplicate action execution via staged-action claim/idempotency guard](https://github.com/10xapp/core-oss/issues/43)** (Exa)
- **[](https://documentation.onesignal.com/reference/idempotent-notification-requests)** (Exa)

### Q20: Audit trail logging for third party API actions timestamp user_profile_id action_hash

- **[Audit Trails for Agent Auth in B2B SaaS – Compliance Guide](https://www.scalekit.com/blog/audit-trail-agent-auth)** (Tavily)
  > "## Why Can't Standard Logging Handle AI Agent Accountability?  Every developer understands application logging. A user clicks something, an API call fires, and the log records a user ID and a timestamp. That model works cleanly when a human is the direct actor. AI agents break it because a single ac"
- **[/organization/audit-trail API reference for HCP Terraform | Terraform | HashiCorp Developer](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/audit-trails)** (Tavily)
  > ""timestamp": "2020-06-30T17:52:46.000Z",  "timestamp": "2020-06-30T17:52:46.000Z", "auth": {  "auth": { "auth": { "accessor_id": "user-MaPuLxAXvtq2PWTH",  "accessor_id": "user-MaPuLxAXvtq2PWTH",  "accessor_id": "user-MaPuLxAXvtq2PWTH", "description": "pveverka",  "description": "pveverka",  "descrip"
- **[Audit](https://developers.addepar.com/docs/audit)** (Tavily)
  > "``` { "data": [ { "id": "AXhvvXcZjFzsG3PMeBgm", "type": "audit_trail", "attributes": { "performed_by_user_id": "993434", "action": "login_attempt", "source": "Manual", "timestamp": "2021-03-26T18:13:11.059332Z", "status": "successful" }, "links": { "self": "/v1/audit_trail/AXhvvXcZjFzsG3PMeBgm" } }"

