# Aster Companion Research Dossier: Real-Time Audio, Streaming Voice, Full-Duplex & VAD

**Domain Key**: `01_realtime_audio_voice`  
**Generated**: November 2026  
**Total Queries Executed**: 20  

## Executive Findings & Architectural Directives

This document compiles verified engineering research for Real-Time Audio, Streaming Voice, Full-Duplex & VAD in the Aster Companion ecosystem. These findings directly inform our Supabase backend, Android Compose client, iOS SwiftUI app, laptop web client, and multimodal AI pipelines.

---

## Query Inventory & Verified Evidence

### Q1: OpenAI Realtime API WebRTC protocol session creation client_secret ephemeral token

- **[Sessions](https://developers.openai.com/api/reference/resources/realtime/subresources/sessions/index.md)** (Exa)
- **[WebRTC | OpenAI API](https://developers.openai.com/api/docs/guides/voice-webrtc)** (Exa)
- **[](https://developers.openai.com/api/reference/resources/realtime/subresources/client_secrets/methods/create)** (Exa)
- **[Getting started with the Realtime API](https://developers.openai.com/api/docs/guides/realtime)** (Exa)

### Q2: Gemini Multimodal Live API bidirectional WebSocket audio streaming protocol format

- **[ADK Gemini Live AI Toolkit: A Visual Guide to Real-Time Multimodal AI Agent Development | by Kaz Sato | Google Cloud - Community | Medium](https://medium.com/google-cloud/adk-bidi-streaming-a-visual-guide-to-real-time-multimodal-ai-agent-development-62dd08c81399)** (Tavily)
  > "`response_modalities` determines whether the model responds with text or audio. You must choose one per session—`["TEXT"]` for chat applications, `["AUDIO"]` for voice. Native audio models require audio output; half-cascade models support both.  `streaming_mode` selects the transport protocol. BIDI"
- **[Google Colab](https://colab.research.google.com/github/GoogleCloudPlatform/generative-ai/blob/main/gemini/multimodal-live-api/intro_multimodal_live_api.ipynb)** (Tavily)
  > "spark Gemini   keyboard_arrow_down ### Audio Streaming  Implementing real-time audio requires strict adherence to sample rate specifications and careful buffer management to ensure low latency and natural interruptibility.  The Live API supports the following audio formats:     Input audio: Raw 16-b"
- **[OpenAI Realtime API Alternatives: Best Realtime APIs in 2026](https://inworld.ai/resources/openai-realtime-api-alternatives)** (Tavily)
  > "The architecture is different from modular approaches. Gemini 3.1 Flash Live is built on Gemini 3 Pro and accepts audio, images, video, and text as inputs with a 128K token context window. The Live API uses a bidirectional WebSocket connection. Raw 16-bit PCM audio at 16kHz goes in. Raw PCM audio co"

### Q3: Full duplex voice agent turn-taking barge-in cancellation WebRTC audio buffer management

- **[Turns and interruptions](https://pydantic.dev/docs/ai/realtime/turns/)** (Exa)
- **[Build a Real-Time, Full-Duplex Voice AI with WebRTC | ZedIoT Blog](https://zediot.com/blog/building-full-duplex-conversational-ai-with-rtc-ai/)** (Exa)
- **[Handling Interruptions (Barge-in) - Lokutor](https://docs.lokutor.com/guides/handling-barge-in)** (Exa)
- **[Adaptive interruption handling | LiveKit Documentation](https://docs.livekit.io/agents/logic/turns/adaptive-interruption-handling/)** (Exa)

### Q4: Voice activity detection VAD Silero WebRTC VAD threshold energy speech onset detection

- **[Voice Activity Detection - A Lazy Data Science Guide](http://mohitmayank.com/a_lazy_data_science_guide/audio_intelligence/voice_activity_detection)** (Tavily)
  > "Skip to content   Introduction  Steps in VAD  Code     + Py-WebRTC VAD   + Silero-VAD  # Voice Activity Detection  ## Introduction   🗣 Voice activity detection (VAD) is the process of identifying the chunks or parts of an audio stream that contains certain "voiced activities".  There could be differ"
- **[Voice activity detection: VAD for voice agents | Cartesia](https://www.cartesia.ai/learn/voice-activity-detection)** (Tavily)
  > "WebRTC VAD is an option for frame-level speech decisions with strict PCM format requirements. Silero VAD is a neural detector with PyTorch and ONNX options. Compare them on audio from your intended devices, noise conditions, and speakers. Neither standalone detector decides whether a sentence is com"
- **[Voice Activity Detection in the Browser](https://micdrop.dev/blog/voice-activity-detection-browser)** (Tavily)
  > "Silero VAD is a neural network of about 309K parameters that reads a 512-sample frame, 32 milliseconds at 16 kHz, and returns the probability that the frame contains speech. Its LSTM state carries across frames, so it scores each frame using the ones before it. A volume threshold measures loudness a"

### Q5: WebRTC jitter buffer audio echo cancellation acoustic echo suppression mobile Android iOS

- **[modules/audio_processing/aecm/echo_control_mobile.cc - src.git - Git at Google](https://webrtc.googlesource.com/src.git/+/bb547203bfebcc478b263c4e9ca173c6fd5a0c5d/modules/audio_processing/aecm/echo_control_mobile.cc)** (Exa)
- **[modules/audio_device/android/java/src/org/webrtc ...](https://chromium.googlesource.com/external/webrtc/+/HEAD/modules/audio_device/android/java/src/org/webrtc/voiceengine/WebRtcAudioEffects.java)** (Exa)
- **[Twilio Voice Mobile SDKs Audio Options API | Twilio](https://www.twilio.com/en-us/changelog/twilio-voice-mobile-sdks-audio-options-api-now-available-in-ga)** (Exa)
- **[jni/webrtc/modules/audio_processing/aec/echo_cancellation.c](https://github.com/illuspas/libaec-android/blob/master/jni/webrtc/modules/audio_processing/aec/echo_cancellation.c)** (Exa)

### Q6: Opus codec 24kHz 48kHz streaming chunk duration 20ms frame size low latency voice

- **[OpusFAQ - XiphWiki](https://wiki.xiph.org/OpusFAQ)** (Tavily)
  > "A 20ms frame size works well for most applications. Smaller frame sizes may be used to achieve lower latency, but have lower quality at a given bitrate. [...] Sizes greater than 20 ms increase latency and are generally beneficial only at fairly low bitrates, or when used to reduce external overhead"
- **[Opus Codec: The Audio Format Explained | WebRTC Streaming | Wowza](https://www.wowza.com/blog/opus-codec-the-audio-format-explained)** (Tavily)
  > "Opus provides a very performant 26.5 ms latency using its default settings (20 ms frame size), making it highly suitable for Voice over IP (VoIP) communications.  ### Narrowband to Fullband [...] ### Low Latency  The lag between when a user speaks and when someone else on the other side of the inter"
- **[[1602.04845] High-Quality, Low-Delay Music Coding in the Opus Codec](https://ar5iv.labs.arxiv.org/html/1602.04845)** (Tavily)
  > "Like other transform codecs, Opus controls pre-echo primarily by varying the MDCT size. When the encoder detects a transient, it computes multiple short MDCTs over the frame and interleaves the output coefficients. For 20-ms frames, there are 8 MDCTs with full-overlap, 5 ms windows. We constrain the"

### Q7: Synthetic voice disclosure guidelines FCC FTC watermarking C2PA provenance standards

- **[Reducing Risks Posed by Synthetic Content: An Overview of Technical Approaches to Digital Content Transparency](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-4.pdf)** (Exa)
- **[In the Matter of Implications of Artificial Intelligence Technologies on Protecting Consumers from Unwanted Robocalls and Robotexts](https://docs.fcc.gov/public/attachments/FCC-24-84A1.pdf)** (Exa)
- **[AI Output Disclosures: Use, Provenance, Adverse Incidents | National Telecommunications and Information Administration](https://www.ntia.gov/issues/artificial-intelligence/ai-accountability-policy-report/developing-accountability-inputs-a-deeper-dive/information-flow/ai-output-disclosures)** (Exa)
- **[Fcc 24 84a4](https://docs.fcc.gov/public/attachments/FCC-24-84A4.txt)** (Exa)

### Q8: Consent verification workflow for voice cloning biometric authorization protocol

- **[Voice Cloning in 2026: Ethics, Consent, and Compliance](https://www.callmissed.com/blog/voice-cloning-in-2026-ethics-consent-and-compliance)** (Tavily)
  > "User-proofed authorization—The actual voice owner must perform an action (voice or text signature) at the moment of consent.  Time- and purpose-stamping—The consent includes when and for what use(s) the voice can be cloned.  Linkage to downstream assets—All generated samples, models, and deployments"
- **[Understanding Deepfake Voice Fraud: AI Voice Cloning Risks | Adaptive Security](https://www.adaptivesecurity.com/blog/deepfake-voice-fraud)** (Tavily)
  > "voice biometrics cannot serve as a standalone identity verification control, and organizations relying on voice ID need layered, out-of-band verification workflows to compensate for the structural weakness. [...] Protecting against deepfake voice fraud requires layering behavioral protocols, verific"
- **[AI Voice Cloning Attacks and How to Detect Them](https://sosafe-awareness.com/glossary/voice-cloning)** (Tavily)
  > "Documentation: For these steps to stand up to an audit, they belong in a written procedure. A log recording the time and outcome of each verification makes the practice traceable. Evidence of this kind can feed into management systems aligned with ISO 27001, NIS2 or DORA, the latter two being EU fra"

### Q9: Server side audio streaming backpressure mitigation queue management WebSocket drops

- **[Production Patterns - Telnyx](https://developers.telnyx.com/docs/voice/stt/websocket-streaming/production-patterns)** (Exa)
- **[maxmillienjr/realtime-voice-infra](https://github.com/maxmillienjr/realtime-voice-infra)** (Exa)
- **[internal/pipeline/realtime_audio.go](https://github.com/streamcoreai/streamcore-server/blob/9fcb472e/internal/pipeline/realtime_audio.go)** (Exa)
- **[Audio Pipeline | Backchannel](https://backchannel.page/docs/audio-pipeline/)** (Exa)

### Q10: OpenAI Realtime API server_vad input_audio_buffer.speech_started response.cancel event flow

- **[Realtime conversations | OpenAI API](https://developers.openai.com/api/docs/guides/realtime-conversations)** (Tavily)
  > "1. The client monitors for new `input_audio_buffer.speech_started` events from the server, which indicate the user has started speaking. The server will automatically cancel any in-progress model response and a `response.cancelled` event will be emitted. 2. When the client detects this event, it sho"
- **[Need help being able to interrupt the Realtime API response - API - OpenAI Developer Community](https://community.openai.com/t/need-help-being-able-to-interrupt-the-realtime-api-response/972589)** (Tavily)
  > "INFO:vad:Speech started   INFO:main:Speech has started.   INFO:main:User started speaking while audio is playing.   INFO:main:Clearing input audio buffer.   INFO:main:Cancelling response.   INFO:main:Truncate the current audio, current item ID: item\_AHaqWiaRzvSTacllhd5u8, current audio content inde"
- **[Use the GPT Realtime API for speech and audio with Azure OpenAI - Microsoft Foundry | Microsoft Learn](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/realtime-audio)** (Tavily)
  > "The server sends the `input_audio_buffer.speech_started` event when it detects the start of speech.  At any time, the client can optionally append audio to the buffer by sending the `input_audio_buffer.append` event.  The server sends the `input_audio_buffer.speech_stopped` event when it detects the"

### Q11: Gemini Live API BidiGenerateContentSetup generation_config speech_config voice_name

- **[Live API - WebSockets API reference  |  Gemini API  |  Google AI for Developers](https://ai.google.dev/api/live)** (Exa)
- **[Live API capabilities guide  |  Gemini API  |  Google AI for Developers](https://ai.google.dev/gemini-api/docs/live-api/capabilities)** (Exa)
- **[Get started with Gemini Live API using the Google GenAI SDK  |  Gemini API  |  Google AI for Developers](https://ai.google.dev/gemini-api/docs/live-api/get-started-sdk)** (Exa)
- **[Configure language and voice  |  Gemini Enterprise Agent Platform  |  Google Cloud Documentation](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/live-api/configure-language-voice)** (Exa)

### Q12: Streaming speech synthesis TTS chunked audio playback low latency AudioTrack Android

- **[Android Real-Time TTS: Streaming Text-to-Speech Tutorial [2025]](https://picovoice.ai/blog/android-streaming-text-to-speech)** (Tavily)
  > "#### 4a. Configure AudioTrack  `Orca` outputs mono, 16-bit PCM, with a sample rate of 22050 Hz, which is a common format for speech synthesis. Using `AudioTrack` in streaming mode allows you to play audio chunks incrementally, keeping latency low.  ```  val sampleRate = orca?.sampleRate ?: 22050  va"
- **[Streaming Text to Speech API Developer Guide | Bland AI](https://www.bland.ai/blog/streaming-text-to-speech)** (Tavily)
  > "Streaming text to speech systems that split LLM output into small chunks for low latency often feed the TTS engine incomplete syntactic units, causing unnatural pacing, flat intonation, and listener fatigue. Production teams must implement intelligent sentence-boundary detection or minimum-chunk-siz"
- **[Stream low-latency speech from AI agents using Kokoro TTS on Amazon SageMaker AI | Artificial Intelligence](https://aws.amazon.com/blogs/machine-learning/stream-low-latency-speech-from-ai-agents-using-kokoro-tts-on-amazon-sagemaker-ai)** (Tavily)
  > "This solution closes the gap by streaming synthesis alongside generation instead of waiting for it to finish. As the agent produces each sentence, that sentence streams immediately to a hosted Kokoro-82M text-to-speech model, so audio playback can start before the agent finishes speaking its full re"

### Q13: AVAudioEngine iOS low latency full duplex audio record and playback simultaneous

- **[Tips about AVAudioEngine | /var/log/snak](https://snakamura.github.io/log/2024/11/audio_engine.html)** (Exa)
- **[Problems Recording and Playing Back Audio Simultaneously](https://stackoverflow.com/questions/31871168/problems-recording-and-playing-back-audio-simultaneously)** (Exa)
- **[mobile/packages/expo-two-way-audio/ios/AudioEngine.swift](https://github.com/stablyai/orca/blob/main/mobile/packages/expo-two-way-audio/ios/AudioEngine.swift)** (Exa)
- **[What’s New in Core Audio](https://devstreaming-cdn.apple.com/videos/wwdc/2015/507pq8rldk/507/507_whats_new_in_core_audio.pdf?dl=1)** (Exa)

### Q14: Handling network interruption in WebRTC voice session ICE restart reconnect resumption

- **[Lifetime of a WebRTC session - Web APIs | MDN](https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API/Session_lifetime)** (Tavily)
  > "Sometimes, during the lifetime of a WebRTC session, network conditions change. One of the users might transition from a cellular to a Wi-Fi network, or the network might become congested, for example. When this happens, the ICE agent may choose to perform ICE restart. This is a process by which the"
- **[ICE Restart: renegotiating connectivity in place](https://bloggeek.me/webrtcglossary/ice-restart)** (Tavily)
  > "BlogGeek.me  # ICE Restart  NAT traversal·Updated Oct 2026·5 min read  ICE restart is a mechanism in WebRTC that triggers a fresh round of ICE negotiation on an existing PeerConnection without tearing down the session.  It is defined in IETF RFC 8445 (the current ICE specification) and exposed in th"
- **[Both WebRTC peers initiate ICE restart simultaneously](https://stackoverflow.com/questions/50763607/both-webrtc-peers-initiate-ice-restart-simultaneously)** (Tavily)
  > "Thanks for the help. That seems to be a good solution. Another thing I am confused about is ICE restart. So, let's say peer A connects for the first time and creates an offer and sends it. In this case the iceRestart parameter should be false. Then let's say connection loss happens and the peer does"

### Q15: Audio packet loss concealment PLC algorithm conversational latency under 300ms

- **[Complex-bin2bin: A Latency-Flexible Generative Neural Model for Audio Packet Loss Concealment](https://doi.org/10.1109/taslp.2024.3515794)** (Exa)
- **[G.711 App. I (09/1999)](https://www.itu.int/ITU-T/recommendations/rec.aspx?rec=5065)** (Exa)
- **[Real-Time Packet Loss Concealment With Mixed Generative and Predictive Model](https://www.isca-archive.org/interspeech_2022/valin22_interspeech.pdf)** (Exa)
- **[Adaptive playout scheduling and loss concealment for voice communication over ip networks - Multimedia, IEEE Transactions on](https://web.stanford.edu/~bgirod/pdfs/LiangMM2003.pdf)** (Exa)

### Q16: Partial transcript generation and speculative response cancellation in voice agents

- **[Voice Agent Turn-Taking: The 250ms Threshold That Reshapes Your Architecture](https://tianpan.co/blog/2026/05/10/voice-agent-turn-taking-250ms-threshold-reshapes-architecture)** (Tavily)
  > "Once you accept that endpointing has irreducible latency — even an excellent semantic detector adds 150–300ms — the next move is to do useful work during that window. Speculative LLM generation kicks off inference on the partial transcript when STT confidence crosses a threshold (typically 80–90%),"
- **[voice-agent-examples/docs/SPECULATIVE_SPEECH_PROCESSING.md at main · NVIDIA/voice-agent-examples · GitHub](https://github.com/NVIDIA/voice-agent-examples/blob/main/docs/SPECULATIVE_SPEECH_PROCESSING.md)** (Tavily)
  > "Interim transcripts will be processed: Response generation starts after the first stable interim transcript is received  Speculative caching: TTS responses are speculatively cached until the user stops speaking  Reduced latency: Early response generation takes place on the basis of interim transcrip"
- **[Introducing Flux STT: Conversational Speech Recognition](https://deepgram.com/learn/introducing-flux-conversational-speech-recognition)** (Tavily)
  > "Building voice agents today is messy. Pipelines stack ASR, VAD, endpointing, and client-side logic, forcing developers to reconcile thresholds, timers, and cancellation rules instead of focusing on conversation. And even after stitching all that together, traditional ASR still floods you with partia"

### Q17: Microphone permission handling and privacy indicator compatibility Android 14 15

- **[Privacy indicators  |  Android Open Source Project](https://source.android.com/docs/core/permissions/privacy-indicators)** (Exa)
- **[Privacy checklist  |  Android Developers](https://developer.android.com/privacy-and-security/about)** (Exa)
- **[Explain access to more sensitive information  |  Privacy  |  Android Developers](https://developer.android.com/training/permissions/explaining-access)** (Exa)
- **[packages/SystemUI/src/com/android/systemui/appops/AppOpsControllerImpl.java - platform/frameworks/base - Git at Google](https://android.googlesource.com/platform/frameworks/base/+/master/packages/SystemUI/src/com/android/systemui/appops/AppOpsControllerImpl.java)** (Exa)

### Q18: iOS microphone privacy recording indicator AVAudioSessionCategoryPlayAndRecord options

- **[Apple iOS 14 privacy improvements: visual notifications](https://www.cnbc.com/2020/07/10/apple-ios-14-privacy-improvements-visual-notifications.html)** (Tavily)
  > "For years, people have alleged that social apps like Facebook use the iPhone's microphone to listen into conversations surreptitiously and target ads, claiming that they saw an ad for a company or product right after they were talking about it. Facebook has consistently denied it.  But if that were"
- **[What Do the Green and Orange Dots Mean on an iPhone?](https://www.businessinsider.com/guides/tech/green-orange-light-dot-on-iphone?op=1)** (Tavily)
  > "With the iOS 14 update, Apple introduced a number of new tools to help users protect their privacy, and force apps to be more transparent with how they use your phone.  The indicator lights are part of that, alerting users if third-party apps use their microphone or camera without consent. If you fi"
- **[Alert iPhone Users - Your iPhone Is Listening Turn This settings Off Immediately](https://www.youtube.com/watch?v=c59qaxqiC9Q)** (Tavily)
  > "[14:20] someone or simply want to review your existing permissions. [14:24] 15th, check the orange microphone indicator. Finally, let's talk about a small indicator on your iPhone that [14:32] everyone should know about. When you see an orange indicator at the top of your screen, it means an app is"

### Q19: Provider-neutral voice adapter abstraction layer OpenAI Realtime vs Gemini Live vs ElevenLabs

- **[deliberium/vona](https://github.com/deliberium/vona)** (Exa)
- **[Introduction - RealtimeSwitch API Documentation](https://realtimeswitch.com/docs/introduction)** (Exa)
- **[README.md](https://github.com/Kkartik14/TVIC/blob/main/README.md)** (Exa)
- **[README.md](https://github.com/Inferensys/realtime-voice-agent-starter/blob/main/README.md)** (Exa)

### Q20: Voice cloning security safeguards preventing deepfake impersonation authorization flow

- **[AI Voice Cloning Scams: Detection and Prevention Guide | Adaptive Security](https://www.adaptivesecurity.com/blog/the-ultimate-guide-to-ai-voice-cloning-scams-how-to-detect-prevent-and-protect-against-them)** (Tavily)
  > "Individual awareness is necessary but insufficient in organizational environments. Preventing AI voice cloning scams at the enterprise level requires structural controls that prevent authorization of high-risk actions through a single communication channel. According to Right-Hand AI's The State of"
- **[Protect Executives from AI Voice Cloning & Deepfakes](https://vanishid.com/resources/blog/ai-voice-cloning-deepfake-protection)** (Tavily)
  > "What remains consistent is the value of layered defenses. The safe phrase protocol, the occlusion test, independent callback verification, organizational awareness training, and executive digital footprint reduction each address a different point in the attack chain. Used together, they significantl"
- **[AI Impersonation: Why detection fails, what actually works](https://www.yubico.com/resources/glossary/ai-impersonation)** (Tavily)
  > "In 2024, LastPass security teams received deepfake audio calls impersonating their CEO with voice cloning so convincing that employees nearly granted unauthorized access to sensitive systems. The attack failed only because LastPass had already implemented additional verification protocols. Most orga"

