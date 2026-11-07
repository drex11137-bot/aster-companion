# Aster Companion Research Dossier: Continuous Screen Awareness & Temporal Visual Ingestion

**Domain Key**: `02_screen_awareness_android_ios`  
**Generated**: November 2026  
**Total Queries Executed**: 20  

## Executive Findings & Architectural Directives

This document compiles verified engineering research for Continuous Screen Awareness & Temporal Visual Ingestion in the Aster Companion ecosystem. These findings directly inform our Supabase backend, Android Compose client, iOS SwiftUI app, laptop web client, and multimodal AI pipelines.

---

## Query Inventory & Verified Evidence

### Q1: Android MediaProjection API Android 14 15 FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION requirements

- **[Foreground service types  |  Background work  |  Android Developers](https://developer.android.com/develop/background-work/services/fgs/service-types)** (Exa)
- **[Foreground service types are required  |  Android Developers](https://developer.android.com/about/versions/14/changes/fgs-types-required)** (Exa)
- **[Media projection  |  Android media  |  Android Developers](https://developer.android.com/media/grow/media-projection)** (Exa)
- **[Changes to foreground service types for Android 15  |  Android Developers](https://developer.android.com/about/versions/15/changes/foreground-service-types)** (Exa)

### Q2: Android MediaProjection callback onStop user revoked capture handle foreground service

- **[Must register a callback before starting capture, to manage resources in response to MediaProjection states. · Issue #545 · opentok/opentok-android-sdk-samples · GitHub](https://github.com/opentok/opentok-android-sdk-samples/issues/545)** (Tavily)
  > "= null private val mediaProjectionCallback = object : MediaProjection.Callback() { override fun onStop() { super.onStop() Log.d(TAG, "MediaProjection stopped by system or user. Stopping stream.") stopStream() stopSelf() } } @RequiresApi(Build.VERSION_CODES.TIRAMISU) override fun onStartCommand(inten"
- **[Android Screen Sharing: MediaProjection + WebRTC (2026)](https://www.forasoft.com/blog/article/screen-sharing-android-1644)** (Tavily)
  > "Since Android 15 QPR1, any media projection stops automatically when the screen locks, and users can also end it from a status-bar chip. Handle `MediaProjection.Callback.onStop()` to tear down the track and tell the remote side.    MediaProjection or AccessibilityService.takeScreenshot() for screen"
- **[media/java/android/media/projection/MediaProjectionManager.java - platform/frameworks/base - Git at Google](https://android.googlesource.com/platform/frameworks/base/+/master/media/java/android/media/projection/MediaProjectionManager.java)** (Tavily)
  > "| \ callback can be a result of the system stopping MediaProjection due to various reasons. | | \ This includes the user stopping the MediaProjection via UI affordances in system-level UI, | | \ the screen being locked, or another {@link MediaProjection} session starting. | | \- Start the screen cap"

### Q3: VirtualDisplay ImageReader PixelCopy Android screen capture efficient YUV RGB bitmap

- **[Media projection  |  Android media  |  Android Developers](https://developer.android.com/media/grow/media-projection)** (Exa)
- **[tests/tests/view/src/android/view/cts/PixelCopyTest.java - platform/cts - Git at Google](https://android.googlesource.com/platform/cts/+/master/tests/tests/view/src/android/view/cts/PixelCopyTest.java)** (Exa)
- **[media/capture/content/android/java/src/org/chromium/media/ScreenCapture.java - chromium/src - Git at Google](https://chromium.googlesource.com/chromium/src/+/a18b95669ed38c0931818534ce17f131a006e476/media/capture/content/android/java/src/org/chromium/media/ScreenCapture.java)** (Exa)
- **[Medium](https://medium.com/bolt-labs/how-to-programmatically-capture-screen-on-android-a-comprehensive-guide-f500c95e455a)** (Exa)

### Q4: iOS ReplayKit RPBroadcastSampleHandler broadcast upload extension CMSampleBuffer video frame

- **[RPSystemBroadcastPickerView & iOS Screen Sharing (iOS 27)](https://www.forasoft.com/blog/article/how-to-implement-screen-sharing-in-ios-1193)** (Tavily)
  > "`RPBroadcastProcessModeSampleBuffer` is the value that tells ReplayKit to hand raw `CMSampleBuffer` video and audio to your `RPBroadcastSampleHandler` subclass (the other mode delivers MP4 clips through `RPBroadcastMP4ClipHandler`). For real-time screen sharing over WebRTC you always want the sample"
- **[SwiftUI: Create A BroadCast Service with Replay Kit](https://medium.com/@itsuki.enjoy/swiftui-create-a-broadcast-service-with-replay-kit-a108e175919b)** (Tavily)
  > "Broadcast Upload Extension: Here is where we will get those `CMSampleBuffers` for the recording, similar to (actually the same as) what we were receiving within the `startCapture` handler we had in my previous _ReplayKit For Screen/Video/Audio Recording or Capturing_. Here is where we will be proces"
- **[How to Implement Screen Sharing in iOS App Using ReplayKit and App Extension - Indie Hackers](https://www.indiehackers.com/post/how-to-implement-screen-sharing-in-ios-app-using-replaykit-and-app-extension-567497f65b)** (Tavily)
  > "Permission pop-up  ReplayKit starts generating a CMSampleBuffer stream for each media type – audio or video. The stream contains the media fragment itself – the captured video – and all necessary information.  `func handleSampleBuffer(_ sampleBuffer: CMSampleBuffer, sampleType: RPSampleBufferType )"

### Q5: iOS ReplayKit broadcast extension memory limit 50MB avoiding OOM process termination

- **[video-quickstart-ios/ReplayKitExample/README.md at ...](https://github.com/twilio/video-quickstart-ios/blob/master/ReplayKitExample/README.md?plain=1)** (Exa)
- **[ReplayKit broadcast extension crash EXC_RESOURCE RESOURCE_TYPE_MEMORY on mic on](https://stackoverflow.com/questions/61077318/replaykit-broadcast-extension-crash-exc-resource-resource-type-memory-on-mic-on)** (Exa)
- **[ReplayKit | Apple Developer Forums](https://developer.apple.com/forums/tags/replaykit)** (Exa)
- **[Memory limit issue with screen casting using the broadcast extension and WebRTC protocol on iOS](https://stackoverflow.com/questions/60392629/memory-limit-issue-with-screen-casting-using-the-broadcast-extension-and-webrtc)** (Exa)

### Q6: macOS ScreenCaptureKit low latency display audio stream capture SCStreamConfiguration

- **[How to Record System Audio on Mac with ScreenCaptureKit (Easy Guide)](https://creavit.studio/blog/screencapturekit-audio-recording-mac-guide)** (Tavily)
  > "ScreenCaptureKit is Apple's native framework for capturing screen content on macOS (introduced in macOS 12.3). It replaced the older CGWindowList and AVCaptureScreenInput APIs with a modern, high-performance alternative.  For developers building screen recording apps — or power users curious about h"
- **[Meet ScreenCaptureKit - WWDC22 - Videos - Apple Developer](https://developer.apple.com/videos/play/wwdc2022/10156)** (Tavily)
  > "`// Creating a SCStreamConfiguration object let streamConfig = SCStreamConfiguration() // Set output resolution to 1080p streamConfig.width = 1920 streamConfig.height = 1080 // Set the capture interval at 60 fps streamConfig.minimumFrameInterval = CMTime(value: 1, timescale: CMTimeScale(60)) // Hide"
- **[ScreenCaptureKit | Apple Developer Forums](https://developer.apple.com/forums/tags/screencapturekit)** (Tavily)
  > "let config = SCStreamConfiguration() config.capturesAudio = true let newStream = SCStream(filter: filter, configuration: config, delegate: self) try newStream.addStreamOutput(seldlerQueue: .main) if filter.isMicrophoneEnabled { try newStream.addStreamOutputsampleHandlerQueue: .main) } try await newS"

### Q7: Browser navigator.mediaDevices.getDisplayMedia screen share permission laptop client

- **[MediaDevices: getDisplayMedia() method - Web APIs | MDN](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getDisplayMedia)** (Exa)
- **[Using the Screen Capture API - Web APIs | MDN](https://developer.mozilla.org/en-US/docs/Web/API/Screen_Capture_API/Using_Screen_Capture)** (Exa)
- **[Screen Capture API - Web APIs | MDN](https://developer.mozilla.org/en-US/docs/Web/API/Screen_Capture_API)** (Exa)
- **[Privacy-preserving screen sharing controls  |  Web Platform  |  Chrome for Developers](https://developer.chrome.com/docs/web-platform/screen-sharing-controls)** (Exa)

### Q8: Adaptive frame sampling screen change detection perceptual hash pHash SSIM difference

- **[pHash vs dHash: Perceptual Image Hashing | MojoAuth Security Guides](https://mojoauth.com/security-guides/phash-vs-dhash)** (Tavily)
  > "Method. pHash works in the frequency domain (DCT); dHash works on pixel gradients. That is why pHash is slower but more stable under heavier tonal edits.  Speed. dHash is a resize plus 64 comparisons. pHash adds a 32×32 DCT, a small cost per image that adds up across millions of images.  Robustness."
- **[Perceptual Image Hashing for Near-Duplicate Detection | Mixpeek](https://mixpeek.com/guides/perceptual-image-hashing-near-duplicate-detection)** (Tavily)
  > "pHash costs more (a transform instead of a threshold) but it is the most resistant to compression, gamma shifts, and minor edits, which is why "perceptual hash" colloquially means pHash. A close cousin, wavelet hash (wHash), swaps the DCT for a Haar wavelet transform and keeps the low-frequency wave"
- **[Perceptual hashing - Wikipedia](https://en.wikipedia.org/wiki/Perceptual_hashing)** (Tavily)
  > "Perceptual hashing is the use of a fingerprinting algorithm "Fingerprint (computing)") that produces a snippet, hash, or fingerprint of various forms of multimedia. A perceptual hash is a type of locality-sensitive hash, which is analogous if features of the multimedia are similar. This is in contra"

### Q9: Mobile screen OCR ML Kit Text Recognition vs Tesseract latency on-device vs cloud

- **[Choose the Right On-Device Text Recognition (OCR) SDK on Android Using DeltaML - Fritz ai](https://fritz.ai/choose-the-right-on-device-text-recognition-sdk-on-android/)** (Exa)
- **[Top OCR Libraries for Mobile App Development in 2026 - Designveloper](https://www.designveloper.com/blog/mobile-ocr-libraries/)** (Exa)
- **[Text recognition v2 | ML Kit](https://developers.google.com/ml-kit/vision/text-recognition/v2)** (Exa)
- **[Comparing iOS Text Recognition SDKs Using Delta - Fritz ai](https://fritz.ai/comparing-on-device-text-recognition-ocr/)** (Exa)

### Q10: Visual temporal event graph reconstructing UI state transitions across sequential frames

- **[TempReasoner: neural temporal graph networks for event timeline construction](https://pmc.ncbi.nlm.nih.gov/articles/PMC12876831)** (Tavily)
  > "Figure 4 shows the hierarchical temporal encoder, which combines local and global temporal processing. The local and global temporal processors use gated mechanisms to capture short-range dependencies and event transitions across the whole sequence via a GRU, and to capture long-range temporal depen"
- **[Workflow visualization with Temporal’s Timeline View | Temporal](https://temporal.io/blog/lets-visualize-a-workflow)** (Tavily)
  > "FullTimeline  The Timeline represents the flow of Events in time as your Workflow is executing. It could be a series of sequential Events, or many all at once. There could be large gaps of time between them, or milliseconds. Some could fail or terminate or retry, some could complete as expected. All"
- **[Temporal Graph Machine Learning](https://medium.com/data-science-collective/temporal-graph-machine-learning-9cf3c82c6b77)** (Tavily)
  > "Jointly optimizing reconstruction and temporal smoothing:Here, the loss function consists of two terms. The first term measures the quality of the reconstruction (as in the static graph scenario) and the second term measures the similarity between the embeddings for each pair of consecutive time sta"

### Q11: Screen capture FPS vs upload FPS vs backend analysis FPS honest metrics reporting

- **[Screen recording benchmarks for developers: 4 metrics to compare in 2026 | transcribeall.io](https://transcribeall.io/blog/screen-recording-benchmarks-for-developers-4-metrics-to-compare-in-2026.php)** (Exa)
- **[Detect variable frame rate uploads with ffprobe and ...](https://dev.to/masonwritescode/detect-variable-frame-rate-uploads-with-ffprobe-and-normalize-them-before-they-break-your-pipeline-55cf)** (Exa)
- **[Testing Methodology & Measurement Standards | FPSRate](https://fpsrate.com/methodology/)** (Exa)
- **[We Need to Talk About FPS Metrics Reporting...](http://hole-in-my-head.blogspot.com/2023/03/we-need-to-talk-about-fps-metrics.html)** (Exa)

### Q12: Capturing internal app audio vs environmental microphone Android AudioPlaybackCaptureConfiguration

- **[How to record internal audio on Android devices or record MediaPlayer Audio Stream?](https://stackoverflow.com/questions/52543466/how-to-record-internal-audio-on-android-devices-or-record-mediaplayer-audio-stre)** (Tavily)
  > "To capture the audio, you then need to build an `AudioRecord` object and add the `AudioPlaybackCaptureConfiguration` to it:  1.   Call `AudioPlaybackCaptureConfiguration.Builder.build()`) to build an `AudioPlaybackCaptureConfiguration`. 2.   Pass the configuration to the `AudioRecord` by calling `se"
- **[AudioPlaybackCaptureConfiguration Class (Android.Media) | Microsoft Learn](https://learn.microsoft.com/en-us/dotnet/api/android.media.audioplaybackcaptureconfiguration?view=net-android-35.0)** (Tavily)
  > "``` [Android.Runtime.Register("android/media/AudioPlaybackCaptureConfiguration", ApiSince=29, DoNotGenerateAcw=true)] public sealed class AudioPlaybackCaptureConfiguration : Java.Lang.Object ```  ``` [] type AudioPlaybackCaptureConfiguration = class inherit Object ```  Inheritance :   Object      Ja"
- **[Capture video and audio playback  |  Android media  |  Android Developers](https://developer.android.com/media/platform/av-capture)** (Tavily)
  > "For security and privacy, playback capture imposes some limitations. To be able to capture audio, an app must meet these requirements:  `RECORD_AUDIO` `MediaProjectionManager.createScreenCaptureIntent()`  To capture audio from another app, your app must build an `AudioRecord` object and add an `Audi"

### Q13: OS security restrictions blocking protected content FLAG_SECURE Android DRM banking screens

- **[Secure sensitive activities  |  Fraud prevention  |  Android Developers](https://developer.android.com/security/fraud-prevention/activities)** (Exa)
- **[Protect your app and fight abuse with security flags FLAG_SECURE and REQUIRE_SECURE_ENV - Play Console Help](https://support.google.com/googleplay/android-developer/answer/14638385?hl=en)** (Exa)
- **[Prevent screen recording on DRM-protected videos](https://github.com/androidx/media/issues/2385)** (Exa)
- **[DRM  |  Android OS core topics  |  Android Open Source Project](https://source.android.com/docs/core/media/drm)** (Exa)

### Q14: Screen capture battery consumption thermal throttling mitigation 5 FPS vs 30 FPS vs 120 FPS

- **[screen](https://www.thefreedictionary.com/screen)** (Tavily)
  > "screen grab    screen grid    screen memory    screen off    screen out    screen pass    screen process    screen resolution    screen saver    screen test    screen trading    screen writer    screenager    screencap    screencraft    screened    screener    screenful    ▼ [...] screen filter  _n_"
- **[Screen - Wikipedia](https://en.wikipedia.org/wiki/Screen)** (Tavily)
  > "## Media display  [edit]   Electronic visual display, a cathode ray tube, liquid crystal display (LCD), or organic light emitting diode (OLED)  Touchscreen, a display device that also takes input via embedded pressure sensors  Projection screen, a viewing surface  Display device, an output device fo"
- **[Amazon.co.jp : screen](https://www.amazon.com/screen/s?k=screen)** (Tavily)
  > "## SCREEN(スクリーン) 2025年 3 月号【表紙】『キャプテン・アメリカ：ブレイブ・ニュー・ワールド』【特別付録】マッツ・ミケルセン『愛を耕すひと』  KTC 27" Gaming Monitor WQHD (2560x1440) Fast IPS 200Hz (210OC) 1ms (MPRT) 131%sRGB HDR400 Low Blue Light Flicker Free Free...  ## KTC 27" Gaming Monitor WQHD (2560x1440) Fast IPS 200Hz (210OC) 1ms (MPRT) 131%sRGB HDR40"

### Q15: Resumable video chunk upload protocol for continuous screen recording HLS WebM fragmented MP4

- **[Resumable.js — Chunked File Upload Library Documentation](https://www.resumablejs.com/)** (Exa)
- **[](https://cdn.jsdelivr.net/npm/@classytic/react-media@0.3.2/dist/video/recording/recorder.d.ts)** (Exa)
- **[Resumable and large files (tus) · Cloudflare Stream docs](https://developers.cloudflare.com/stream/uploading-videos/resumable-uploads/)** (Exa)
- **[](https://cdn.jsdelivr.net/npm/@classytic/react-media@0.3.2/dist/core/providers/mse-segment.d.ts)** (Exa)

### Q16: UI element detection bounding boxes accessibility tree semantic screen understanding

- **[WebUI: A Dataset for Enhancing Visual UI Understanding with ...](https://3dvar.com/Wu2023WebUI.pdf)** (Tavily)
  > "Element detection is an example of a task where labeled data is available in both the source and target domain (albeit fewer exam-ples of mobile screens), so it is possible to employ inductive transfer learning. The WebUI dataset contains the locations of elements that we scraped from the website ac"
- **[Browsers, code and assistive technologies — Web Accessibility Guide — NZ Government](https://govtnz.github.io/web-a11y-guidance/ka/fundamental-concepts-in-web-a11y/browsers-code-and-at)** (Tavily)
  > "For more on the accessibility tree, what it includes, and how it works, see:   The accessibility tree — Semantics to Screen Readers — A List Apart  How accessibility trees inform assistive tech — Hidde de Vries  The Accessibility Tree — Ben Myers  The Accessibility Tree — Web Fundamentals — Google D"
- **[The Accessibility Tree  |  Articles  |  web.dev](https://web.dev/articles/the-accessibility-tree)** (Tavily)
  > "Earlier we noted that screen readers will announce an element's role, name, state, and value. By using the right semantic element, role, state, and value are covered, but we must also ensure that we make an element's name discoverable.  Broadly, there are two types of names:   Visible labels, which"

### Q17: User visible status indicator floating bubble awareness active overlay Android WindowManager

- **[Use notification bubbles for conversations  |  Jetpack Compose  |  Android Developers](https://developer.android.com/develop/ui/compose/notifications/bubbles)** (Exa)
- **[How to detect if another app is floating above mine (e.g., overlay/chathead) on Android 11+?](https://stackoverflow.com/questions/79559468/how-to-detect-if-another-app-is-floating-above-mine-e-g-overlay-chathead-on)** (Exa)
- **[Behavior changes: all apps](https://developer.android.com/about/versions/12/behavior-changes-all)** (Exa)
- **[Detect Android Activity partially obscured without click/touch](https://stackoverflow.com/questions/77894919/detect-android-activity-partially-obscured-without-click-touch)** (Exa)

### Q18: iOS Live Activities Dynamic Island indicator for active screen broadcast extension

- **[Displaying live data with Live Activities | Apple Developer Documentation](https://developer.apple.com/documentation/activitykit/displaying-live-data-with-live-activities)** (Tavily)
  > "Live Activities can appear temporarily in the extended presentation in the Dynamic Island to allow interactions and status updates while a person is actively performing a task. Locking the device, collapsing the extended presentation in the Dynamic Island, or tapping outside the Dynamic Island ends"
- **[WWDC23: Design dynamic Live Activities  | Apple](https://www.youtube.com/watch?v=m6WMwSj_EbA)** (Tavily)
  > "[7:28] Your Live Activity receives this treatment automatically, but it's worth checking to make sure your colors have enough contrast when this mode is active. [7:36] Next, it's time to talk about the Dynamic Island. Here's Chan to go into all the details. Chan Karunamuni: Thanks, Mac. [7:43] The D"
- **[Live Activities essentials - WWDC26 - Videos - Apple Developer](https://developer.apple.com/videos/play/wwdc2026/223)** (Tavily)
  > "Live Activities can also expand to show more information from the Dynamic Island. This occurs when an alerting update happens or when someone long-presses on it. The expanded view provides even more space to let people know about essential updates.    And in iOS 27, Live Activities are visible in th"

### Q19: Contextual control panel quick pause stop mute awareness session architecture

- **[Contours · UX patterns for voice agents](https://dtrao100.github.io/contours/patterns/control-bar/)** (Exa)
- **[docs/presence-ui.md](https://github.com/leaf76/lazy-desktop-mcp/blob/main/docs/presence-ui.md)** (Exa)
- **[Customize media notifications and playback controls with the Media Session API  |  Articles  |  web.dev](https://web.dev/articles/media-session)** (Exa)
- **[](https://bitfreedom.net/code/apunkt/rowboat/commit/adb8b16a3ca8bee738ec92717141ea46ccaf1b22.diff)** (Exa)

### Q20: Temporal video embedding models for sequential screen state understanding Google Gemini Vision

- **[Show HN: Gemini can now natively embed video, so I built sub-second video search | Hacker News](https://news.ycombinator.com/item?id=47503617)** (Tavily)
  > "|  |  |  |  ---  |  |  | sohamrj 6 months ago  | parent | next (javascript:void(0))   Not aware of any that do native video-to-vector embedding the way Gemini Embedding 2 does. There are CLIP-based models (like VideoCLIP) that embed frames individually, but they don't process temporal video. you'd n"
- **[Video understanding  |  Gemini Enterprise Agent Platform  |  Google Cloud Documentation](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/video-understanding)** (Tavily)
  > "Use a higher Frame Per Second (FPS) sampling rate for videos requiring granular temporal analysis, such as fast-action understanding or high-speed motion tracking.  ## Limitations  While Gemini multimodal models are powerful in many multimodal use cases, it's important to understand the limitations"
- **[Video understanding  |  Gemini API  |  Google AI for Developers](https://ai.google.dev/gemini-api/docs/video-understanding)** (Tavily)
  > "Gemini API Gemini API  # Video understanding  To learn about video generation, see the Gemini Omni Flash guide.  Gemini models can process videos, enabling many frontier developer use cases that would have historically required domain specific models. Some of Gemini's vision capabilities include the"

