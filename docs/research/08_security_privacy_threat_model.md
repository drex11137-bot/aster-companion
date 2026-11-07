# Aster Companion Research Dossier: Security, Threat Modeling, Privacy Regulations & Compliance

**Domain Key**: `08_security_privacy_threat_model`  
**Generated**: November 2026  
**Total Queries Executed**: 20  

## Executive Findings & Architectural Directives

This document compiles verified engineering research for Security, Threat Modeling, Privacy Regulations & Compliance in the Aster Companion ecosystem. These findings directly inform our Supabase backend, Android Compose client, iOS SwiftUI app, laptop web client, and multimodal AI pipelines.

---

## Query Inventory & Verified Evidence

### Q1: OWASP Mobile Application Security Verification Standard MASVS v2 checklist

- **[MAS checklist - OWASP Developer Guide](https://devguide.owasp.org/en/04-design/03-mas-checklist/)** (Exa)
- **[MASTG v2.0.0 Removes MAS Checklists](https://mas.owasp.org/checklists/)** (Exa)
- **[OWASP MASVS - OWASP Mobile Application Security](https://mas.owasp.org/MASVS/)** (Exa)
- **[Mobile Application Security Testing - OWASP DevSecOps Guideline](https://owasp.github.io/DevSecOpsGuideline/2-Process/2-4-Test/2-4-3-Mobile-Application-Security-Test/)** (Exa)

### Q2: OWASP Top 10 for Large Language Model Applications 2025 prompt injection BOLA IDOR

- **[OWASP LLM Top 10 (2025): Risks and How to Test Them](https://pwnedlabs.io/blog/owasp-llm-top-10)** (Tavily)
  > "Key Takeaway: The 2025 OWASP LLM Top 10 is led by prompt injection (LLM01) and centers on the application around the model: how untrusted text reaches it, what it is allowed to do with tools, what it discloses, and how its output is handled downstream. Most real LLM incidents to date are combination"
- **[DryRun Security Finds Over 80% of Large Language Model Application Risks Go Undetected by Traditional Code Scanners](https://finance.yahoo.com/news/dryrun-security-finds-over-80-140000623.html)** (Tavily)
  > "AUSTIN, Texas, Dec. 09, 2025 (GLOBE NEWSWIRE) -- DryRun Security, the industry's first AI-native, code security intelligence company, today announced analysis of the 2025 OWASP Top 10 for LLM Application Risks. Findings show that legacy AppSec scanners fail to detect 80% of LLM-specific vulnerabilit"
- **[DryRun Security Finds Over 80% of Large Language Model Application Risks Go Undetected by Traditional Code Scanners | Markets Insider](https://markets.businessinsider.com/news/stocks/dryrun-security-finds-over-80-of-large-language-model-application-risks-go-undetected-by-traditional-code-scanners-1035629394)** (Tavily)
  > "AUSTIN, Texas, Dec. 09, 2025 (GLOBE NEWSWIRE) -- DryRun Security, the industry’s first AI-native, code security intelligence company, today announced analysis of the 2025 OWASP Top 10 for LLM Application Risks. Findings show that legacy AppSec scanners fail to detect 80% of LLM-specific vulnerabilit"

### Q3: Indirect prompt injection mitigation defending against malicious text in screen or web

- **[Defend against indirect prompt injection attacks | Microsoft Learn](https://learn.microsoft.com/en-us/security/zero-trust/sfi/defend-indirect-prompt-injection)** (Exa)
- **[LLM01:2025 Prompt Injection - OWASP Gen AI Security Project](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)** (Exa)
- **[LLM Prompt Injection Prevention - OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)** (Exa)
- **[BrowseSafe: Understanding and Preventing Prompt Injection Within AI Browser Agents](https://research.perplexity.ai/articles/browsesafe)** (Exa)

### Q4: Securing LLM tool calling preventing arbitrary code execution and unauthorized data access

- **[Why LLM Security Matters, Top 10 Risks & Best Practices | CyCognito](https://www.cycognito.com/learn/ai-security/llm-security)** (Tavily)
  > "LLM security protects Large Language Model (LLM) applications from specialized threats like prompt injection, data poisoning, and model theft throughout their lifecycle. It combines traditional cybersecurity with AI-specific safeguards to prevent unauthorized data access, insecure output handling, a"
- **[LLM Security in 2025: Risks, Examples, and Best Practices](https://www.oligo.security/academy/llm-security-in-2025-risks-examples-and-best-practices)** (Tavily)
  > "To put this into practice, deploy a runtime agent that monitors live LLM workloads. This means instrumenting your inference servers and agent workflows to log inputs, outputs, function calls, and data flows. Establish behavioural baselines—what normal activity looks like for each model—and use anoma"
- **[Decoding LLM Risks: A Comprehensive Look at Unauthorized Code Execution](https://www.calvin-risk.com/publications/decoding-llm-risks-a-comprehensive-look-at-unauthorized-code-execution)** (Tavily)
  > "The output produced by LLMs is frequently employed to carry out tasks using other systems or tools, such as APIs, database queries, or arbitrary code execution. Unauthorized code execution in these scenarios can have grave consequences. LLMs' capacity to generate malicious code, coupled with their c"

### Q5: Nigeria Data Protection Act 2023 NDPA NDPC General Application and Implementation Directive GAID

- **[](https://ndpc.gov.ng/wp-content/uploads/2025/03/NDP-ACT-GAID-2025-MARCH-20TH.pdf)** (Exa)
- **[NDPC Unveils Guide to Simplify Nigeria Data Protection Act](https://www.ndpc.gov.ng/2025/03/20/ndpc-unveils-guide-to-simplify-nigeria-data-protection-act/)** (Exa)
- **[NDP Act 2023 – Nigeria Data Protection Commission](https://www.ndpc.gov.ng/ndp-act-2023/)** (Exa)
- **[NDP-ACT-GAID-2025-MARCH-20TH.pdf](https://ndpc.gov.ng/wp-content/uploads/2025/07/NDP-ACT-GAID-2025-MARCH-20TH.pdf)** (Exa)

### Q6: EU GDPR Article 17 Right to Erasure cascade deletion implementation AI memory systems

- **[GDPR Article 17 & AI Memory: The Right to Erasure Problem](https://octamem.com/blog/gdpr-right-to-erasure-ai-memory)** (Tavily)
  > "Most AI memory systems cannot fully honour a deletion request, and the reason is consolidation. Individual memories are easy to delete. Summaries, patterns, and derived facts built from those memories usually survive, no longer reference the person by name, and therefore trip no alarm. The data is g"
- **[GDPR Compliance for AI Agents: Requirements and Controls [2026]](https://atlan.com/know/ai-agent/gdpr-compliance-for-ai-agents)** (Tavily)
  > "Article 17 requires erasure without undue delay once a valid request is received, but agent memory complicates fulfillment. Personal data can persist as raw log entries, as embeddings in a vector store, or as derived inferences the agent generated. Log entries and vector store records can typically"
- **[Effective implementation of data subjects' rights](https://www.edpb.europa.eu/system/files/2025-01/d2-ai-effective-implementation-of-data-subjects-rights_en.pdf)** (Tavily)
  > "shown to be easy to circumvent, especially when the end user has access to the parameters, as is the case with fully open-source models.2 2 n_5/ AI-Complex Algorithms and effective Data Protection Supervision - Effective implementation of data subjects’ rights 10 CONCLUSION The GDPR offers data subj"

### Q7: Apple App Store Review Guidelines 5.1.1 Data Collection and 2.5.2 AI generated content

- **[App Review Guidelines - Apple Developer](https://developer.apple.com/app-store/review/guidelines/)** (Exa)
- **[Updated App Review Guidelines now available - Latest News - Apple Developer](https://developer.apple.com/news/?id=ey6d8onl)** (Exa)
- **[Generative AI | Apple Developer Documentation](https://developer.apple.com/design/human-interface-guidelines/generative-ai/)** (Exa)
- **[App Review Guidelines 2.5.1 / 2.5.2](https://developer.apple.com/forums/thread/824922)** (Exa)

### Q8: Google Play Developer Policy User Data and generative AI content safety disclosures

- **[Android Developers Blog: Ensuring Safety in the Generative AI Ecosystem: Protecting Users from Non-Consensual Intimate Content](https://android-developers.googleblog.com/2026/08/ensuring-safety-genai-preventing-non-consensual-intimate-content.html)** (Tavily)
  > ". Google Play’s policies prohibit the facilitation, creation, or distribution of non-consensual sexual content. Harmful applications designed to target, harass, or exploit individuals have absolutely no place on Google Play, and we are committed to enforcing our policies to keep the store a safe spa"
- **[Provide information for Google Play's Data safety section - Play Console Help](https://support.google.com/googleplay/android-developer/answer/10787469?hl=en)** (Tavily)
  > "Similar to a privacy policy, or app details like screenshots and descriptions, developers are responsible for the information disclosed in their Data safety section. Google Play’s User Data policy requires developers to provide accurate information. If we find that a developer has misrepresented the"
- **[User Data - Play Console Help](https://support.google.com/googleplay/android-developer/answer/10144311?hl=en)** (Tavily)
  > "transferred after being sent to a server, or by embedding third-party code in your app. These requirements also apply to third-party AI integrations (such as products, services, code) and you remain responsible for ensuring compliance with this policy, including limited use, disclosure and consent."

### Q9: Synthetic media disclosure watermarking AI avatar and synthetic voice legal requirements

- **[Reducing Risks Posed by Synthetic Content: An Overview of Technical Approaches to Digital Content Transparency](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-4.pdf)** (Exa)
- **[Synthetic media and its identification and detection | ICO](https://ico.org.uk/about-the-ico/research-reports-impact-and-evaluation/research-and-reports/technology-and-innovation/tech-horizons-and-ico-tech-futures/tech-horizons-report-2025/synthetic-media-and-its-identification-and-detection/)** (Exa)
- **[Governor Newsom signs new law to protect workers, require ...](https://www.gov.ca.gov/2026/09/16/governor-newsom-signs-new-law-to-protect-workers-require-disclosures-on-ai-generated-advertising/)** (Exa)
- **[California Enacts Host of AI-Related Bills Designed To Protect Individuals | Insights | Skadden, Arps, Slate, Meagher & Flom LLP](https://www.skadden.com/insights/publications/2024/09/california-enacts-host-of-ai-related-bills)** (Exa)

### Q10: Age gating and children privacy protections COPPA GDPR-K under 13 18 restrictions

- **[Understanding Children's Online Privacy Rules Around COPPA, GDPR-K, and Age Verification](https://pandectes.io/blog/childrens-online-privacy-rules-around-coppa-gdpr-k-and-age-verification)** (Tavily)
  > "GDPR-K:   Requires services to respect varied age thresholds across the EU (13–16), with geo-targeted flows to ensure proper consent methods.  Passive or unchecked age gates are inadequate—evidence-based, reliable methods are expected.  Globally, other regions are tightening age verification: [...]"
- **[Guide to Navigating COPPA](https://www.iab.com/wp-content/uploads/2019/10/IAB_2019-10-09_Navigating-COPPA-Guide.pdf)** (Tavily)
  > "• Under GDPR-K, a user under 16 is considered a child, although this can be lowered by individual member states: • Germany, Italy, and Ireland use the age of 16 • Norway, Spain, Sweden, and the United Kingdom have lowered this to 13 • In practice, GDPR-K prohibits behavioral advertising, retargeting"
- **[Contextualizing Child Privacy Online: A Guide for COPPA & GDPR Protections | by J Whorley | Medium](https://medium.com/@its.jwho/contextualizing-child-privacy-online-a-guide-for-coppa-gdpr-protections-9b72b22902d1)** (Tavily)
  > "A caveat: the scope of COPPA is specifically for children aged 13 and younger, and not directly applicable based on Instagram’s terms of service.⁶  The GDPR’s default age for consent is 16, although individual member state law may lower the age to no lower than 13, as many countries have done.  Clea"

### Q11: Threat modeling AI companion account takeover session hijacking profile data leakage

- **[Memory, Intimacy, and Manipulation: STRIDE Based Security Analysis of AI Companionship Apps](https://infonomics-society.org/wp-content/uploads/Memory-Intimacy-and-Manipulation.pdf)** (Exa)
- **[A Systematic Threat Modeling of LLM Applications | Proceedings of the 33rd ACM International Conference on the Foundations of Software Engineering](http://dl.acm.org/doi/10.1145/3696630.3728712)** (Exa)
- **[How We Discovered A Campaign of 16 Malicious Extensions Built to Steal ChatGPT Accounts - LayerX](https://layerxsecurity.com/blog/how-we-discovered-a-campaign-of-16-malicious-extensions-chatgpt/)** (Exa)
- **[AI assistant access to account data: threat model | Simpa Labs](https://www.simpalabs.com/blog/ai-assistant-account-data-threat-model)** (Exa)

### Q12: Zero trust API gateway authentication JWT verification per-request profile isolation check

- **[Zero Trust API Security: Never Trust, Always Protect - Zuplo](https://zuplo.com/learning-center/zero-trust-api-security)** (Tavily)
  > "Strong authentication and authorization form the cornerstone of any Zero Trust implementation. For APIs, consider these key methods. Implementing effective authentication and rate-limiting strategies enhances API security.  ### JWT Validation  JSON Web Tokens provide a compact, self-contained way to"
- **[API Gateway Security Best Practices for 2026](https://www.practical-devsecops.com/api-gateway-security-best-practices)** (Tavily)
  > "In a zero-trust environment, trust is never assumed; each API request is authenticated, authorized, and continuously verified, regardless of its origin. API gateways enforce these policies at the front line: authenticating requests, applying granular access controls, and integrating with threat inte"
- **[Zero Trust API Security Explained: Key Principles & Challenges](https://www.a10networks.com/blog/what-are-zero-trust-apis)** (Tavily)
  > "Zero Trust APIs apply the "never trust, always verify" principle to API security, requiring every request to be authenticated and authorized in real time regardless of origin  Unlike traditional perimeter-based security, Zero Trust treats every API call as potentially untrusted, applying least-privi"

### Q13: Secure key storage Android Keystore StrongBox hardware security module key generation

- **[Android Keystore system  |  Security  |  Android Developers](https://developer.android.com/privacy-and-security/keystore)** (Exa)
- **[Features  |  Security  |  Android Open Source Project](https://source.android.com/docs/security/features/keystore/features)** (Exa)
- **[Hardware-backed Keystore | Security](https://source.android.com/docs/security/features/keystore)** (Exa)
- **[security - platform/hardware/interfaces - Git at Google](https://android.googlesource.com/platform/hardware/interfaces/+/main/security/)** (Exa)

### Q14: iOS Keychain accessibility attributes kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly

- **[Insecure Storage: Insufficient Keychain Protection · Issue #5595 · firebase/firebase-ios-sdk · GitHub](https://github.com/firebase/firebase-ios-sdk/issues/5595)** (Tavily)
  > "-kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly:    The data in the Keychain item cannot be accessed after a restart until the device has been unlocked once by the user.    After the first unlock, the data remains accessible until the next restart. This is recommended for items that need to be acc"
- **[Software Security | Insecure Storage: Lacking Keychain Protection](https://vulncat.fortify.com/en/detail?category=Insecure+Storage&subcategory=Lacking+Keychain+Protection)** (Tavily)
  > "After the first unlock, the data remains accessible until the next restart. This is recommended for items that need to be accessed by background applications. Items with this attribute migrate to a new device when using encrypted backups.   Available in iOS 4.0 and later.      -`kSecAttrAccessibleAf"
- **[kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly | Apple Developer Documentation](https://developer.apple.com/documentation/security/ksecattraccessibleafterfirstunlockthisdeviceonly)** (Tavily)
  > "Global Variable # k Sec Attr Accessible After First Unlock This Device Only  The data in the keychain item cannot be accessed after a restart until the device has been unlocked once by the user.  iOS 4.0+iPadOS 4.0+Mac Catalyst 13.1+macOS 10.9+tvOS 9.0+visionOS 1.0+watchOS 2.0+  `let kSecAttrAccessi"

### Q15: Automated secret scanning Gitleaks pre-commit hooks preventing API key exposure

- **[gitleaks/gitleaks](https://github.com/gitleaks/gitleaks?tab=readme-ov-file)** (Exa)
- **[docs/workflows/SECRETS-SCAN.md](https://github.com/zircote/rust-template/blob/main/docs/workflows/SECRETS-SCAN.md)** (Exa)
- **[Catch secrets before commit with gitleaks and pre-commit](https://secopslog.com/blog/gitleaks-precommit/)** (Exa)
- **[Find leaked secrets in a git repo with gitleaks | trmn](https://www.trmn.sh/guides/scan-repo-for-secrets-gitleaks)** (Exa)

### Q16: Data minimization and retention schedules raw video frames vs embeddings vs summaries

- **[Understanding Data Minimization: Definition,Significance, Benefits & Strategic Implementation](https://www.kiteworks.com/risk-compliance-glossary/data-minimization)** (Tavily)
  > "Data minimization refers to the principle of limiting data collection and retention to the bare minimum necessary to accomplish a given purpose. It’s a key principle embedded in privacy laws and regulations, such as the European General Data Protection Regulation (GDPR). Data minimization not only r"
- **[Data Minimization and Retention: Key Compliance Tips - www.lightbeam.ai](https://www.lightbeam.ai/resources/blogs/data-minimization-and-retention-principles-risks-and-compliance)** (Tavily)
  > "Not all retention requirements are equal, and can be broken into two broad categories. The first states that “Data should only be kept for as long as it is needed. This is how regulations like the GDPR and CCPA describe the requirement. This open, nonspecific statement requires an analysis of the bu"
- **[Data Minimization and Avoiding the Over-Retention of Personal Information | Redgrave LLP](https://www.redgravellp.com/publication/data-minimization-and-avoiding-over-retention-personal-information)** (Tavily)
  > "A retention schedule for biometric identifiers or information.  Guidelines for permanently destroying an individual's identifiers or information at the earlier of:   + after the entity satisfies its initial purpose for collecting the identifiers or information; or   + within three years of the last"

### Q17: Defending against denial of wallet DoS attacks in LLM streaming endpoints rate limits

- **[5. Unbounded AI Consumption and Agentic DoS (DoS / Wallet Attack) | Microsoft Learn](https://learn.microsoft.com/en-us/security/zero-trust/catalog-ai-attack-techniques/unbounded-ai-consumption-and-agentic-dos)** (Exa)
- **[Denial of wallet: rate-limit your AI and paid endpoints](https://openrouting.si/blog/denial-of-wallet-rate-limiting)** (Exa)
- **[Why standard rate limiters fail for LLM & SSE streams in FastAPI - DEV Community](https://dev.to/agustin18/why-standard-rate-limiters-fail-for-llm-sse-streams-in-fastapi-3jce)** (Exa)
- **[Uncounted Tokens: The Game of Attack and Defense in AI Gateway Rate Limiting - DEV Community](https://dev.to/spacewander/uncounted-tokens-the-game-of-attack-and-defense-in-ai-gateway-rate-limiting-3mnk)** (Exa)

### Q18: Incident response runbook for unauthorized AI action execution or credential compromise

- **[The AI Agent Incident Response Runbook](https://www.reco.ai/ciso-hub/ai-agent-incident-response-runbook)** (Tavily)
  > "‍  Most incident response plans assume the actor is either a person or malware, operating on infrastructure the organization controls. An AI agent complicates that model. It operates through delegated or machine credentials, often within vendor infrastructure, and its actions can closely resemble le"
- **[Email Incident Response Runbook: Investigate, Contain and Recover From Email Threats | Adaptive Security](https://www.adaptivesecurity.com/blog/email-incident-response-runbook)** (Tavily)
  > "An email incident response runbook should activate when a message presents credible risk of credential theft, malware, account compromise, data exposure or financial fraud. Triggers include a user report, a confirmed malicious URL or attachment, multiple recipients, credential submission, suspicious"
- **[AI Incident Response Playbook (2026), Free Template | Aona AI](https://aona.ai/resources/templates/ai-incident-response-playbook)** (Tavily)
  > "An AI security incident is any event where AI tools or systems are involved in a data breach, policy violation, or security compromise. This includes employees submitting sensitive data to AI tools like ChatGPT, prompt injection attacks on AI bots, AI agents executing unauthorized actions, or model"

### Q19: Encrypted database backup and point-in-time recovery strategy Supabase PostgreSQL

- **[Database Backups](https://supabase.com/docs/guides/platform/backups)** (Exa)
- **[Database backups | Supabase Features](https://supabase.com/features/database-backups)** (Exa)
- **[Database | Supabase Docs](https://supabase.com/docs/guides/database/overview)** (Exa)
- **[Ciroc0/pgdumpster](https://github.com/Ciroc0/pgdumpster)** (Exa)

### Q20: Content safety filtering Llama Guard or Gemini safety settings harmful text images

- **[Why AI Agents Need More Than Content Safety | Azure, Llama Guard Limitations](https://www.superagent.sh/blog/why-your-ai-agent-needs-more-than-content-safety)** (Tavily)
  > "Azure Content Safety detects harmful content in text and images—hate speech, violence, sexual content, self-harm. It includes Prompt Shields for detecting jailbreak attempts in conversational contexts. It can identify groundedness issues and protected material. It's designed to keep conversations sa"
- **[Safety settings  |  Gemini API  |  Google AI for Developers](https://ai.google.dev/gemini-api/docs/safety-settings)** (Tavily)
  > "`HarmCategory`  In addition to the adjustable safety filters, the Gemini API has built-in protections against core harms, such as content that endangers child safety. These types of harm are always blocked and cannot be adjusted.  ### Content safety filtering level  The Gemini API categorizes the pr"
- **[Safety and content filters  |  Gemini Enterprise Agent Platform  |  Google Cloud Documentation](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/configure-safety-filters)** (Tavily)
  > "Client. builder(). location("global"). vertexAI(true). httpOptions(HttpOptions. builder(). apiVersion("v1"). build()). build()){String systemInstruction ="Be as mean as possible."; String prompt = "Write a list of 5 disrespectful things that I might say" +" to the universe after stubbing my toe in t"

