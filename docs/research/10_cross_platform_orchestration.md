# Aster Companion Research Dossier: Cross-Platform Orchestration, Multi-Device Sessions & State

**Domain Key**: `10_cross_platform_orchestration`  
**Generated**: November 2026  
**Total Queries Executed**: 20  

## Executive Findings & Architectural Directives

This document compiles verified engineering research for Cross-Platform Orchestration, Multi-Device Sessions & State in the Aster Companion ecosystem. These findings directly inform our Supabase backend, Android Compose client, iOS SwiftUI app, laptop web client, and multimodal AI pipelines.

---

## Query Inventory & Verified Evidence

### Q1: Active companion profile per device restriction enforcement distributed session lock

- **[Private active session lock | Incogniton Knowledge Hub](https://docs.incogniton.com/team-features/private-active-session-lock)** (Exa)
- **[How to use active session lock - Multilogin](https://multilogin.com/help/en_US/how-to-use-active-session-lock)** (Exa)
- **[Launch indication, parallel launch blocking and sessions in Dolphin {anty} - Dolphin {Anty}](https://docs.dolphin-anty.com/en/teamwork/profile-activity)** (Exa)
- **[Teamwork | Kameleo Developer Center](https://developer.kameleo.io/concepts/teamwork/)** (Exa)

### Q2: Cross-device session handover seamless transition from mobile phone to laptop client

- **[Creating Seamless Cross-Device Experiences with Windows | OD501](https://www.youtube.com/watch?v=YDeHGPk0zRc)** (Tavily)
  > "[10:59] We have provided the details to reach us directly at the end of this session. [11:03] Do stay with us as we move on to the next exciting section on Cross Device Resume. [11:08] Awesome. Now, let's imagine your users start a task on your phone, in your app, [11:16] like drafting a message, st"
- **[Multi-device AI session continuity: how cross-device conversation sync works](https://ably.com/blog/ai-session-continuity-cross-device-channel-based-architecture)** (Tavily)
  > "Deduplicating repeat work. The user can't tell whether the previous session completed, so they re-prompt. You pay for the same generation twice, and you need request-level idempotency to stop paying for it three times.  Reconciling conflicting state. A new prompt arrives from the phone while the lap"
- **[Create Seamless Cross-Device Experiences with Windows for your app | OD802](https://www.youtube.com/watch?v=e3ixnHI3z1k)** (Tavily)
  > "[16:18] It's a simple and seamless way to bring users back into the app right from where they left off. Here's simply how it works. [16:27] When you open the app on your mobile device or tablet, Windows can show a subtle badge right on your apps Taskbar item. [16:35] It's a visual nudge that when cl"

### Q3: WebSocket presence and channel multiplexing Supabase Realtime multi-device sync

- **[Presence](https://supabase.com/docs/guides/realtime/presence)** (Exa)
- **[Realtime Architecture](https://supabase.com/docs/guides/realtime/architecture)** (Exa)
- **[Realtime Protocol](https://supabase.com/docs/guides/realtime/protocol)** (Exa)
- **[Realtime Architecture](https://cdn.jsdelivr.net/gh/supabase/realtime@main/ARCHITECTURE.md)** (Exa)

### Q4: Handling simultaneous input from multiple devices under the same companion profile

- **[Companion device profiles  |  Android OS core topics  |  Android Open Source Project](https://source.android.com/docs/core/connect/companion-device-profile)** (Tavily)
  > "Companion device profile, introduced in Android 12, is a feature that allows companion apps to request a set of permissions specific to the type of the companion device, for example, a smartwatch. Using a companion device profile simplifies the enrollment process by allowing apps to display a single"
- **[Bitfocus - Companion](https://bitfocus.io/companion)** (Tavily)
  > "Button designer - Either with colored text or upload your own images  Feedback - Devices can give feedback to buttons to display state  Stacked actions - Run multiple actions from the same button  Delayed actions - Set delay time individually for each action  Multi device - Have multiple stream deck"
- **[The Stream Deck Hybrid - Using Companion with Elgato Software](https://www.youtube.com/watch?v=jakwSoXQ-aY)** (Tavily)
  > "[19:32] add all of your devices through here now I've got my two PTZ cameras that are set up here so I don't need to go in here we [19:39] got that all set up configuration is going to depend on what you have for cameras what you have for the software that you're using all that other good [19:48] st"

### Q5: Device registry schema unique device hardware ID platform push token metadata

- **[Device API | Pushwoosh Documentation](https://docs.pushwoosh.com/developer/api-reference/device-api/)** (Exa)
- **[Understanding device identifiers in Pushwoosh | Pushwoosh Documentation](https://docs.pushwoosh.com/developer/pushwoosh-knowledge-hub/device-identifiers/)** (Exa)
- **[Device Management | Zyphr Documentation](https://zyphr.dev/docs/features/devices)** (Exa)
- **[Devices API: Register Push Tokens | Espresso Notify Docs](https://docs.espressonotify.com/docs/api/devices)** (Exa)

### Q6: Graceful session suspension and resumption when user switches companion profiles

- **[session-recovery – Paseo plugin](https://paseo.sh/plugins/sm1ee/session-recovery)** (Tavily)
  > "Local Devin ACP sessions use the same Goal preview and Pause/Resume buttons when the optional companion for the verified Paseo 0.13.0 build is installed. Native state is read from the session's existing ACP connection. Pause cancels the current turn; Resume sends Devin's native /goal resume command"
- **[Manage sessions - Claude Code Docs](https://code.claude.com/docs/en/sessions)** (Tavily)
  > "| `/resume` | Switches to a different session from inside an active session | [...] A session is a saved conversation tied to a project directory. Claude Code stores it locally as you work, so you can resume where you left off, branch to try a different approach, or switch between tasks. The desktop"
- **[Graceful in Home Healthcare, LLC](https://www.mapquest.com/us/nebraska/graceful-in-home-healthcare-llc-534405216)** (Tavily)
  > "Advertisement  Advertisement  2755 Jamie Ln, #1, Lincoln, NE, 68516-7750  Graceful in Home Healthcare, LLC, located in Lincoln, NE, offers a wide range of in-home caregiving services tailored to meet individual needs. Their offerings include personal care, companion care, senior care, and specialize"

### Q7: Preventing conversational context leakage between Profile A and Profile B during switch

- **[fix(desktop): restore active chat across profile switches](https://github.com/NousResearch/hermes-agent/pull/96708)** (Exa)
- **[[Bug]: Desktop cross-profile prompt leak: one profile backend resumes and writes another profile's session](https://github.com/NousResearch/hermes-agent/issues/85294)** (Exa)
- **[feat(desktop): restore the last selected session when switching profiles](https://github.com/NousResearch/hermes-agent/issues/77952)** (Exa)
- **[Profile切换后session历史未隔离 — default profile的会话泄漏到named profile](https://github.com/NousResearch/hermes-agent/issues/29220)** (Exa)

### Q8: Laptop desktop client architecture React 18 Vite WebRTC screen share audio capture

- **[Rethinking Elevator safety with Embedded WebRTC](https://www.samvyo.com/blog/enhancing-elevator-safety-with-webrtc)** (Tavily)
  > "✔ Custom WebRTC Build: Compiled WebRTC libraries optimized for embedded hardware.   ✔ C++ Application: Built using RTC peer connection for establishing seamless video calls.   ✔ Media Capture: Developed browser-equivalent getUserMedia functionality for accessing cameras and microphones.   ✔ Efficien"
- **[Top 10 Screen Capture Software Tools in 2026 for Better Snapshots](https://www.softwaretestinghelp.com/best-screen-capture-software)** (Tavily)
  > "=> Visit Aiseesoft Screen Recorder Website  ### #5) Screen Recorder  CyberLink Screen Recorder 4 is a desktop capture and video streaming platform for Windows platforms. It can be used for game streaming, screen recording, and video editing.  It contains the features of PowerDirector and makes it ea"
- **[Take a Screen Capture on a Windows or Mac Computer](https://services.nvcc.edu/TDClient/413/Portal/KB/Article/24126/Take-a-Screen-Capture-on-a-Windows-or-Mac-Computer)** (Tavily)
  > "## Overview  This article details the steps to take a screen capture on a Windows or Mac computer.  ##  (PRNT SCN).  2.   Press and hold the Print Screen key to take a full screen capture and save it the Windows clipboard.  3.   Press the Alt + Print Screen keys to capture only the selected, active"

### Q9: Cross-platform state management Zustand vs Redux Toolkit offline persistence web

- **[Deeper Dive into State Management in React & React Native with TypeScript (2025 Edition) - DEV Community](https://dev.to/serifcolakel/deeper-dive-into-state-management-in-react-react-native-with-typescript-2025-edition-447)** (Exa)
- **[Sharing State Across Packages and Apps in a React Monorepo (Web + Mobile) - DEV Community](https://dev.to/abdalla_emad_335fff40f342/sharing-state-across-packages-and-apps-in-a-react-monorepo-web-mobile-4gak)** (Exa)
- **[Comparison - Zustand Docs](https://zustand.docs.pmnd.rs/learn/getting-started/comparison.html)** (Exa)
- **[Zustand vs Redux: notes from a 35-store production app](https://boopr.com/blog/zustand-vs-redux)** (Exa)

### Q10: Native Android Kotlin Coroutines Flow StateFlow UI state management MVVM pattern

- **[ViewModel State Management in Android with Kotlin](https://androidacademic.blogspot.com/2024/03/viewmodel-state-management.html)** (Tavily)
  > "Coroutine-based reactive stream — best for complex state with Kotlin coroutines  StateFlow is the modern, Kotlin-first alternative to LiveData. It integrates natively with Kotlin coroutines, supports backpressure handling, and works well with Jetpack Compose. It always holds a value and emits update"
- **[StateFlow in Kotlin: Complete Guide to Observable State Management for Android UI](https://www.youtube.com/watch?v=rnRsUiI3W9o)** (Tavily)
  > "💡 Perfect for Android developers who want to build reactive, maintainable applications using modern Kotlin Coroutines patterns. Whether you're a beginner or looking to strengthen your understanding of state management, this tutorial provides clear explanations and practical examples.  🎯 StateFlow is"
- **[Android Handbook | Project architecture / MVVM](https://infinum.com/handbook/android/project-architecture/mvvm)** (Tavily)
  > "Since Kotlin Coroutines introduced StateFlow and SharedFLow, these types have opened the opportunity for substituting LiveData and they are becoming the go-to types for handling states and events. Additionally, they also solve the problems which appear when using pure Flows for this purpose (pure Fl"

### Q11: iOS SwiftUI Observation framework @Observable StateObject async await concurrency

- **[Discover Observation in SwiftUI - WWDC23 - Videos - Apple Developer](https://developer.apple.com/videos/play/wwdc2023/10149/)** (Exa)
- **[proposals/0475-observed.md](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0475-observed.md)** (Exa)
- **[Observation and MainActor - Forums](https://developer.apple.com/forums/thread/731822)** (Exa)
- **[Discover concurrency in SwiftUI - WWDC21 - Videos - Apple Developer](https://developer.apple.com/videos/play/wwdc2021/10019/)** (Exa)

### Q12: Unified API client contracts TypeScript and Kotlin data transfer objects parity

- **[Gable Blog | How Data Transfer Objects (DTOs) Shape Reliable APIs](https://www.gable.ai/blog/data-transfer-objects)** (Tavily)
  > "Gable helps this effort by allowing engineers to adopt data contracts into their workflows through a unified platform for authoring, enforcing, and validating them. It detects data objects in code and maps which services produce and consume them. Further, by defining data contracts alongside the sou"
- **[Pros and Cons of Data Transfer Objects | Microsoft Learn](https://learn.microsoft.com/en-us/archive/msdn-magazine/2009/brownfield/pros-and-cons-of-data-transfer-objects)** (Tavily)
  > "It turns out that a mixed approach that uses data contracts only when using classes is not possible, is often the more acceptable solution. But as an architect, you must not make this decision lightly. Violating good design rules is allowed, as long as you know what you're doing.  Send your question"
- **[Embrace Contributes Its Kotlin Implementation and SDK to OpenTelemetry](https://finance.yahoo.com/sectors/technology/articles/embrace-contributes-kotlin-implementation-sdk-070000671.html)** (Tavily)
  > ""The real power of OpenTelemetry is the standard itself – a shared contract that allows many implementations to evolve and serve different environments," said Jamie Lynch, Senior Software Engineer at Embrace and a Maintainer of the OpenTelemetry Kotlin project. "By contributing a Kotlin Multiplatfor"

### Q13: Shared validation schemas Zod TypeScript parity with Kotlin data classes

- **[zodable — Nathan Fallet](https://www.nathanfallet.me/projects/zodable)** (Exa)
- **[Zodable: Generate Zod and Pydantic Schemas from Kotlin Classes for Seamless Backend-Frontend Integration](https://discuss.kotlinlang.org/t/zodable-generate-zod-and-pydantic-schemas-from-kotlin-classes-for-seamless-backend-frontend-integration/30170)** (Exa)
- **[zodable/zodable](https://github.com/zodable/zodable)** (Exa)
- **[jagatsingh/schema-gen](https://github.com/jagatsingh/schema-gen)** (Exa)

### Q14: Handling clock skew and out-of-order packet arrival in cross-device timeline sync

- **[Clock Synchronization in Wireless Sensor Networks: An Overview](https://pmc.ncbi.nlm.nih.gov/articles/PMC3280734)** (Tavily)
  > "By using standard results from estimation theory [28, Theorem 3.2, p. 44] and making some mathematical manipulations, the minimum variance unbiased (MVU) estimator for the relative clock offset and skew takes the expression : where Di = T1,i − T1,1. In case that there is no relative clock skew ( θS("
- **[Dealing with Clock Skew and Time Sync - System Design Interview Guide | bugfree.ai](https://www.bugfree.ai/knowledge-hub/dealing-with-clock-skew-and-time-sync-in-multi-region-systems)** (Tavily)
  > "To mitigate the issues caused by clock skew, consider the following strategies:  ### 1. Use Network Time Protocol (NTP)  Implementing NTP is one of the most effective ways to synchronize clocks across distributed systems. NTP can help ensure that all nodes maintain a consistent time reference, reduc"
- **[Clock synchronization in a network with asymmetric delays](https://cs.stackexchange.com/questions/103/clock-synchronization-in-a-network-with-asymmetric-delays)** (Tavily)
  > "You can create more cases by 'grabbing' the PC timeline and 'sliding' it, holding the message send/receive points fixed relative to their respective timelines. The asymmetries you cause are exactly negated by the clock offset. In fact, you can even make messages go BACKWARDS IN TIME one way (as long"

### Q15: Remote device session revocation terminating compromised laptop or phone access

- **[Revoke user access in an emergency in Microsoft Entra ID - Microsoft Entra ID | Microsoft Learn](https://learn.microsoft.com/en-us/entra/identity/users/users-revoke-access)** (Exa)
- **[Managing Concurrent Sessions and Multi-Device Logins | Session Management](https://cyunified.com/learn/cybersecurity/web-application-security/session-management/managing-concurrent-sessions-and-multi-device-logins)** (Exa)
- **[Terminate active sessions and add users/machines to the block list | Advanced Secure Private Access features | Citrix](https://docs.citrix.com/us/en/citrix-secure-private-access/service/advanced-spa-features/terminate-active-user-sessions-block-users.html)** (Exa)
- **[About session revocation](https://help.ivanti.com/mi/help/en_us/ACC/46/gd/Content/AccessGuide/About_session_revocation.htm)** (Exa)

### Q16: Push notification routing notifying only active devices or suppressing active device

- **[Push notifications: frequently asked questions - Customer.io Documentation](https://docs.customer.io/messaging/channels/push/faq)** (Tavily)
  > "iOS devices only report delivery when a user has opted into notifications and a push notification appears to the user (whether in the notification tray, lock screen, etc). But Android reports the delivery of notifications regardless of opt-in status. This means that a message might report that it wa"
- **[Notification Hubs - Active devices vs max devices - Microsoft Q&A](https://learn.microsoft.com/en-us/answers/questions/305507/notification-hubs-active-devices-vs-max-devices)** (Tavily)
  > "Thanks for asking question! If I have understood right you are using free tier. You may want to know that Active devices are devices eligible to receive notifications. They are defined as unique registration IDs for devices using Google Cloud Messaging or Amazon Device Messaging, channel uniform res"
- **[What Are Push Notifications? Meaning, Examples and How They Work](https://messageflow.com/blog/what-are-push-notifications-how-they-work)** (Tavily)
  > "Push notifications are short messages (usually one or two sentences, often including a call-to-action button) that appear on a phone or computer screen – regardless of whether the user is actively using the device or even if the screen is locked.  Their key characteristic is that they are a “push” f"

### Q17: Audit logging of cross-device operations timestamp device_id profile_id action

- **[Get device config history](https://roscolive-api-v1.apidog.io/33219987e0)** (Exa)
- **[Guide how to import data into OpenPanel](https://gist.github.com/lindesvard/1f2e8e22198e1ff98e7300be26880865)** (Exa)
- **[Audit events](https://www.canva.dev/docs/audit-logs/audit-events/)** (Exa)
- **[docs/production/audit-events.md](https://github.com/GnomesOfZurich/axess/blob/main/docs/production/audit-events.md)** (Exa)

### Q18: Continuous deployment pipeline for multi-platform Android iOS Web Supabase backend

- **[Deployment & Branching | Supabase Docs](https://supabase.com/docs/guides/deployment)** (Tavily)
  > "1. Develop locally using the Supabase CLI 2. Push changes to your GitHub repository 3. Deploy automatically to your Supabase project from your `main` branch  This workflow works on all plans and does not require branching.  If you have branching enabled (on the Pro Plan), you can extend this workflo"
- **[What is mobile CI/CD? CI/CD for iOS and Android | Bitrise](https://bitrise.io/guides/mobile-cicd)** (Tavily)
  > "The continuous integration part of CI/CD means developers merge code into a shared branch frequently (at least daily), and every merge triggers an automated build and test run. The continuous delivery part means the pipeline can produce a signed, tested binary ready for release at any point, without"
- **[Supabase | The Postgres Development Platform](https://supabase.com)** (Tavily)
  > "Supabase Authentication user db rows Supabase Authentication user db rows Supabase Authentication user db rows Supabase Authentication user db rows  ## Edge Functions  Easily write custom code    without deploying or scaling servers.  Supabase Edge Functions globe Supabase Edge Functions globe  ## S"

### Q19: End to end integration testing cross-device synchronization Playwright and Appium

- **[quinncess18/generalstore-mobile-framework](https://github.com/quinncess18/generalstore-mobile-framework)** (Exa)
- **[quinncess18/taqelah-mobile-automation](https://github.com/quinncess18/taqelah-mobile-automation)** (Exa)
- **[Playwright Automated Testing in Docker with Appium for CI/CD](https://www.royalcyber.com/blogs/test-automation/playwright-automated-testing-in-docker-with-appium/)** (Exa)
- **[Appium and Playwright for Mobile Testing | BrowserStack](https://www.browserstack.com/guide/playwright-appium)** (Exa)

### Q20: Production observability OpenTelemetry distributed tracing Prometheus metrics SLOs

- **[Prometheus Distributed Tracing: An Easy-to-Follow Guide for Engineers | Last9](https://last9.io/blog/prometheus-distributed-tracing)** (Tavily)
  > "By integrating with OpenTelemetry and Prometheus, Last9 unifies metrics, logs, and traces to optimize performance, cost, and real-time insights with correlated monitoring and alerting.  Talk to us to know more about our platform capabilities!  💡  And if you’d like to discuss anything further about P"
- **[Observability for Developers: OpenTelemetry, Distributed Tracing, and Modern Monitoring | daily.dev](https://daily.dev/blog/observability-developers-opentelemetry-distributed-tracing-monitoring)** (Tavily)
  > "Custom metrics, such as SLIs, SLOs, and error budgets, bring a user-focused lens to service reliability. While traditional metrics like CPU usage or memory consumption reveal system performance, they often miss the mark when it comes to user experience. SLIs (Service Level Indicators) measure servic"
- **[Software Engineer – OpenTelemetry and Hyperledger Besu Integration - Ridgeville, SC - Indeed.com](https://www.indeed.com/viewjob?jk=9cd480f9d8006f1d)** (Tavily)
  > "Design, implement, and maintain OpenTelemetry-based observability solutions to provide distributed tracing, metrics, and logging for communication platforms.  Integrate OpenTelemetry SDKs and APIs with microservices and existing communication workflows.  Configure and optimize backends (e.g., Jaeger"

