# Aster Companion — Web & Laptop Client

Production-grade, responsive desktop and web client for **Aster Companion**, built strictly in accordance with **PRD v1.1** and the 4 reference design system screenshots.

---

## 🎨 Design System & Palette

- **Dark Graphite Base:** `#121110`
- **Elevated Card Surfaces:** `#1C1A18` / `#22201E` (subtle borders `#2A2724` / `#332F2B`)
- **Warm Amber Accent:** `#E59843` / `#F5A623` (glow: `rgba(229, 152, 67, 0.35)`)
- **Restrained Violet:** `#7966F3` (glow: `rgba(121, 102, 243, 0.35)`)
- **Cream Text:** `#FAF8F5`
- **Muted Text:** `#A09E9B`
- **Online Indicator:** `#22C55E`

---

## 📱 Implemented Screens & Features

### 1. `Today` Screen (`TodayScreen.tsx`)
- **Greeting & Status:** "Good evening, Maya", Aster circular portrait with warm radial amber glow and bright green online indicator dot.
- **Tagline:** *"A calmer, brighter you — one step at a time."*
- **Next Reminder Card:** Warm amber calendar icon, *"Call Dad at 7:30 PM Today"*, and interactive **Snooze** button with audio chime and status feedback.
- **Your Tasks Checklist:** Interactive checkboxes with completion toggle, due date labels (*"Today"*, *"Tomorrow"*, *"This week"*), and inline task creation.
- **Recent Memories Photo Cards:** Pixel-matched photographic memory cards (*"You love oat flat whites"*, *"Sister's birthday: Nov 14"*).

### 2. `Chat` Screen (`ChatScreen.tsx`)
- **Multimodal Message Thread:**
  - Violet user message bubble (`#7966F3`) with delivery timestamp and double checks (`✓✓`).
  - Dark graphite Aster bubble (`#1C1A18`) with companion avatar.
- **Interactive Saturday Schedule Card:**
  - Date title *"Saturday, Nov 15"* with vertical timeline connectors.
  - Distinct timeline nodes: 9:00 AM Slow morning (coffee), 11:30 AM Gentle workout (dumbbell), 1:00 PM Lunch (utensils), 3:00 PM Personal time (book), 7:00 PM Wind down (moon).
- **Citation Chip:** Clickable *"Used 2 memories"* chip opening the citation inspector displaying exact memory provenance and relevance confidence.
- **Quick Action Pills:** *"Add reminder"* & *"Summarize"*.
- **WebAudio Microphone & Speech Input:** Real browser audio recording with active timer, transcript generation, and warm amber send button.

### 3. `Memories` Screen (`MemoriesScreen.tsx`)
- **Header & Search:** Full-text search with instant filtering.
- **Category Filter Pills:** *"All"*, *"People"*, *"Preferences"*, *"Plans"*.
- **Memory Cards:** Distinct icon representations (Sun, Person, Health plus, Running athlete) with inline edit, delete, and share actions.
- **Explicit Memory Sharing Modal (`MemorySharingModal.tsx`):** PRD Section 9.4 compliant item-level sharing between Profile 1 (Aster) and Profile 2 (Nova) with confirmation and audit logging.

### 4. `Companion Studio` (`CompanionStudioScreen.tsx`)
- **Dual Profile Switcher:** Seamless switching between independent companion profiles (*"Aster"* vs *"Nova"*).
- **Interactive Avatar Canvas (`AvatarCanvas.tsx`):**
  - Mouse-responsive 3D tilt perspective.
  - Warm amber radial back-glow.
  - Automatic blinking lids and breathing animation.
- **Name Editor:** Inline renaming with persistence.
- **Appearance Swatches:**
  - Hair color swatches: Auburn, Black, Brown, Blonde, Silver.
  - Eye color swatches: Hazel, Brown, Blue, Green, Grey.
  - Style selector pills: Natural, Casual, Professional, Creative.
  - Voice selector pills: Warm voice, Calm, Energetic, Playful, with real Web Speech / Web Audio preview playback.
- **Save Companion:** Warm amber CTA button with celebratory feedback.

### 5. `Awareness & Screen Sharing` (`AwarenessScreen.tsx`)
- **Laptop Display Capture:** Invokes `navigator.mediaDevices.getDisplayMedia` for real screen sharing, with fallback high-fidelity simulated perception pipeline.
- **Microphone Stream:** `navigator.mediaDevices.getUserMedia` integration.
- **Real-Time Telemetry Dashboard:**
  - Capture FPS (target 120 FPS as specified in PRD Section 5.3)
  - Upload FPS
  - Analysis FPS
  - Latency (ms)
  - Monotonic frame sequence counter
  - Integrity & gap detection (ensures zero fabricated context)
- **Controls:** Non-obstructive top-bar status badge, quick pause, stop, and microphone mute.

### 6. `Cross-Device Session Manager` (`DeviceSessionManager.tsx`)
- **Device Registry:** Manages Laptop (current device), Phone (Pixel 9 Pro), and Tablet (iPad Air).
- **PRD Section 9.5 Profile Activation Rules:**
  - Enforces single profile per device.
  - Supports different profiles across separate devices under one account.
- **Session Handover:** Seamless transfer of active continuity between laptop and mobile.
- **Synchronization Indicators:** Real-time state (Synced, Buffering, Checkpointed, Offline).

---

## 🛠️ Build & Development Commands

```bash
# Install dependencies
npm install

# Start local dev server (http://localhost:5173)
npm run dev

# Run TypeScript typecheck and production build
npm run build

# Preview production build
npm run preview
```
