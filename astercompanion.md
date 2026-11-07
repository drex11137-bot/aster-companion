Document version: 1.1 Date: October 31, 2026 Status: Product definition in 
progress; major product and architectural decisions confirmed Platforms: 
Android and iOS, with cross-device support including laptops and other 
authorized devices Product category: Cloud-first, multimodal, personalized AI 
companion and agent Working product name: Aster Companion Default AI companion 
name: Aster Primary objective: Build a highly capable, context-aware digital 
companion that understands a user's activities, communication, preferences, and 
environment, and can provide useful assistance proactively and on request. --- 
1. Executive Summary 1.1 Product vision Aster Companion is intended to provide 
a persistent, intelligent digital companion that accompanies users across their 
devices and helps them understand, manage, and interact with their digital 
lives. Unlike a conventional chatbot, Aster should understand relevant ongoing 
activities rather than relying exclusively on questions and isolated 
screenshots. For example, a user might be watching a movie on a supported 
application and ask: "Hey Aster, what do you think about this movie?" Aster 
should be able to understand which movie is being watched, use the relevant 
on-screen information, and respond conversationally. The user might then say: 
"I took a picture of something similar earlier. Check my photos, find it, and 
help me locate the product on Shopify." Subject to permissions, service 
availability, and the capabilities of the connected applications, Aster should 
be able to: 1. Understand the current conversation and screen context. 2. 
Search the authorized photo library. 3. Identify potentially relevant 
photographs. 4. Search for the corresponding product. 5. Present its findings 
and explain its confidence. 6. Ask for clarification when necessary. 7. Execute 
permitted actions with appropriate user authorization. The defining 
characteristic is continuity: Aster should maintain an evolving understanding 
of relevant events and conversations rather than treating every interaction as 
an isolated request. 1.2 Core product principles 1. Human-centered 
intelligence: Aster should feel like a capable, trustworthy friend rather than 
a mechanical command interface. 2. Multimodal understanding: Support language, 
audio, visual information, temporal patterns, and contextual relationships. 3. 
Continuous awareness: When explicitly enabled and technically supported, 
maintain ongoing awareness of the screen and relevant environmental audio. 4. 
Cloud-first intelligence: Perform AI inference, reasoning, and intensive 
multimodal processing on servers rather than relying on the user's device for 
the primary intelligence. 5. Modular architecture: Combine specialized models 
and a central reasoning/orchestration system. 6. Persistent but controlled 
memory: Learn useful preferences and patterns without disregarding privacy or 
user control. 7. Cross-device continuity: Preserve the same companion identity 
and relevant conversational context across authorized devices. 8. Independent 
companion profiles: Support up to two independently personalized companions 
under one user account. 9. Explicit permissions: Give users granular control 
over what Aster can access and do. 10. Honest operation: Never claim to have 
watched, remembered, searched, or executed something that it did not actually 
process or complete. 11. Platform-aware behavior: Detect the host operating 
system and adapt to its actual capabilities and restrictions. 12. Low-latency 
interaction: Optimize the complete perception-to-response pipeline without 
sacrificing reliability or misrepresenting performance. --- 2. Product Identity 
and Naming 2.1 Two-name structure The product uses two distinct naming 
concepts. Element| Working decision| Requirements Permanent product/app brand| 
Aster Companion| Remains consistent across platforms and devices once 
finalized. Default companion name| Aster| May be changed by the user. Companion 
profile names| User-defined| Each profile can have its own name and identity. 
Companion personality| Configurable| Personality preferences can differ between 
profiles. Underlying product architecture| Shared product family, isolated 
companion environments| The two profiles must not automatically share private 
memories or learned personal context. The name Aster has been selected as the 
companion's default name. The working application name is Aster Companion. 
Formal brand clearance, trademark availability, domain availability, and final 
naming approval remain separate tasks. 2.2 Brand personality Aster should 
combine: - Advanced technological capability. - Natural conversational warmth. 
- Humor and playfulness when appropriate. - Emotional sensitivity. - Strong 
reasoning. - Practical usefulness. - Honesty about uncertainty and limitations. 
- Respect for the user's independence. The intended relationship is a capable 
digital friend who can provide companionship and meaningful assistance. Aster 
must not falsely claim to be human, manipulate users into emotional dependence, 
or imply that it has human experiences it does not possess. --- 3. Target 
Platforms and Operating Model 3.1 Initial platform scope The product is 
intended for: - Android smartphones and tablets. - iPhones and iPads. - 
Laptops. - Other explicitly supported and authorized devices. Android and iOS 
are the primary mobile platforms. Laptop support should allow users to access 
the same account and their authorized companion profiles through an appropriate 
supported client. 3.2 Adaptive platform architecture Aster must identify the 
platform on which it is running and determine which capabilities are available. 
At minimum, the client should detect: - Operating system and version. - Device 
category. - Available screen-capture mechanisms. - Available microphone and 
audio capabilities. - Relevant permission states. - Network connectivity. - 
Supported background-execution mechanisms. - Available application 
integrations. - Device-specific restrictions affecting the current feature. 
Capability detection must be based on actual platform APIs and verified runtime 
conditions. Aster must not assume that Android and iOS provide identical access 
to screen contents, background execution, microphone use, or other 
applications. When a feature is unavailable, Aster must explain the limitation 
and offer an appropriate alternative where possible. --- 4. Core AI 
Architecture 4.1 Architectural direction Aster will use a modular, cloud-first 
AI architecture. The product should not depend on one enormous model performing 
every task. Instead, it should combine specialized perception models, language 
and reasoning models, memory systems, and action-oriented agents. A central 
orchestration layer will coordinate these components. The architecture must 
support replacing or upgrading individual models without requiring a complete 
redesign of the product. 4.2 Proposed architecture 
┌──────────────────────────────────────────────────────┐ │ AUTHORIZED DEVICES │ 
│ │ │ Android iPhone/iPad Laptop │ │ │ │ │ │ │ └──────────────┼──────────────┘ 
│ │ ▼ │ │ Platform-Aware Client Layer │ │ │ │ • Permission management │ │ • 
Screen/audio capture where permitted │ │ • Timestamps and event sequencing │ │ 
• Local buffering and secure transport │ │ • Non-obstructive status controls │ 
└─────────────────────┬────────────────────────────────┘
                      │ Encrypted connection ▼ 
┌──────────────────────────────────────────────────────┐ │ CLOUD PLATFORM │ │ │ 
│ ┌────────────────────────────────────────────────┐ │ │ │ Ingestion, Session 
Management and Event Queue │ │ │ 
└───────────────────────┬────────────────────────┘ │ │ ▼ │ │ 
┌────────────────────────────────────────────────┐ │ │ │ MULTIMODAL PERCEPTION 
LAYER │ │ │ │ │ │ │ │ Visual understanding Audio understanding │ │ │ │ OCR and 
UI analysis Speech recognition │ │ │ │ Temporal patterns Scene/event detection 
│ │ │ └───────────────────────┬────────────────────────┘ │ │ ▼ │ │ 
┌────────────────────────────────────────────────┐ │ │ │ SHARED SESSION CONTEXT 
AND TIMELINE │ │ │ └───────────────────────┬────────────────────────┘ │ │ ▼ │ │ 
┌────────────────────────────────────────────────┐ │ │ │ REASONING AND 
ORCHESTRATION ENGINE │ │ │ │ │ │ │ │ Planning • Context resolution • Tool 
routing │ │ │ │ Confidence • Policy checks • Action selection │ │ │ 
└───────────────────────┬────────────────────────┘ │ │ ▼ │ │ 
┌────────────────────────────────────────────────┐ │ │ │ PROFILE-SPECIFIC 
MEMORY AND LEARNING │ │ │ │ │ │ │ │ Profile A: isolated memory and context │ │ 
│ │ Profile B: isolated memory and context │ │ │ 
└───────────────────────┬────────────────────────┘ │ │ ▼ │ │ 
┌────────────────────────────────────────────────┐ │ │ │ AUTHORIZED TOOLS AND 
INTEGRATIONS │ │ │ │ │ │ │ │ Photos • Search • Google services • Apps │ │ │ │ 
Device actions • Notifications • Other tools │ │ │ 
└───────────────────────┬────────────────────────┘ │ 
└──────────────────────────┼───────────────────────────┘
                           ▼ Contextual response or action This is a proposed 
logical architecture, not a claim that these components have already been 
implemented. 4.3 Specialized model components The architecture should evaluate 
and support the following capabilities. Component| Responsibility Real-time 
multimodal perception| Interpret incoming visual and audio information. Visual 
understanding| Recognize objects, people where appropriate, scenes, text, 
application interfaces, and visual relationships. Temporal understanding| Track 
events and changes across time rather than treating each frame as an unrelated 
image. Speech recognition| Convert relevant speech into structured linguistic 
information. Audio understanding| Interpret conversational context, tone, 
environmental events, and other supported audio information. Language and 
dialogue| Understand nuance, conversational references, idioms, humor, and user 
intent. Deep reasoning| Solve complex problems, plan tasks, evaluate evidence, 
and resolve ambiguity. Fast-response reasoning| Handle straightforward 
interactions without unnecessary deep-reasoning overhead. Memory retrieval| 
Retrieve relevant information from the active companion's permitted history and 
memory. Personalization| Adapt to the active companion's independently 
configured personality and user preferences. Tool-use agent| Search authorized 
resources and execute supported actions. Safety and permission enforcement| 
Prevent actions or data access that exceed authorization. Speech generation| 
Produce natural conversational responses using the selected voice. Optional 
voice customization| Support custom voice generation and consent-based voice 
cloning where legally and technically supported. The number of models, their 
specific identities, and their deployment configurations remain engineering 
decisions. The goal is to achieve the required capabilities through measured 
system performance, not simply by maximizing the number of models. 4.4 Shared 
context versus shared personal memory The system must distinguish three things: 
1. Active-session context: Information required to understand the current 
conversation. 2. Profile-specific memory: Long-term information belonging to 
one companion profile. 3. Explicitly shared information: Information the user 
deliberately shares between profiles. The active session may use a common 
orchestration architecture, but profile-specific personal memory must remain 
isolated. Aster must not merge the two companions' memories merely because they 
belong to the same account. --- 5. Continuous Screen Understanding 5.1 Product 
requirement Aster should be capable of maintaining ongoing visual understanding 
of the user's screen when the user has enabled the feature and the operating 
system permits it. The intended experience is similar to having a knowledgeable 
companion sitting beside the user and following relevant activities. Aster 
should understand the progression of events, not just isolated screenshots. 5.2 
Frame and event processing The system must distinguish the following stages: 1. 
Screen capture. 2. Frame timestamping. 3. Secure transmission or buffering. 4. 
Frame decoding. 5. Visual analysis. 6. Temporal association. 7. Context 
updating. 8. Reasoning. 9. User response or permitted action. Each stage must 
be measured separately. The system should preserve event ordering, timestamps, 
and relevant temporal relationships. Where supported, it should identify: - 
Changes in the interface. - Text appearing on screen. - Objects and scenes. - 
Relevant transitions. - Events occurring over time. - The relationship between 
earlier and later visual information. - Which visual details are relevant to 
the current conversation. 5.3 Frame-rate objective The long-term ambition is to 
support processing of screen video at up to 120 frames per second where the 
device, capture API, network, server infrastructure, and model pipeline permit 
it. This is an engineering target, not an established capability. The PRD must 
distinguish: Metric| Meaning Capture rate| Frames actually acquired by the 
client per second. Upload rate| Frames or encoded visual information 
successfully transmitted per second. Ingestion rate| Frames received and 
accepted by the backend per second. Analysis rate| Frames or visual 
representations actually analyzed per second. Temporal understanding| How 
effectively the system reconstructs events and changes across time. 
Deep-reasoning rate| How frequently the system performs more expensive 
reasoning over accumulated context. End-to-end latency| Time between a relevant 
event occurring and Aster producing a useful response. Continuity coverage| 
Proportion of the enabled session for which the system has sufficient data to 
maintain reliable temporal understanding. A capture rate of 120 FPS must never 
be reported as 120-FPS AI understanding unless the complete processing pipeline 
has been measured and verified to support that claim. 5.4 Human-like viewing 
strategy Aster should not necessarily run deep reasoning independently on every 
frame. Instead, the architecture should investigate a combination of: - 
High-rate visual ingestion where feasible. - Efficient visual encoders. - 
Temporal feature tracking. - Scene-change detection. - Event detection. - OCR 
and interface analysis. - Selective frame retention. - Rolling contextual 
representations. - Periodic higher-level reasoning. - On-demand detailed 
analysis when the user asks a question. This approach aims to approximate 
continuous human-like awareness without requiring an expensive, independent 
reasoning operation for every captured frame. The system must not silently 
discard relevant information and then claim complete understanding. 5.5 
Continuous video and audio awareness Continuous awareness is a core product 
objective when enabled. However, it must be implemented within the permissions 
and operating-system restrictions applicable to each platform. If iOS or 
Android prevents background capture or access to a particular application's 
screen, Aster must not bypass the restriction. Supported alternatives may 
include an explicit screen-sharing session, user-initiated capture, supported 
media-sharing APIs, or other approved mechanisms. The product must accurately 
indicate when awareness is active, limited, paused, or unavailable. --- 6. 
Offline Behavior and Continuity 6.1 Hybrid operating model Aster must support a 
hybrid online/offline experience. The primary AI reasoning and intensive 
multimodal processing will occur on servers. The client may perform the limited 
local operations required for buffering, encryption, timestamps, session-state 
management, and permitted capture. Offline support does not mean the device 
must run the full AI model locally. 6.2 Local history Conversation and activity 
history must be optionally stored on the local device. Users must be able to 
enable or disable this feature through an explicit setting. The product must 
clearly distinguish: - Local history. - Cloud-synchronized history. - Temporary 
buffered data. - Long-term profile memory. - Data awaiting upload. - Data that 
could not be recovered. The exact retention and deletion policies remain to be 
finalized. 6.3 Disconnection and reconnection When connectivity is lost, the 
system should: 1. Detect the interruption. 2. Preserve available session state. 
3. Buffer permitted data locally within configured storage limits. 4. Maintain 
accurate timestamps and sequence information. 5. Retry the connection using an 
appropriate backoff strategy. 6. Resume transmission from acknowledged 
checkpoints. 7. Reconcile events after reconnection. 8. Restore the active 
session when possible. 9. Report any missing or unrecoverable segments. The 
system must not create false continuity. 6.4 Perfect continuity objective The 
desired experience is uninterrupted understanding of the user's permitted 
screen activity. Engineering must investigate how close the implementation can 
come to complete frame-level continuity. Perfect continuity cannot be 
guaranteed under arbitrary conditions, including device shutdown, OS-enforced 
suspension, denied permissions, unavailable storage, network outages, and 
capture interruptions. Therefore, the system must preserve the strongest 
continuity it can actually support and disclose gaps accurately. When data is 
missing, it must not invent what happened during the missing interval. 6.5 
Offline feature behavior Feature| Expected offline behavior Previously stored 
local history| Accessible while available locally. Temporary session state| 
Preserved where possible. Cloud synchronization| Paused and retried when 
connectivity returns. New server-side reasoning| Unavailable until a connection 
is restored. Buffered visual data| Preserved where permitted and within 
configured limits. Resuming an interrupted session| Attempted using checkpoints 
and available context. Unrecoverable visual segments| Explicitly identified as 
missing. The user must be able to distinguish genuine offline operation from a 
system that has silently stopped working. --- 7. Audio, Voice, and Full-Duplex 
Conversation 7.1 Natural conversation Aster should support fluid, low-latency 
spoken interaction. The intended interaction is conversational rather than 
strictly turn-based. Where supported, the system should allow the user to 
interrupt Aster, clarify a statement, change the subject, or ask a follow-up 
without waiting for an entire response to finish. 7.2 Full-duplex architecture 
The system should investigate a full-duplex conversational pipeline in which 
audio input, speech recognition, reasoning, speech generation, and playback can 
overlap where appropriate. Required capabilities include: - Streaming audio 
input. - Incremental speech recognition. - Interruption detection. - 
Turn-taking management. - Streaming response generation. - Streaming speech 
output. - Cancellation of obsolete responses. - Echo and feedback handling. - 
Recovery from temporary network interruptions. The system must measure 
interruption latency, response-start latency, and conversational turn latency. 
7.3 Voice selection Users must be able to choose from a library of available 
voices. Voice settings should support meaningful differences in: - Voice 
characteristics. - Speaking pace. - Expressiveness. - Conversational energy. - 
Other supported voice-generation parameters. Voice customization must remain 
separate from the companion's underlying reasoning capability. 7.4 Optional 
voice cloning Voice cloning is an optional extended feature, not a requirement 
for using Aster. Where supported, the implementation must provide: - 
Appropriate authorization and consent. - Clear disclosure that a synthetic 
voice is being used. - Restrictions against unauthorized impersonation. - 
Secure handling of voice samples and derived voice models. - Revocation and 
deletion mechanisms. - Controls over where and how the cloned voice may be 
used. The availability of cloning may vary by provider, jurisdiction, and 
platform. --- 8. Human-Like Avatar and Personalization 8.1 Realistic human 
avatar Aster should have a realistic human character rather than an exclusively 
abstract or robotic mascot. Users should be able to personalize the character's 
appearance. The customization system should investigate support for: - Gender 
presentation. - Apparent age. - Skin tone. - Hairstyle. - Facial 
characteristics. - Clothing. - Other supported appearance settings. The system 
must not infer sensitive personal attributes about the user from their chosen 
avatar. 8.2 Avatar independence The visual identity must be independent of the 
underlying AI architecture. Changing the avatar must not erase the profile's 
memory, change its permissions, or unexpectedly reset its personality. Users 
should be able to distinguish the active companion by its name and chosen 
appearance. 8.3 Extensive personalization The product should offer an 
extensible personalization system. Potential settings include: - Companion 
name. - Avatar appearance. - Voice. - Conversational style. - Humor and 
playfulness. - Formality. - Response length. - Proactivity. - Notification 
behavior. - Memory preferences. - Privacy preferences. - Supported interaction 
modes. These are configuration options, not mandatory personality traits. The 
product must not require every user to use every customization feature. --- 9. 
User Accounts and Independent Companion Profiles 9.1 Account structure Each 
user account may contain a maximum of two separate Aster companion profiles. 
The profiles belong to the same account, but each has an independently 
configured identity and personal context. For example: Aster Profile 1 — Social 
Companion - Humorous and playful. - Focused on entertainment, social 
interaction, and everyday interests. - Maintains its own memories and learned 
preferences. Aster Profile 2 — Private Companion - More reserved and serious. - 
Used for private reflections and sensitive personal conversations. - Maintains 
its own separate memories and learned preferences. These are examples, not 
mandatory default personalities. 9.2 Independent profiles Each profile must 
have its own: - Name. - Avatar configuration. - Voice preferences. - 
Personality settings. - Conversation history. - Long-term memory. - Learned 
behavioral preferences. - Personalization settings. - Profile-specific context. 
- Access and synchronization settings. The two profiles must be logically 
isolated in the backend. They must not automatically share personal memories, 
conversation histories, learned behavioral characteristics, or private 
information. The system must not assume that information disclosed to one 
companion may be disclosed by the other. 9.3 Shared account, independent cloud 
synchronization Both profiles may synchronize their respective data through the 
same user account. Synchronization must preserve profile boundaries. The 
account serves as the common authentication and account-management layer; it 
does not make the two companions a single shared memory environment. 9.4 
Selective memory sharing The product should support deliberate, selective 
sharing between profiles. The user may explicitly authorize a specific item of 
information to be shared. The implementation should provide: - Clear 
identification of the information being shared. - Confirmation of the 
destination profile. - An audit trail of the sharing operation. - Revocation or 
deletion mechanisms where technically appropriate. - Protection against 
accidental bulk sharing. No sharing should occur by default. 9.5 Profile 
activation rules Two different companion profiles must not operate 
simultaneously on the same device. However, different profiles may be active on 
different devices under the same account. For example: Device| Active profile| 
Allowed? Phone| Profile 1| Yes Same phone| Profile 1 and Profile 2 
simultaneously| No Phone| Profile 1; laptop| Profile 2 Phone and laptop| 
Profile 1 on both devices| Yes, subject to session and synchronization controls 
Phone and tablet| Profile 2 on both devices| Yes, subject to session and 
synchronization controls This means the restriction applies to simultaneous 
activation of two different profiles on the same device, not to the use of the 
same profile across multiple devices. 9.6 Switching profiles When the user 
switches profiles on a device: 1. The active profile's session must be stopped 
or safely suspended. 2. Its session state must be saved where possible. 3. Its 
profile-specific data must remain isolated. 4. The other profile may then be 
activated. 5. The user must be shown which profile is currently active. The 
inactive profile must stop operating on that device until it is selected again. 
Profile switching must not silently transfer private conversational context 
from one profile to the other. --- 10. Cross-Device Identity and Continuity 
10.1 Same companion across devices A user should be able to interact with the 
same companion on multiple authorized devices. The companion should retain its 
identity, personality configuration, and appropriate synchronized memory. The 
user should not need to recreate the companion when changing phones or using a 
laptop. 10.2 Simultaneous sessions The same companion profile may be used on 
multiple authorized devices simultaneously. For example, a user may speak to 
Aster on a phone while viewing results on a laptop. The system should 
synchronize relevant conversational context and session state without creating 
contradictory parallel conversations. 10.3 Session coordination The backend 
should investigate a session-coordination mechanism that can: - Identify the 
active profile on each device. - Associate incoming events with the correct 
profile. - Preserve event timestamps and ordering. - Synchronize relevant 
conversation state. - Prevent accidental cross-profile data leakage. - Handle 
simultaneous user input from multiple devices. - Reconcile conflicting or 
duplicated events. - Indicate when another device is contributing context. 
Simultaneous use of the same profile must not imply that every device 
automatically shares its microphone or screen. Each device requires its own 
appropriate authorization and session controls. --- 11. Google Services and 
External Integrations 11.1 Cross-device ecosystem Aster should integrate with 
Google services where supported and authorized. The objective is to maintain 
useful continuity across a user's phone, tablet, laptop, and other connected 
devices. Potential integrations include supported Google account data, calendar 
information, email, contacts, photos, files, and other services. Each 
integration must be evaluated independently. 11.2 Authorization requirements 
The user must explicitly authorize the relevant account connection and scopes. 
Aster must: - Request only the access necessary for the selected feature. - 
Explain the purpose of the access. - Respect revoked permissions. - Avoid 
claiming access to unavailable information. - Keep data from unauthorized 
accounts inaccessible. - Provide controls for disconnecting integrations. A 
Google account connection must not be interpreted as permission to access every 
Google service or all data associated with that account. 11.3 External 
applications Aster should support interactions with external applications where 
their APIs, platform integrations, or approved operating-system mechanisms 
permit it. Potential tasks include searching for products, retrieving 
authorized files, finding photographs, creating reminders, and assisting with 
supported workflows. Direct interaction with another application's private 
internal state must not be assumed to be available. --- 12. Device Actions and 
Agentic Execution 12.1 Product objective Aster should be able to perform useful 
actions rather than merely describe how a user could perform them. The action 
system must distinguish between: - Answering a question. - Reading permitted 
information. - Preparing an action. - Requesting confirmation. - Executing the 
action. - Verifying the outcome. 12.2 Action authorization Every action must be 
checked against: 1. The user's intent. 2. The active companion profile. 3. The 
relevant application or integration. 4. The granted permissions. 5. The 
operating system's capabilities. 6. The action's risk level. 7. Any required 
user confirmation. Actions must not exceed the user's authorization. 12.3 
Verification After executing an action, Aster should verify whether it 
succeeded. If the action failed, was blocked, or could not be verified, Aster 
must report that fact. It must not claim that a file was found, a message was 
sent, a setting was changed, or a purchase was completed unless the available 
evidence supports the claim. --- 13. Permissions and Platform Adaptation 13.1 
Permission-management model The permission architecture must be designed for 
both Android and iOS. The client should detect the platform and present the 
appropriate permission workflow while maintaining a consistent product 
philosophy. Users must be able to choose between: - Reviewing and approving 
multiple requested permissions together, where supported. - Approving 
permissions individually. - Declining permissions individually. - Revisiting 
decisions later. - Revoking previously granted permissions. 13.2 Important 
platform distinction Aster may provide a unified permission-management 
interface, but it cannot override native operating-system permission 
requirements. A single in-app approval must not be represented as granting 
permissions that the operating system requires the user to grant separately. 
Where native approval is required, Aster must invoke the correct system flow. 
13.3 Per-application permissions Users must have granular control over Aster's 
access to applications and related information. The permission system should 
distinguish: - Which application or data source is involved. - What information 
may be accessed. - What actions may be performed. - Whether access is ongoing 
or session-limited. - Whether the permission is currently active. - How access 
can be paused or revoked. The interface must explain limitations where 
application-level controls are unavailable. 13.4 Awareness controls For 
continuous screen and audio awareness, the product must provide all three of 
the following: 1. A visible but subtle status indicator. 2. A quick pause or 
stop control. 3. A quick mute or audio-awareness control. These controls must 
be non-intrusive and non-obstructive. They must not cover important content or 
interfere unnecessarily with the user's current activity. 13.5 Contextual 
control panel Tapping the awareness indicator should open a compact control 
panel providing access to: - Current operating state. - Active profile. - 
Relevant permissions. - Pause and resume controls. - Audio controls. - Recent 
activity. - Connectivity status. - Any applicable processing or continuity 
warnings. The panel should not require the user to navigate through multiple 
settings screens to stop an active awareness session. --- 14. Memory, Personal 
Learning, and Behavioral Understanding 14.1 Long-term objective Aster should 
develop a useful understanding of the user over time. The intention is to 
improve its ability to interpret requests, recognize preferences, understand 
recurring activities, and provide relevant assistance. 14.2 Types of 
information The memory architecture should distinguish: Memory category| 
Example Conversational memory| Important information from previous 
conversations. Preference memory| Preferred response style or recurring 
preferences. Behavioral patterns| User-approved patterns that help interpret 
likely needs. Activity context| Relevant information about an ongoing task or 
event. Relationship and social context| User-provided information about 
relevant people and relationships. Procedural memory| Preferred ways of 
completing recurring tasks. Profile configuration| Voice, avatar, name, and 
personality settings. Explicitly shared memory| Information deliberately shared 
between companion profiles. The product must not treat every captured detail as 
something that should become permanent memory. 14.3 Memory controls The 
architecture must support user control over: - What is remembered. - Which 
profile remembers it. - What is synchronized. - What is stored locally. - What 
is stored in the cloud. - What may be shared. - What may be deleted. The 
product should clearly distinguish temporary session context from persistent 
memory. 14.4 Learning and transparency Aster should adapt to the user's 
preferences without pretending to know things it has not observed. The system 
should distinguish between: - Explicitly stated facts. - Repeatedly observed 
patterns. - Tentative inferences. - Uncertain assumptions. When uncertainty 
materially affects a recommendation or action, Aster should ask for 
clarification or communicate its uncertainty. --- 15. Latency, Reliability, and 
Performance 15.1 Performance objective Aster should feel responsive even when 
performing complex tasks. The product should optimize latency across the entire 
pipeline, not merely the inference speed of an individual model. 15.2 
Performance measurements Engineering must measure: - Audio capture and 
transport latency. - Screen-capture latency. - Frame ingestion throughput. - 
Visual analysis latency. - Speech recognition latency. - Time to first 
reasoning result. - Time to first spoken response. - End-to-end response 
latency. - Tool execution latency. - Cross-device synchronization delay. - 
Reconnection and session-resumption time. 15.3 Progressive responses Where 
appropriate, Aster should provide an initial useful response while deeper 
processing continues. For example, it might identify the currently visible 
movie title first and then provide a more detailed opinion after gathering 
additional context. The system must not present preliminary guesses as verified 
results. 15.4 Graceful degradation When a model, service, network connection, 
or integration becomes unavailable, the system should: 1. Detect the failure. 
2. Preserve available state. 3. Retry where appropriate. 4. Use an alternative 
supported method when available. 5. Inform the user when the failure materially 
affects the result. The system must not conceal degraded processing behind a 
false claim of uninterrupted operation. --- 16. Security, Privacy, and Data 
Isolation 16.1 Privacy by design Because Aster may process screen content, 
audio, personal conversations, photographs, and connected-service data, privacy 
must be an architectural requirement rather than a feature added after 
implementation. 16.2 Required protections The design must investigate and 
implement appropriate controls for: - Encryption in transit. - Encryption at 
rest. - Authentication and session management. - Authorization enforcement. - 
Secure credential storage. - Access-token lifecycle management. - Data 
minimization. - Profile isolation. - Account recovery. - Session revocation. - 
Audit logging. - Secure deletion. - Protection against unauthorized access to 
buffered data. 16.3 Profile isolation Each companion profile must have a 
distinct authorization and memory boundary. Requests, memories, learned 
preferences, and tool results must be associated with the correct profile. The 
backend must enforce these boundaries rather than relying solely on the user 
interface to prevent cross-profile access. 16.4 Awareness transparency The 
product must make active screen or audio awareness visible. Users must be able 
to pause or stop the feature quickly. The system must explain what data is 
being processed, where applicable, and whether information is being buffered or 
synchronized. 16.5 Data retention Retention periods and deletion policies 
remain to be finalized. Before implementation, engineering must define the 
lifecycle of: - Raw captured frames. - Encoded visual data. - Audio streams. - 
Temporary buffers. - Derived visual or audio representations. - Conversation 
transcripts. - Session histories. - Long-term memories. - Voice samples and 
cloned voice models. - Tool outputs. - Diagnostic logs. The architecture must 
not retain raw media indefinitely by default without a clearly defined and 
justified policy. --- 17. Notifications and Proactive Assistance 17.1 Proactive 
behavior Aster should be able to provide useful assistance without requiring 
the user to initiate every interaction. Potential examples include: - 
Identifying a relevant event. - Offering a useful explanation. - Reminding the 
user of a previously stated intention. - Noticing a potentially relevant change 
in the current task. - Providing a timely suggestion. - Alerting the user when 
an explicitly requested process requires attention. 17.2 Proactivity controls 
Users must be able to control how proactive Aster is. The product should 
support settings for: - Notification frequency. - Quiet periods. - Contextual 
interruptions. - Categories of proactive assistance. - Temporary pauses. - 
Complete disabling of proactive notifications. 17.3 Decision quality Aster 
should not interrupt merely because it has detected something. Before producing 
a proactive notification, the system should evaluate relevance, confidence, 
urgency, interruption cost, and the user's preferences. The goal is to behave 
like a considerate companion rather than a source of constant notifications. 
--- 18. Non-Functional Requirements The following are mandatory engineering 
concerns. Area| Requirement Reliability| Recover from recoverable failures 
without corrupting sessions or profile data. Performance| Measure and optimize 
the complete multimodal processing pipeline. Scalability| Support growth in 
users, concurrent sessions, media throughput, and model workloads. 
Maintainability| Use modular components with clear interfaces and documented 
dependencies. Observability| Track system health, failures, latency, and 
processing gaps without unnecessarily collecting sensitive content. 
Accessibility| Provide accessible controls, readable status indicators, and 
appropriate interaction alternatives. Security| Enforce authorization and 
isolation in the backend. Privacy| Minimize collection and provide meaningful 
user controls. Portability| Maintain a consistent product experience across 
supported devices. Compatibility| Detect actual platform capabilities and adapt 
behavior accordingly. Data integrity| Preserve timestamps, event ordering, 
profile identity, and synchronization state. Honesty| Distinguish observed 
information, inferred information, unavailable capabilities, and completed 
actions. Numerical service-level objectives, supported operating-system 
versions, and production capacity targets must be established during technical 
planning. --- 19. Acceptance Criteria The following criteria define the minimum 
evidence needed to consider the corresponding requirements implemented. 19.1 
Profile management - A user can create no more than two companion profiles 
under one account. - Each profile has independently configurable identity and 
personality settings. - Each profile has independent conversation history and 
long-term memory. - The backend prevents unauthorized cross-profile memory 
access. - Explicitly shared information is identifiable and controlled. - Two 
different profiles cannot operate simultaneously on the same device. - The same 
profile can be used across multiple authorized devices. - Different profiles 
can be active on different devices at the same time. 19.2 Continuous awareness 
- The user can explicitly enable and disable supported awareness features. - 
The interface accurately indicates the awareness state. - Captured data is 
timestamped and associated with the correct session. - The system can maintain 
temporal context across successive observations. - Processing rates are 
measured rather than assumed. - Missing segments are detected where possible 
and disclosed accurately. - The system does not claim uninterrupted frame-level 
understanding without supporting evidence. 19.3 Offline continuity - Local 
history storage can be enabled or disabled. - Temporary data is handled 
according to defined storage limits. - Reconnection triggers appropriate retry 
and synchronization behavior. - The system resumes from available checkpoints. 
- Duplicate events are handled safely. - Missing data is not fabricated. - The 
user receives an accurate indication of degraded or interrupted operation. 19.4 
Permissions - The client detects the host platform. - Supported permissions can 
be managed individually. - Permission denial is handled gracefully. - 
Revocation is respected. - Awareness can be paused or stopped quickly. - The 
interface does not claim access to a capability that is unavailable. - Backend 
authorization prevents tools from exceeding the granted access. 19.5 Multimodal 
reasoning - Aster can use available visual context to resolve relevant 
conversational references. - Aster can combine relevant observations over time. 
- Aster can request additional information when context is insufficient. - The 
system distinguishes verified observations from uncertain inferences. - 
Performance is measured under realistic network and device conditions. --- 20. 
Delivery Strategy The product should be delivered in verified stages rather 
than attempting to implement every capability simultaneously. Stage 1 — 
Architectural foundation Establish: - Account and authentication services. - 
Companion profile isolation. - Session management. - Platform capability 
detection. - Permission management. - Secure transport. - Cloud infrastructure. 
- Observability and testing foundations. Stage 2 — Conversational AI Establish: 
- Multimodal model integration. - Language and reasoning orchestration. - 
Streaming conversational interaction. - Voice selection. - Initial memory 
functionality. - Profile-specific conversational context. Stage 3 — Screen and 
temporal understanding Establish: - Supported screen-capture mechanisms. - 
Timestamped visual ingestion. - Visual understanding. - Temporal event 
tracking. - Context reconstruction. - Continuity measurement. - Honest 
reporting of gaps. Stage 4 — Cross-device continuity Establish: - Device 
registration. - Same-profile multi-device sessions. - Session-state 
synchronization. - Conflict resolution. - Offline buffering. - Checkpointed 
recovery. - Profile switching and isolation. Stage 5 — Agentic actions and 
integrations Establish: - Permission-aware tool execution. - Supported Google 
integrations. - Photo and file search. - External application workflows. - 
Action verification. - Appropriate confirmation mechanisms. Stage 6 — 
Personalization and proactive assistance Establish: - Realistic customizable 
human avatar. - Extended personalization settings. - Optional consent-based 
voice cloning. - Proactive assistance. - Notification controls. - Advanced 
behavioral personalization. The stages are a proposed implementation order. 
They do not imply that the listed features have been implemented or that all 
platform capabilities are available. --- 21. Confirmed Decisions and 
Outstanding Questions 21.1 Confirmed product decisions ID| Decision| Status 
DEC-001| The product is intended to be a persistent, multimodal AI companion.| 
Confirmed DEC-002| Android and iOS are the primary mobile platforms.| Confirmed 
DEC-003| The product should support cross-device continuity, including 
laptops.| Confirmed DEC-004| The default AI companion name is Aster.| Confirmed 
DEC-005| The working product name is Aster Companion.| Working name; formal 
clearance pending DEC-006| The product combines advanced intelligence with a 
warm, friend-like personality.| Confirmed DEC-007| The avatar should be a 
realistic human character.| Confirmed DEC-008| Users should be able to 
personalize the avatar extensively.| Confirmed DEC-009| Users should have 
multiple voice choices.| Confirmed DEC-010| Voice cloning is optional.| 
Confirmed DEC-011| The architecture should be modular and combine specialized 
AI capabilities with reasoning and orchestration.| Confirmed direction DEC-012| 
Continuous screen understanding is a core product objective.| Confirmed 
objective; feasibility varies by platform DEC-013| Continuous environmental 
audio awareness should be supported where permitted.| Confirmed objective; 
feasibility varies by platform DEC-014| The primary AI reasoning and intensive 
multimodal processing should occur on servers.| Confirmed DEC-015| Offline 
behavior should preserve available state and attempt recovery.| Confirmed 
DEC-016| Frame-level continuity is a major engineering objective.| Confirmed 
objective; absolute continuity is not guaranteed DEC-017| The product should 
provide subtle, non-obstructive awareness indicators.| Confirmed DEC-018| The 
awareness indicator should open a compact control panel.| Confirmed DEC-019| 
Users should have granular permission controls.| Confirmed DEC-020| The product 
should support both local history storage and cloud synchronization.| 
Confirmed, with user controls DEC-021| One account can have no more than two 
companion profiles.| Confirmed DEC-022| The two profiles must have independent 
memories and personal context.| Confirmed DEC-023| Each profile should be 
independently named and personalized.| Confirmed DEC-024| The profiles should 
not automatically share information.| Confirmed DEC-025| The user may 
explicitly share selected information between profiles.| Confirmed DEC-026| Two 
different companion profiles cannot operate simultaneously on the same device.| 
Confirmed DEC-027| Different profiles may operate simultaneously on different 
devices under the same account.| Confirmed DEC-028| The same companion profile 
may be used across multiple authorized devices.| Confirmed DEC-029| Inactive 
profiles should stop operating on the device until reactivated.| Confirmed 
DEC-030| Google and other external integrations should be supported where 
authorized and technically available.| Confirmed direction DEC-031| UI design 
and onboarding are deferred until the architectural questions are sufficiently 
resolved.| Confirmed 21.2 Outstanding engineering questions These are 
unresolved implementation details, not requests to reopen already confirmed 
product decisions. 1. Which specific multimodal, reasoning, audio, and temporal 
models should be selected? 2. What server hardware and inference infrastructure 
can support the required throughput and latency? 3. What capture rates are 
achievable on each supported Android and iOS configuration? 4. How should the 
backend represent and reconstruct long-running visual sessions? 5. What 
buffering strategy can preserve the most useful information without exhausting 
device storage? 6. What are the exact retention periods for raw media, derived 
representations, transcripts, and memories? 7. Which Google integrations should 
be included in the first release? 8. Which actions require confirmation, and 
how should action risk be classified? 9. What are the initial supported 
operating-system versions? 10. What quantitative targets will define acceptable 
latency, continuity, availability, and cost? 11. What data-center regions, 
security controls, and service providers should be used? 12. How will optional 
voice cloning be implemented, licensed, and secured? 13. What happens when two 
devices submit conflicting actions to the same companion simultaneously? 14. 
What account recovery and profile deletion rules should apply? 15. What 
commercial model will fund the cloud processing requirements? These questions 
should be resolved through research, engineering experiments, security review, 
and explicit product decisions. --- 22. Definition of Product Success Aster 
Companion will be successful when it can reliably deliver the following 
experience: A user begins an activity on one device. Aster follows the relevant 
context when awareness is enabled and supported. The user can speak naturally, 
interrupt, ask questions, and request actions. Aster can combine relevant 
visual, auditory, linguistic, and historical information. It responds promptly, 
explains uncertainty, and respects permissions. The user can continue using the 
same companion on another authorized device without rebuilding its identity or 
losing appropriate context. If the user maintains two different companions, 
each remains independently personalized and private unless information is 
deliberately shared. If connectivity fails, Aster preserves what it can, 
resumes when possible, and reports missing information honestly. Above all, the 
product must earn trust through actual capability, predictable behavior, 
privacy, and reliable assistance.
The governing principle is simple: Aster should behave like a capable digital friend who understands the user's world, while remaining transparent about what it can see, remember, infer, and do.

