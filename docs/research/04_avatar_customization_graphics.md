# Aster Companion Research Dossier: Realistic 3D Human Avatar, Customization & Lip-Sync Graphics

**Domain Key**: `04_avatar_customization_graphics`  
**Generated**: November 2026  
**Total Queries Executed**: 20  

## Executive Findings & Architectural Directives

This document compiles verified engineering research for Realistic 3D Human Avatar, Customization & Lip-Sync Graphics in the Aster Companion ecosystem. These findings directly inform our Supabase backend, Android Compose client, iOS SwiftUI app, laptop web client, and multimodal AI pipelines.

---

## Query Inventory & Verified Evidence

### Q1: Three.js glTF avatar morph targets facial blendshapes ARKit 52 blendshapes

- **[examples/webgl_morphtargets_webcam.html](https://github.com/mrdoob/three.js/blob/9813ee76/examples/webgl_morphtargets_webcam.html)** (Exa)
- **[three-morph-targets-shapekeys — avnehsbhatia/ultraui](https://www.skills.sh/avnehsbhatia/ultraui/three-morph-targets-shapekeys)** (Exa)
- **[rana-jatin/avatar-stage](https://github.com/rana-jatin/avatar-stage)** (Exa)
- **[ThreeJS Blendshapes | mind-ar-js](https://hiukim.github.io/mind-ar-js-doc/more-examples/threejs-face-blendshapes/)** (Exa)

### Q2: Ready Player Me avatar customization API glTF export skin hair clothing styles

- **[GitHub - api-evangelist/ready-player-me: Ready Player Me — independent third-party profile of a public API surface, by API Evangelist. Create, retrieve, update, and delete Ready Player Me cross-platform avatars. Includes template-based creation, asset equipping, draft management, color palette discovery, and binary glTF (.glb) plus 2D PNG renders used in Unity, Unreal, web, iOS, and Andro · GitHub](https://github.com/api-evangelist/ready-player-me)** (Tavily)
  > "Documentation  OpenAPI — OpenAPI Specification  Postman Collection — Postman Collection 2.1  Open Collection — Open Collection 1.0  ### Ready Player Me Assets API  Discover and retrieve avatar wearable assets — hair, outfits, headwear, glasses, facewear, footwear, beards, costumes, and custom assets"
- **[Ready Player Me API — Docs, OpenAPI & Kin Score | APIs.io](https://apis.io/providers/ready-player-me)** (Tavily)
  > "Ready Player Me was a cross-game avatar platform: a hosted Avatar Creator plus REST APIs that produced interoperable 3D character avatars as binary glTF (.glb) and 2D PNG renders for Unity, Unreal, web, iOS and Android. The Avatars, Assets and Auth APIs covered draft/save avatar creation, template-b"
- **[Ready Player Me Discontinued (Jan 31, 2026) — What Happened & How to Migrate](https://avatarsdk.com/blog/2026/01/15/switch-from-ready-player-me-to-avatar-sdk-fast-familiar-production-ready)** (Tavily)
  > "Familiar integration flow — MetaPerson Creator embeds via iframe + JS API, much like RPM’s creator did  Engine-ready workflows for Web, Unity and Unreal  Configurable exports — LODs, formats (GLB/glTF and FBX) and texture resolutions  Avatar styles from cartoon to photorealistic, generated from a si"

### Q3: Real-time audio viseme generation Oculus Lipsync WebAudio API phoneme mapping

- **[HeadAudio | HeadAudio: An audio node/processor for real-time audio-driven viseme detection and lip-sync in browsers.](https://met4citizen.github.io/HeadAudio/)** (Exa)
- **[](https://developers.meta.com/vr/documentation/unreal/audio-ovrlipsync/)** (Exa)
- **[](https://developers.meta.com/vr/documentation/native/audio-ovrlipsync-viseme-reference/)** (Exa)
- **[Audio-driven avatar lipsync](https://salmanmkc.github.io/audio-avatar-lipsync/)** (Exa)

### Q4: Android Filament rendering engine 3D glTF avatar realistic human skin shader PBR

- **[PBR - Physically Based Rendering in glTF](https://www.khronos.org/gltf/pbr)** (Tavily)
  > "Khronos glTF PBR defines a standard set of parameters that are used to simulate real-world lighting interactions, materials, and surface properties. 3D artists and developers can use PBR to create stunning, lifelike environments that accurately respond to lighting conditions, reflections, and shadow"
- **[Filament -- Open Source PBR Engine Released](https://www.youtube.com/watch?v=gqXkPVQrfyQ)** (Tavily)
  > "# Filament -- Open Source PBR Engine Released ## Channel: Gamefromscratch (verified) 289K subscribers 408 likes  ### Description 22,270 views Posted: 2018-08-04 Filament is a PBR (Physically Based Rendering) cross platform real time rendering engine for Windows, Mac, Linux and Android.  Developed in"
- **[GitHub - google/filament: Filament is a real-time physically based rendering engine for Android, iOS, Windows, Linux, macOS, and WebGL2 · GitHub](https://github.com/google/filament)** (Tavily)
  > "filament-android filament-android-debug `filament-android` gltfio-android `filament-android` filament-utils-android `gltfio-android` filamat-android  ### iOS  iOS projects can use CocoaPods to install the latest release:  ## Documentation  `matc`  ## Examples  Night scene Night scene Materials Mater"

### Q5: Android SceneView 3D model viewer Jetpack Compose integration glTF animations

- **[sceneview/samples at main · sceneview/sceneview · GitHub](https://github.com/sceneview/sceneview/tree/main/samples)** (Exa)
- **[SceneView — 3D and AR for Compose, SwiftUI and the web](https://sceneview.github.io/)** (Exa)
- **[docs/docs/nodes.md](https://github.com/sceneview/sceneview/blob/main/docs/docs/nodes.md)** (Exa)
- **[GLB Model animations · sceneview/sceneview · Discussion #213 · GitHub](https://github.com/sceneview/sceneview/discussions/213)** (Exa)

### Q6: iOS SceneKit RealityKit realistic human avatar facial blendshapes ARFaceAnchor

- **[ARFaceAnchor.BlendShapeLocation | Apple Developer Documentation](https://developer.apple.com/documentation/arkit/arfaceanchor/blendshapelocation)** (Tavily)
  > "`static let mouthUpperUpRight: ARFaceAnchor.BlendShapeLocation`  The coefficient describing upward movement of the upper lip on the right side.  ### Eyebrows, Cheeks, and Nose  `static let browDownLeft: ARFaceAnchor.BlendShapeLocation`  The coefficient describing downward movement of the outer porti"
- **[Face Tracking with ARKit - Tech Talks - Videos - Apple Developer](https://developer.apple.com/videos/play/tech-talks/601)** (Tavily)
  > "which defines a geometry object that can be attached to any SceneKit node. Now aside from the geometry mesh, we also have something that we call blend shapes. Blend shapes provide a high-level model of the current facial expression. They're a dictionary of named coefficients representing the pose of"
- **[ARKit 52 Facial Blendshapes: The Ultimate Guide with Anatomy References for Artists](https://pooyadeperson.com/the-ultimate-guide-to-creating-arkits-52-facial-blendshapes)** (Tavily)
  > "Apple ARKit's 52 facial blendshapes are a set of predefined expressions designed for creating realistic facial animations.  Blendshapes, often referred to as "morph targets" control vertex movements on a scale from 0.0 to 1.0. At 0.0, the face is in its neutral state "eyes open & mouth closed"), whi"

### Q7: Avatar customization state schema hair color eye color skin tone clothing preset

- **[examples/avatars/avatar-customization.holo](https://github.com/brianonbased-dev/HoloScript/blob/main/examples/avatars/avatar-customization.holo)** (Exa)
- **[docs/schema-v0.md](https://github.com/neka-nat/kugutu/blob/main/docs/schema-v0.md)** (Exa)
- **[Configuration Schema | rooomAvatars | rooom Docs](https://developers.rooom.com/docs/rooom-avatars/editor/configuration-schema)** (Exa)
- **[](https://www.dicebear.com/styles/personas/presets/index.md)** (Exa)

### Q8: Decoupled avatar architecture visual presentation independent of memory and reasoning

- **[Reinforcement Learning to See, Hear, and Reason Over Video](https://openaccess.thecvf.com/content/CVPR2026/papers/Kulkarni_AVATAR_Reinforcement_Learning_to_See_Hear_and_Reason_Over_Video_CVPR_2026_paper.pdf)** (Tavily)
  > "7914 4.1. Off-Policy Architecture To address both the data inefficiency of on-policy learning and the vanishing advantage problem, AVATAR employs an off-policy architecture. [...] (e.g., combining speech and visual cues to identify the speaker) are critical. In the experiments, we apply AVATAR withi"
- **[AIA: Rethinking Architecture Decoupling Strategy In Unified Multimodal Model](https://arxiv.org/html/2511.22663v4)** (Tavily)
  > "!(2511.22663v4/fig/cuhk-logo2.png)  |  |  |  |  ## 1 Introduction  Unified Multimodal Model (UMM) is trained to perform two distinct tasks (e.g., visual generation and understanding) within a single network, aiming to enhance interpretability by visualizing intermediate processes (interleaved genera"
- **[Decoupled Cross-Attention Layers](https://www.emergentmind.com/topics/decoupled-cross-attention-layers)** (Tavily)
  > "Decoupled cross-attention layers are architectural constructs within neural networks, particularly transformer-derived models, that explicitly separate the sources and mechanisms of attention between different components, modalities, or hierarchical representations. Unlike traditional attention mech"

### Q9: Canvas 2D fallback realistic avatar animated glowing ring idle breathing animations

- **[Bot Avatars: animated AI agent avatars for React | Libraries.dev](https://libraries.dev/bots)** (Exa)
- **[Peraravatar — Free browser-only PNGTuber (OBS compatible) | GyunGyun×Create](https://gyungyun.com/en/works/peraravatar/)** (Exa)
- **[references/guides/ui-templates.md](https://github.com/pattern-ai-labs/agentcall/blob/main/references/guides/ui-templates.md)** (Exa)
- **[agent-avatar](https://registry.directory/educlopez/smoothui/agent-avatar)** (Exa)

### Q10: No-avatar mode accessible UI design for AI companion text and voice only

- **[15+ Chatbot UI Examples & Design Best Practices [2026]](https://ethora.com/blog/chatbot-ui-examples-and-best-practices)** (Tavily)
  > "Takeaway: Avatar and AR features are genuinely engaging but add significant UI complexity that most business chatbots don’t need. Know your use case before borrowing from consumer AI companion design.  1. Animated bubble UI (Concept)  Typed messages detach and float as animated bubbles into the conv"
- **[Headspace Rolls out Voice Feature for Empathetic AI Companion, Ebb](https://finance.yahoo.com/news/headspace-rolls-voice-feature-empathetic-130000616.html?fr=sycsrp_catchall)** (Tavily)
  > "Headspace is the leading everyday mental health companion, helping people care for their minds anytime, anywhere. Our all-in-one app delivers personalized support — from AI-powered guidance to meditation and mindfulness, coaching, and therapy — all designed to fit seamlessly into daily life. We part"
- **[Headspace Rolls out Voice Feature for Empathetic AI Companion, Ebb](https://finance.yahoo.com/news/headspace-rolls-voice-feature-empathetic-130000616.html)** (Tavily)
  > "Headspace is the leading everyday mental health companion, helping people care for their minds anytime, anywhere. Our all-in-one app delivers personalized support — from AI-powered guidance to meditation and mindfulness, coaching, and therapy — all designed to fit seamlessly into daily life. We part"

### Q11: WebGL 3D avatar performance optimization mobile browser 60 FPS low battery draw

- **[WebGL on Mobile: The Performance Budget Nobody Respects — xImmersion | Mobile WebGL Optimization & 3D Website Development Services](https://ximmersion.dev/blogs/webgl-on-mobile-performance-budget)** (Exa)
- **[High-Fidelity WebGL: Bringing 3D Avatars to Life in the Browser | Optential Ventures](https://www.optentialventures.com/blog/high-fidelity-webgl-bringing-3d-avatars-to-life-in-the-browser)** (Exa)
- **[Browser avatar performance budgets: protect the conversation before the spectacle — Turntaking Review](https://turntakingreview.com/guides/browser-avatar-performance-budgets/)** (Exa)
- **[PrismAvatar: Real-time animated 3D neural head avatars on edge devices](https://arxiv.org/html/2502.07030)** (Exa)

### Q12: Morph target interpolation smooth transitions between conversational expressions

- **[Morph target animation - Wikipedia](https://en.wikipedia.org/wiki/Morph_target_animation)** (Tavily)
  > "The "morph target" is a deformed version of a shape. When applied to a human face, for example, the head is first modelled with a neutral expression and a "target deformation" is then created for each other expression. When the face is being animated, the animator can then smoothly morph (or "blend""
- **[Mood Swings : Expressive Speech Animation](http://graphics.stanford.edu/papers/moodswings/moodswings.pdf)** (Tavily)
  > "4 Facial expression retargeting To retarget an expressive talking face to a different face model, we choose to use a blendshape retargeting method. Many commercial animation software systems have built-in methods for blendshape animation using a set of predeﬁned model poses. These basic poses are ty"
- **[glTF-Tutorials | glTF Tutorials](https://github.khronos.org/glTF-Tutorials/gltfTutorial/gltfTutorial_017_SimpleMorphTarget.html)** (Tavily)
  > "The asset contains an animation that interpolates between the different morph targets for a single triangle. A screenshot of this asset is shown in Image 17a.      Image 17a: A triangle with two morph targets."

### Q13: Audio amplitude to jawOpen morph target real-time procedural lip sync algorithm

- **[Article s10-05: TTS + Lip Sync — Three.js From Zero · MasterAllArts](https://masterallarts.com/learn/threejs-from-zero/s10-05-tts-lipsync/)** (Exa)
- **[Lip sync, and finding her face · Voice and avatar · Kotoba](https://kotoba.rodhnin.com/docs/voice-avatar/lip-sync-and-framing)** (Exa)
- **[Lip-Sync Pipeline (RMS → aa Expression) | tekkamelon/vroid_companion | DeepWiki](https://deepwiki.com/tekkamelon/vroid_companion/4.2-lip-sync-pipeline-(rms-aa-expression))** (Exa)
- **[Lip-sync | SDK Manual | Live2D Manuals & Tutorials](https://docs.live2d.com/en/cubism-sdk-manual/lipsync/)** (Exa)

### Q14: Realistic eye saccades blinking micro-expressions idle animation system in 3D avatars

- **[Using Facial Animation to Increase the Enfacement Illusion ...](https://discovery.ucl.ac.uk/10093933/1/Using_idle_facial_animation_to_increase_avatar_self_identification.pdf)** (Tavily)
  > "The idle facial system of the animated condition was comprised of a number of ambient animations intended to help make the avatar feel alive. A professional animator designed the facial system by authoring a number of looping animations on various parts of the face. For example, the nostrils scale s"
- **[TalkingEyes: Pluralistic Speech-Driven 3D Eye Gaze Animation](https://arxiv.org/html/2501.09921v2)** (Tavily)
  > "When generating animations, we first sample the number of blinks per minute from the distribution and then convert that into blink intervals. Subsequently, we adjust the expression parameters within a 5-frame window for each blink to create the blinking action. [...] To generate more vivid animation"
- **[Animating Blinks and Eye Movements for Subtlety](https://www.youtube.com/watch?v=-vwoMXAEp7Y)** (Tavily)
  > "#3Danimation #AnimationTutorial  #ComputerAnimation #AnimationSchool #StudentAnimation #CGIAnimation #AnimationMentor #LearnAnimation #3danimation  #Maya3d  #Animationjobs  #3Danimator [...] [13:15] We can do a lot with this to show emotion in animation, even though in real life is not realistic. So"

### Q15: Color grading post-processing warm amber glow lighting shader Three.js

- **[Color Grading Studio — Three.js Demos](https://threejsdemos.com/demos/postfx/color-grading)** (Exa)
- **[Amber, animated WebGL background · movin.design](https://movin.design/shaders/amber/)** (Exa)
- **[Post Processing 3DLUT](https://rbm-lib.github.io/three.js/manual/en/post-processing-3dlut.html)** (Exa)
- **[Home | postprocessing](https://pmndrs.github.io/postprocessing/public/docs/)** (Exa)

### Q16: glTF Draco mesh compression texture compression KTX2 mobile load time reduction

- **[Export guidelines • Asset Transformer SDK • Unity Docs](https://docs.unity.com/en-us/asset-transformer-sdk/2025.7/manual/sdktips/export-guidelines)** (Tavily)
  > "Important  Combining optimization + Draco compression + KTX2 textures typically achieves 90-95% file size reduction compared to uncompressed, unoptimized exports. This is the recommended configuration for web and mobile applications.  ​ [...] Important  Using KTX2 textures with Draco mesh compressio"
- **[3D Model Optimization for the Web: glTF, Draco, KTX2](https://threejsresources.com/3d-model-optimization)** (Tavily)
  > "KTX2 / Basis Universal stays compressed in GPU memory, roughly a quarter of the raw footprint. This is the correct answer for anything texture-heavy or mobile-facing. It needs a transcoder served alongside the model, which is a small one-off setup cost.  WebP decodes natively in every current browse"
- **[Compression ... draco + ktx2 example - Questions - three.js forum](https://discourse.threejs.org/t/compression-draco-ktx2-example/31382)** (Tavily)
  > "I used “gestaltor.io” the emerging gltf editor to create “draco compression” as well as “ktx2” compressed textures (converting them from jpeg / png)  The only working example that I could find is for “meshopt” compression + ktx2. This seems to be based on “gltfpack”. This is also quite powerful and"

### Q17: Avatar profile synchronization keeping companion appearance consistent across devices

- **[Create an Avatar on your Galaxy phone](https://www.samsung.com/us/support/answer/ANS10004606/)** (Exa)
- **[Chitin — Where you meet your AI](https://chitin.net/)** (Exa)
- **[How to export avatars and use your AI girlfriend across apps ...](https://pradprathivi.com/how-to-export-avatars-and-use-your-ai-girlfriend-across-apps-and-devices)** (Exa)
- **[Networking Avatars using Meta Avatars SDK | Meta Horizon OS Developers](https://latest.developers.meta.com/horizon/documentation/unity/meta-avatars-networking/)** (Exa)

### Q18: Accessible color contrast for avatar glow badges and status indicators WCAG AAA

- **[Accessible Color Contrast | Accessibly](https://accessiblyapp.com/web-accessibility/color-contrast)** (Tavily)
  > "The level AAA success criterion is known as enhanced contrast. This follows the same structure as the level AA success criterion but instead requires a more strict 7:1 ratio for normal text and 4.5:1 for large text. This higher level of contrast is recommended by the WCAG, but still higher than the"
- **[WebAIM: Contrast and Color Accessibility - Understanding WCAG 2 Contrast and Color Requirements](https://webaim.org/articles/contrast)** (Tavily)
  > "The only difference between this Level AAA success criterion and Level AA 1.4.3 is that contrast requirements are more stringent. It requires 7:1 contrast for normal text and 4.5:1 for large text. Although higher contrast is often recommended, Level AA conformance is the requirement within common la"
- **[Web Accessibility Color Contrast Checker - Conform to WCAG](https://accessibleweb.com/color-contrast-checker)** (Tavily)
  > "## How it Works  Please select a foreground color and a background color. You can enter hex color codes or use the color selector tool (aka eye dropper in the color input element). The “WCAG Compliance Information” chart will tell you if the selected colors pass conformance.  ## Select Colors  Contr"

### Q19: Interactive touch rotation zooming lighting controls in companion customization studio

- **[Elgato Stream Deck](https://companion.free/user-guide/v4.2/surfaces/elgato-streamdeck)** (Exa)
- **[Interface & Gestures  — Procreate Handbook](https://help.procreate.com/procreate/handbook/5.4/3d-painting/interface-gestures)** (Exa)
- **[Stream Deck + and Bitfocus Companion](https://heretorecord.com/blog/stream-deck-and-bitfocus-companion/)** (Exa)
- **[Stream Deck + XL (0fd9:00c6): touchstrip gestures and dial ...](https://github.com/bitfocus/companion-surface-elgato-stream-deck/issues/21)** (Exa)

### Q20: Exporting and caching avatar render snapshots for low-power dashboard thumbnails

- **[Loading and Caching Assets and Thumbnails | Apple Developer Documentation](https://developer.apple.com/documentation/photokit/loading-and-caching-assets-and-thumbnails)** (Tavily)
  > "## Overview  Photos automatically downloads or generates images to your specification, caching them for quick reuse. Use the `PHImageManager` class to request images of assets at a specified size, or AVFoundation objects to work with video assets. When working with large numbers of assets—for exampl"
- **[Dashboard Snapshots | Pricefx Documentation | Pricefx Knowledge Base](https://knowledge.pricefx.com/pricefx-unity-documentation/pricefx-capabilities/dashboards/dashboard-snapshots)** (Tavily)
  > "This feature enables users to schedule or trigger ad-hoc pre-calculated snapshots of Dashboards so they can access fully rendered results instantly, without waiting for heavy computations to run. By storing the serialized dashboard output in temporary cloud storage, users can load dashboards rapidly"
- **[Wayback Machine Snapshots Finder (Internet Archive) · Apify](https://apify.com/arthursbuisness/wayback-machine-snapshots)** (Tavily)
  > "Actor ideas  Get inspired to build Actors  Changelog  See what’s new on Apify  Customer stories  Find out how others use Apify  Company  About Apify  Contact us  Blog  Live events  Doing Good  Jobs  We're hiring!  Promotion image background  Join our Discord  Talk to other builders  Pricing  Contact"

