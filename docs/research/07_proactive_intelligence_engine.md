# Aster Companion Research Dossier: Proactive Intelligence, Urgency Modeling & Push Notifications

**Domain Key**: `07_proactive_intelligence_engine`  
**Generated**: November 2026  
**Total Queries Executed**: 20  

## Executive Findings & Architectural Directives

This document compiles verified engineering research for Proactive Intelligence, Urgency Modeling & Push Notifications in the Aster Companion ecosystem. These findings directly inform our Supabase backend, Android Compose client, iOS SwiftUI app, laptop web client, and multimodal AI pipelines.

---

## Query Inventory & Verified Evidence

### Q1: Proactive AI assistant interruption cost cognitive load modeling research papers

- **[Leveraging Changes in Mental Workload during Task Execution to Mitigate Effects of Interruption](http://hdl.handle.net/2142/11088)** (Exa)
- **[TimelyAI: When Should Generative AI Assistants Intervene?](https://dl.acm.org/doi/pdf/10.1145/3805029.3818270)** (Exa)
- **[Assistance or Disruption? Exploring and Evaluating the Design and Trade-offs of Proactive AI Programming Support](https://arxiv.org/html/2502.18658)** (Exa)
- **[Using LLMs to Model Notification Timing from Context-Sensitive Features](https://dl.acm.org/doi/pdf/10.1145/3795011.3795067?download=)** (Exa)

### Q2: Notification scoring formula relevance times confidence times urgency minus cost

- **[10 App Push Notification Metrics That Prove ROI](https://www.sashido.io/en/blog/application-push-notification-metrics-improve-roi)** (Tavily)
  > "This is the metric most affected by timing and preview relevance. And it can move dramatically when you shift from generic blasts to contextual triggers.  You will often see a misleading interpretation here. People assume low open rate means bad copy. In practice, low open rate often means the user"
- **[How timing and messaging drive engagement | Customer.io](https://customer.io/learn/mobile-marketing/push-notification-psychology)** (Tavily)
  > "Effective push notification psychology prioritizes relevance and consistency over urgency and novelty.  ## Push notification timing and the science of context  Timing determines whether a push notification feels like help or noise.  ### Why is there no universal best time to send?  Aggregate benchma"
- **[Notification Design Psychology: When Alerts Help and When They Annoy](https://medium.com/@atticusli/notification-design-psychology-when-alerts-help-and-when-they-annoy-1f8be3e0956c)** (Tavily)
  > "Tier 1: Immediate action required. Security alerts, payment failures, time-critical deadlines. These warrant push notifications with sound and vibration. They should represent less than 5% of all notifications.  Tier 2: Timely but not urgent. New messages, completed tasks, status changes. These warr"

### Q3: Contextual quiet hours user sleeping working schedule adaptive silence rules

- **[KIMYA - Smart, Context-Aware Silence](https://kimyaapp.com/)** (Exa)
- **[How Quietly works: routines, blocks and passes](https://usequietly.app/how-it-works)** (Exa)
- **[How To Create An Ai Voice Assistant That Respects Quiet Hours And Never Interrupts Sleep Mode](https://www.alibaba.com/product-insights/how-to-create-an-ai-voice-assistant-that-respects-quiet-hours-and-never-interrupts-sleep-mode.html)** (Exa)
- **[Quiet hours | Herald docs](https://forge.mograph.life/apps/herald/docs/concepts/quiet-hours)** (Exa)

### Q4: Notification fatigue prevention algorithms exponential backoff on user dismissals

- **[Exponential backoff - Wikipedia](https://en.wikipedia.org/wiki/Exponential_backoff)** (Tavily)
  > "A Heuristic RCP algorithm consists of the following steps: (1) Let m denote the number of previous collisions incurred by a packet at a user as the feedback information in its control loop. For a new packet, K(0) is initialized to 1. (2) The packet’s retransmission interval K(m) increases as m incre"
- **[What Is Exponential Backoff? Retry Patterns Explained | Kestra](https://kestra.io/resources/infrastructure/exponential-backoff)** (Tavily)
  > "At its core, exponential backoff is an algorithm that uses feedback—specifically, the failure of a request—to multiplicatively decrease the rate at which it retries. This gives a struggling system breathing room to recover.  ### Understanding the Core Mechanism  The mechanism is straightforward: [.."
- **[Managing Network Traffic with Exponential Backoff Method | Lenovo US](https://www.lenovo.com/us/en/glossary/exponential-backoff)** (Tavily)
  > "Exponential backoff is a network protocol method that is used to manage and space out repeated requests for a network resource. When you meet a network failure or data congestion, exponential backoff algorithmically increases the wait time between each retry attempt to reduce the load on the network"

### Q5: Firebase Cloud Messaging FCM v1 HTTP API payload format Android push notifications

- **[Send a message using FCM HTTP v1 API - Firebase - Google](https://firebase.google.com/docs/cloud-messaging/send/v1-api)** (Exa)
- **[REST Resource: projects.messages  |  Firebase Cloud Messaging REST API](https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages)** (Exa)
- **[Migrate from legacy FCM APIs to HTTP v1 

    
    
       
    

     
      
      Stay organized with collections
     
     
      
      Save and categorize content based on your preferences.](https://firebase.google.com/docs/cloud-messaging/migrate-v1)** (Exa)
- **[Build app server send requests](https://firebase.google.com/docs/cloud-messaging/send-message)** (Exa)

### Q6: Apple Push Notification service APNs HTTP/2 token based authentication payload

- **[Apns | APIs.io APIs](https://apis.io/apis/ios/apns)** (Tavily)
  > "# Apple Push Notification Service (APNs)  The Apple Push Notification service (APNs) is the HTTP/2 + JSON push delivery surface for sending remote notifications, background updates, VoIP pushes, and Live Activity updates to iOS, iPadOS, watchOS, tvOS and macOS devices. Providers authenticate either"
- **[GitHub - sideshow/apns2: ⚡ HTTP/2 Apple Push Notification Service (APNs) push provider for Go — Send push notifications to iOS, tvOS, Safari and OSX apps, using the APNs HTTP/2 protocol. · GitHub](https://github.com/sideshow/apns2)** (Tavily)
  > "You can use one APNs signing key to authenticate tokens for multiple apps.  A signing key works for both the development and production environments.  A signing key doesn’t expire but can be revoked.  ## Notification  At a minimum, a Notification needs a DeviceToken, a Topic and a Payload.  ``` noti"
- **[Establishing a connection to Apple Push Notification service (APNs) | Apple Developer Documentation](https://developer.apple.com/documentation/usernotifications/establishing-a-connection-to-apns)** (Tavily)
  > "If you’re using device push, the device token that identifies the device to receive the notification; refer to Registering your app with APNs.  If you’re using token-based authentication, your current authentication token; refer to Establishing a token-based connection to APNs.  The notification’s p"

### Q7: Interactive push notifications actionable buttons Snooze Confirm Dismiss mobile

- **[Action buttons for push notifications - OneSignal](https://documentation.onesignal.com/docs/en/action-buttons)** (Exa)
- **[Declaring your actionable notification types](https://developer.apple.com/documentation/usernotifications/declaring-your-actionable-notification-types)** (Exa)
- **[Create a notification | Jetpack Compose](https://developer.android.com/develop/ui/compose/notifications/create-notification)** (Exa)
- **[Expo Notifications](https://docs.expo.dev/versions/latest/sdk/notifications)** (Exa)

### Q8: Linking proactive notifications to source evidence citation transparency AI companion

- **[Employ Introduces AI Screening Companion to Help Recruiters Identify Best-Fit Talent Faster, Fairer and With Greater Transparency](https://finance.yahoo.com/news/employ-introduces-ai-screening-companion-140000701.html)** (Tavily)
  > "Employ Inc.     Backed by responsible AI governance, the new companion proactively matches candidates to jobs, monitors engagement, and automatically delivers feedback, strengthening employer brand and candidate experience in real time [...] Built using IBM watsonx.governance, the AI Screening Compa"
- **[Transparency & Attribution: Citing AI Tools - Artificial Intelligence - Library at University of Calgary](https://libguides.ucalgary.ca/c.php?g=733971&p=5302331)** (Tavily)
  > "Transparency is one of the most important considerations when using AI tools for academic work. Most generative AI systems are trained on massive datasets that draw from a wide range of sources, but these sources are not disclosed to the user. Without clear information about where the AI is pulling"
- **[Transparency and Citation of AI - Artificial Intelligence - Research Guides at Salve Regina University](https://salve.libguides.com/AI/citation-transparency)** (Tavily)
  > "AI Transparency Statements are a good first step towards ethical use of AI. These are short statements in a document that share whether AI was used and how. They can include the tools used and links to prompts, which are akin to "methods" in a research study and help a viewer/reader understand your"

### Q9: User configurable proactive categories health calendar reminders social suggestions

- **[Features - Veil](https://veiltrack.app/features)** (Exa)
- **[Mio — Your Personal AI Agent](https://mio.fyi/)** (Exa)
- **[A-LIST - Make Health Easy](https://a-list.com/)** (Exa)
- **[Free Reminder App — Push, Email, WhatsApp & Telegram | ReminderPro](https://reminderpro.app/)** (Exa)

### Q10: On-device temporal trigger scheduling AlarmManager exact alarms Android 14 requirements

- **[Schedule alarms  |  Background work  |  Android Developers](https://developer.android.com/develop/background-work/services/alarms)** (Tavily)
  > "`SCHEDULE_EXACT_ALARM`  The `SCHEDULE_EXACT_ALARM` permission is not pre-granted to fresh installs of apps targeting Android 13 (API level 33) and higher. If a user transfers app data to a device running Android 14 through a backup-and-restore operation, the `SCHEDULE_EXACT_ALARM` permission will be"
- **[Schedule exact alarms are denied by default  |  Android Developers](https://developer.android.com/about/versions/14/changes/schedule-exact-alarms)** (Tavily)
  > "`SCHEDULE_EXACT_ALARM` `canScheduleExactAlarms()` `AlarmManager.ACTION_SCHEDULE_EXACT_ALARM_PERMISSION_STATE_CHANGED`  ## Affected apps  If a device is running Android 14 or higher, this change will affect a newly installed app that has the following characteristics:  `SCHEDULE_EXACT_ALARM`  ## Cale"
- **[android 13 scheduled alarms vs exact alarms · Issue #1906 · MaikuB/flutter_local_notifications · GitHub](https://github.com/MaikuB/flutter_local_notifications/issues/1906)** (Tavily)
  > "@timobaehr your issue isn't directly (emphasis on directly) related to what was raised by @hichaudh. The point raised by @hichaudh is around how to handle behavioural changes in Android 14. What you're seeing isn't a device-specific either that trying to reproduce this on different devices won't hel"

### Q11: UNUserNotificationCenter local notifications iOS scheduling based on context

- **[Scheduling a notification locally from your app](https://developer.apple.com/documentation/usernotifications/scheduling-a-notification-locally-from-your-app)** (Exa)
- **[UNUserNotificationCenter](https://developer.apple.com/documentation/usernotifications/unusernotificationcenter.md)** (Exa)
- **[Scheduling a notification locally from your app](https://developer.apple.com/documentation/usernotifications/scheduling-a-notification-locally-from-your-app.md)** (Exa)
- **[Implementing a local notification scheduler in Todoist iOS](https://www.doist.dev/implementing-a-local-notification-scheduler-in-todoist-ios/)** (Exa)

### Q12: Proactive suggestion deduplication preventing repeated notifications across devices

- **[Building a Deduplicated Notification System: A Generic Guide for Production Backends](https://www.linkedin.com/pulse/building-deduplicated-notification-system-generic-guide-adegun-mmipf)** (Tavily)
  > "Channel-level deduplication prevents the same notification from being delivered to the same device or address twice. This catches queue retries, concurrent workers, and provider-level retries.  Device-level rate limiting prevents individual recipients from being flooded. This respects provider quota"
- **[How to Build Alert Deduplication Logic](https://oneuptime.com/blog/post/2026-01-30-alert-deduplication/view)** (Tavily)
  > "Learn how to implement alert deduplication to prevent duplicate notifications for the same issue.  Nawaz Dhandala  By @nawazdhandala  • Jan 30, 2026 •  Reading time  Observability   Alerting   Incident Management   SRE  ## On this page [...] 1. Generate a fingerprint from incoming alert attributes 2"
- **[Duplicated notifications - OneSignal](https://documentation.onesignal.com/docs/en/duplicated-notifications)** (Tavily)
  > "foreground handler`})]}),`\n`,\_jsxs(\_components.li,{children:[`You only see duplicates on dev builds or with multiple installs → `,\_jsx(\_components.a,{href:`#multiple-app-instances`,children:`Multiple app instances`})]}),`\n`,\_jsxs(\_components.li,{children:[`Old, previously delivered notificat"

### Q13: Evaluating false positive rate and annoyance score in proactive digital assistants

- **[overji/ProVoice-Bench · Datasets at Hugging Face](https://huggingface.co/datasets/overji/ProVoice-Bench)** (Exa)
- **[ProAgentBench: Evaluating LLM Agents for Proactive Assistance with Real-World Data](https://arxiv.org/html/2602.04482v2)** (Exa)
- **[Sensing What Surveys Miss: Understanding and Personalizing Proactive LLM Support by User Modeling](https://arxiv.org/html/2602.00880v1)** (Exa)
- **[After Talking with 1,000 Personas: Learning Preference-Aligned Proactive Assistants From Large-Scale Persona Interactions](https://arxiv.org/html/2602.04000v1)** (Exa)

### Q14: Context-aware snooze durations 15 min 1 hour this evening tomorrow morning

- **[Snooze alarm use in a global population of smartphone users](https://pmc.ncbi.nlm.nih.gov/articles/PMC12089427)** (Tavily)
  > "in the scientific literature on snooze alarm use. One of the primary contributions of our study is a global sample of smartphone users. Previous studies examining snooze alarm behavior have included populations with limited generalizability, such as an online convenience sample or groups of employed"
- **[Adjust the snooze duration in Clock on iPhone or iPad | Apple Support](https://www.youtube.com/shorts/ZR9anxNzHYI)** (Tavily)
  > "### Transcript [0:00] ♪ [0:02] [ALARM TONE] [0:04] Need just a few more minutes before getting up in the morning? [0:08] You can adjust the snooze duration for alarms in the Clock app starting in iOS 26. [0:15] In the Alarms tab, tap one of your alarms. [0:19] Now, tap Snooze Duration and choose a t"
- **[Daylight Saving Time 2026 Dates | The Old Farmer's Almanac](https://www.almanac.com/content/when-daylight-saving-time)** (Tavily)
  > "The time changes at 2:00 A.M., when most people are asleep. Consider changing your clocks before bed on Saturday, October 31, to avoid confusion in the morning!  ## When Does Daylight Saving Time Start in 2026?  Daylight Saving Time begins on Sunday, March 8, 2026, at 2:00 A.M. local time. The clock"

### Q15: Low-power background context evaluation heuristics minimizing battery impact

- **[CAS: Context-Aware Background Application Scheduling in Interactive Mobile Systems](https://doi.org/10.1109/jsac.2017.2676918)** (Exa)
- **[The latency, accuracy, and battery (LAB) abstraction: programmer productivity and energy efficiency for continuous mobile context sensing: ACM SIGPLAN Notices: Vol 48, No 10](https://dl.acm.org/doi/10.1145/2544173.2509541)** (Exa)
- **[Exclusive Contexts Resolver: A Low-Power Sensing Management System for Sustainable Context-Awareness in Exclusive Contexts](https://www.mdpi.com/2071-1050/9/4/647)** (Exa)
- **[gnuplot plot](https://www.sigmobile.org/mobicom/2015/papers/p40-chenA.pdf)** (Exa)

### Q16: Proactive morning briefing and evening debriefing synthesis prompt engineering

- **[Proactive AI Morning Briefings: amaiko vs Copilot Cowork | amaiko](https://amaiko.ai/blog/proactive-ai-morning-briefing)** (Tavily)
  > "When migrating to amaiko, such recurring prompts are translated into proactive processes. “Summarize my most important emails every morning” becomes Active Inbox. “What’s on the agenda today?” becomes Morning Briefing. “Write the follow-up email” becomes Meeting Recall with a draft. [...] Many compa"
- **[Prompt Engineering - AI Tools and Resources - LibGuides at University of South Florida Libraries](https://guides.lib.usf.edu/AI/promptengineering)** (Tavily)
  > "# Prompt Engineering  Prompt engineering is the practice of intentionally designing instructions for generative AI tools so they produce clearer, more accurate, and more useful results. In academic work, how a prompt is written can significantly affect relevance, transparency, and reliability.  Look"
- **[Prompt Engineering: The Art of Getting What You Need From Generative AI | Ivan Allen College of Liberal Arts](https://iac.gatech.edu/featured-news/2024/02/AI-prompt-engineering-ChatGPT)** (Tavily)
  > "Prompt engineering is the process of crafting and refining a specific, detailed prompt — one that will get you the response you need from a generative AI model. This kind of “coding in English” is a complex and tricky process. Fortunately, our faculty at the Ivan Allen College of Liberal Arts at Geo"

### Q17: Serverless event-driven architecture for proactive reminder triggers Celery Cron PG_Cron

- **[Serverless Scheduling with Amazon EventBridge, AWS Lambda, and Amazon DynamoDB | AWS Architecture Blog](https://aws.amazon.com/blogs/architecture/serverless-scheduling-with-amazon-eventbridge-aws-lambda-and-amazon-dynamodb/)** (Exa)
- **[Implement event-driven architectures with Amazon DynamoDB – Part 3 | AWS Database Blog](https://aws.amazon.com/blogs/database/implement-event-driven-architectures-with-amazon-dynamodb-part-3/)** (Exa)
- **[juspay/kronos](https://github.com/juspay/kronos)** (Exa)
- **[docs/serverless.md](https://github.com/ahmedrowaihi/iterativeflow/blob/main/docs/serverless.md)** (Exa)

### Q18: Observing user response to proactive alerts reinforcement feedback loop weighting

- **[What are Feedback Loops? — updated 2026 | IxDF](https://ixdf.org/literature/topics/feedback-loops)** (Tavily)
  > "Positive feedback loops reinforce user behavior, like showing rewards after task completion. Negative loops highlight errors and suggest corrections, helping users recover. For example, progress indicators, confirmation messages, or error alerts are all types of feedback that shape the user experien"
- **[User Feedback Loop: How to Close It Effectively | Mouseflow](https://mouseflow.com/blog/user-feedback-loop)** (Tavily)
  > "A user feedback loop is the continuous process of collecting feedback, analyzing it, acting on it, and validating whether the changes actually improved the user experience. It turns feedback from passive information into an active optimization system. [...] When implemented effectively, a user feedb"
- **[AI Feedback Loop: How It Works, Examples & Best Practices | IrisAgent](https://irisagent.com/blog/the-power-of-feedback-loops-in-ai-learning-from-mistakes)** (Tavily)
  > "A feedback loop that only learns from tickets it already received is still reactive. The same signals, scored before a customer writes in, are what AI proactive customer service runs on.  ## Feedback Loops in Customer Support  Customer support Feedback loop [...] AI feedback loops operate through a"

### Q19: Emergency alert vs polite suggestion UI hierarchy styling distinctions

- **[Alert | NICE Design System](https://design-system.nice.org.uk/components/alert/)** (Exa)
- **[Alert - Design | GC Design System](https://design-system.canada.ca/en/components/alert/design/)** (Exa)
- **[Alert | U.S. Web Design System (USWDS)](https://designsystem.digital.gov/components/alert/)** (Exa)
- **[2.2.4 Interruptions | a11ybot](https://a11ybot.app/learn/2-2-4-interruptions/)** (Exa)

### Q20: Respecting system Do Not Disturb and Focus modes Android iOS notification channels

- **[How to put WhatsApp on do not disturb? - California Learning Resource Network](https://www.clrn.org/how-to-put-whatsapp-on-do-not-disturb)** (Tavily)
  > "Effectively managing WhatsApp notifications through Do Not Disturb and Focus modes is essential for maintaining productivity and focus in a digitally saturated world. By understanding the underlying mechanisms and leveraging the granular configuration options available on both Android and iOS, users"
- **[Limit interruptions with Modes & Do Not Disturb on Android - Android Help](https://support.google.com/android/answer/9069335?hl=en)** (Tavily)
  > "1. Open your device's Settings app. 2. Tap Modes and thenselect a modeand then More settings and then Display settings and then Display options for filtered notifications. 3. Choose what to block or allow.  At certain times  Important: Settings can vary by phone. For more info, contact your device m"
- **[How to turn Do Not Disturb on or off on your iPhone - Apple Support](https://support.apple.com/en-us/105112)** (Tavily)
  > "On iPhone X and later, and iPad, swipe down from the top-right corner of your screen.     On iPhone SE, and iPhone 8 and earlier, swipe up from the bottom edge of your screen. 2. Tap and hold the button showing either Focus, Do Not Disturb, or another Focus option (Personal, Work, Sleep, Reduce Inte"

