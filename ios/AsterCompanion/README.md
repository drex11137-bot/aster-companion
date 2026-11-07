# Aster Companion — Native iOS SwiftUI Client

Authoritative native iOS implementation for **Aster Companion**, built strictly adhering to PRD v1.1 and reference design screenshots.

---

## 1. Design System & Tokens

Conforms directly to the approved color scheme, contrast invariants, and typography:

| Design Token | Hex Code | Purpose / UI Mapping | WCAG Contrast |
| :--- | :--- | :--- | :--- |
| **Ground Base** | `#121110` | Deep graphite/black screen canvas | 15.2:1 AAA vs Cream |
| **Card Surface** | `#1C1A18` | Primary surface for cards, bubble containers | Structural rule |
| **Elevated Surface** | `#242220` | Secondary surface for dialogs, search inputs, pills | Subtle elevation |
| **Warm Amber Accent** | `#E59843` | Signature action color, snooze pill, avatar halo glow | 7.4:1 AA |
| **Restrained Violet** | `#7966F3` | User chat bubbles, timeline accents, "See all >" links | 4.8:1 AA |
| **Cream Text** | `#FAF8F5` | High-contrast body & header typography | 15.2:1 AAA |
| **Muted Ink** | `#A09D98` | Secondary labels, timestamps, metadata | 6.5:1 AA |
| **Online Status** | `#34D399` | Telemetry green online indicator dot | 3:1 graphical |
| **Divider Rule** | `#2B2825` | 1px subtle separation borders | Structural |

---

## 2. Core SwiftUI Screens

### `TodayView.swift`
- **Greeting & Online Presence**: Displays `"Good evening, Maya"`, Aster avatar with radiant warm amber halo glow (`#E59843`), and green online telemetry dot.
- **Next Reminder Card**: Surface card (`#1C1A18`) with amber calendar icon, reminder title (`"Call Dad at 7:30 PM"`), date badge (`"Today"`), and interactive warm amber capsule button `"Snooze"`.
- **Your Tasks Checklist**: Interactive checklist with toggleable checkboxes, task titles (`"Book dentist"`, `"Finish budget draft"`, `"Pick up parcel"`), due date sub-labels, and chevron right icons.
- **Recent Memories Carousel**: Horizontal scrollable carousel with rich thumbnail photo overlays (`"You love oat flat whites"`, `"Sister's birthday: Nov 14"`).

### `ChatView.swift`
- **Multimodal Stream**: Violet user bubble (`#7966F3`), dark Aster response bubble (`#1C1A18`).
- **Interactive Saturday Schedule Card**: Embedded timeline showing 9:00 AM Coffee, 11:30 AM Workout, 1:00 PM Lunch, 3:00 PM Personal Time, and 7:00 PM Wind Down with circular amber milestone badges and connector lines.
- **Citation Chips**: `"Used 2 memories"` chip launching the referenced memory audit sheet.
- **Quick Action Pills**: Horizontally scrolling pills for `"Add reminder"`, `"Summarize"`, and `"Voice Mode"`.
- **Input Composer**: Capsule bar with photo attachment, microphone button, and warm amber circular send button.

### `MemoryView.swift`
- **Search & Filter**: Capsule search bar and horizontally scrolling category chips (`"All"`, `"People"`, `"Preferences"`, `"Plans"`, `"Health"`).
- **Categorized Cards**: Cards with warm amber circular icons for Sun, Person, Health cross, and Running figure.
- **Explicit Profile Sharing Modal**: Item-level sharing between Profile 1 (Aster) and Profile 2 (Nova) enforcing cryptographic audit logs and user confirmation (PRD DEC-025).

### `CompanionStudioView.swift`
- **Profile Switcher**: Capsule switcher between `"Aster"` and `"Nova"`, enforcing the account constraint of maximum two isolated companion profiles.
- **Avatar Preview**: Large portrait circle with radial warm amber halo blur.
- **Customization Engine**:
  - Name editor with pencil focus trigger.
  - Hair color swatches: Auburn, Black, Brown, Blonde, Silver.
  - Eye color swatches: Hazel, Brown, Blue, Green, Grey.
  - Style chips: Natural, Casual, Professional, Creative.
  - Voice chips: Warm voice, Calm, Energetic, Playful.
- **Save Companion Button**: Full-width warm amber capsule button with confirmation feedback.

### `AwarenessView.swift`
- **Apple ReplayKit Integration**: Embeds `RPSystemBroadcastPickerView` to launch system-level broadcast extension.
- **Honest Perception Telemetry**: Distinguishes client Capture FPS (up to 120 FPS target), network Upload FPS, Ingestion FPS, and server Multimodal Analysis FPS.
- **Quick Controls**: Instant Pause Screen, Mute Environmental Audio, and Emergency Stop controls.

### `VoiceCallView.swift`
- **Full-Duplex Voice Call**: Audio streaming with low latency.
- **Ambient Sound-Reactive Visualizer**: Multi-layered pulsing fluid mesh combining warm amber and restrained violet gradients.
- **Live Transcript & Barge-In**: Real-time scrolling transcription with active speaking/listening indicators.

---

## 3. Services & Architectural Invariants

### Profile Isolation (PRD Section 9 & DEC-021)
- Exactly maximum two profiles per account.
- Zero implicit data sharing between profiles.
- Session suspension upon switching profiles prevents context contamination.

### ReplayKit Broadcast Extension (`Sources/ReplayKitBroadcastExtension/SampleHandler.swift`)
- Subclasses `RPBroadcastSampleHandler`.
- Processes `CMSampleBuffer` for `.video`, `.audioApp`, and `.audioMic`.
- Emits real-time sequence numbers and measured FPS over App Group IPC (`group.com.astercompanion.shared`).

### Offline Resilience (`SupabaseClient.swift` & `AppState.swift`)
- Offline write outbox queue with persistent storage in `UserDefaults`.
- Automatic retry and monotonic sequence drain when network connectivity resumes.

---

## 4. macOS Host & Xcode Build Setup

Per `docs/ios-macos-handoff.md`:

```bash
# 1. Open with Xcode directly
open AsterCompanion.xcodeproj

# 2. Or regenerate Xcode project with XcodeGen
xcodegen generate

# 3. Or build with Swift Package Manager
swift build
swift test
```
