# Aster Companion — iOS ReplayKit & ScreenCapture Architecture

## 1. Executive Summary & Purpose

The **Aster Companion Screen Awareness Subsystem** provides continuous, low-latency, privacy-centric visual and auditory comprehension of the user's active screen context across iOS and macOS.

Per **PRD v1.1** requirements:
- **Continuous Awareness**: User-started, visibly indicated, instantly paused/stopped/muted.
- **Strict Profile Isolation**: Guaranteed separation between companion profiles. No broadcast can stream without an active, verified profile ID; switching profiles terminates the active broadcast session immediately without context transfer.
- **Memory Ceiling Compliance**: Broadcast Upload Extensions on iOS operate under a strict **< 50MB RAM limit** enforced by Apple's Jetsam kernel monitor.
- **Perceptual Difference Hashing (dHash)**: Frame-by-frame 64-bit dHash computation eliminates up to 90% of redundant static frame transmissions, conserving battery, cellular data, and cloud inference costs.
- **Segregated Audio Opt-Ins**: Environmental microphone (`.audioMic`) and system playback (`.audioApp`) are strictly segregated and require explicit, separate user consent.

---

## 2. Directory Structure

```text
ios/AsterCompanion/ReplayKit/
├── AwarenessModels.swift           # Canonical packet envelopes, metadata, and telemetry schemas
├── PerceptualHash.swift            # Zero-allocation dHash & aHash perceptual algorithms on CVPixelBuffer
├── AppGroupIPC.swift               # Darwin notification & shared App Group state bridge
├── AwarenessTransportClient.swift  # WebSocket streaming & chunk upload client with backpressure control
├── SampleHandler.swift             # RPBroadcastSampleHandler extension implementation
├── ReplayKitController.swift       # Main application controller & RPSystemBroadcastPickerView manager
├── ScreenCaptureKitAdapter.swift   # macOS 12.3+ & Catalyst ScreenCaptureKit (SCStream) adapter
├── Tests/
│   └── ReplayKitTests.swift        # XCTest suite for hashing, serialization, and isolation
└── README.md                       # Comprehensive architectural documentation & Xcode configuration
```

---

## 3. Data Flow & Streaming Architecture

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant App as Aster Main App (ReplayKitController)
    participant IPC as App Group IPC (UserDefaults & Darwin)
    participant Ext as Broadcast Extension (SampleHandler)
    participant Transport as AwarenessTransportClient
    participant Supabase as Supabase Backend (/awareness-stream)

    User->>App: Tap "Start Screen Awareness"
    App->>App: Verify Active Profile & Auth Token
    App->>IPC: Write AwarenessSessionConfig
    App->>App: Trigger RPSystemBroadcastPickerView
    User->>Ext: Select Aster Extension & Start Broadcast

    Ext->>IPC: Read AwarenessSessionConfig & Verify Profile
    Ext->>Transport: Initialize WebSocket connection
    Transport->>Supabase: Handshake (session_start)
    Ext->>IPC: Post Darwin(.broadcastStarted)
    IPC->>App: Update state to .active

    loop Video Sampling (e.g., 3-5 FPS)
        Ext->>Ext: Receive CMSampleBuffer(.video)
        Ext->>Ext: Compute 64-bit dHash directly on CVPixelBuffer
        alt Hamming Distance <= 2 (Static Frame)
            Ext->>Ext: Suppress frame; increment static counter
            opt Every 5 static frames
                Ext->>Transport: Send static_heartbeat (no JPEG payload)
            end
        else Visual Change Detected (or 10th consecutive static frame)
            Ext->>Ext: Hardware-accelerated Metal downsample & JPEG compress
            Ext->>Transport: Send .frame packet (Base64 JPEG + SHA256 checksum)
            Transport->>Supabase: Ingest visual frame
        end
    end

    opt User Stops Broadcast via iOS Status Bar
        User->>Ext: Tap Red Status Bar Pill ("Stop")
        Ext->>Transport: Send session_end & disconnect
        Ext->>IPC: Post Darwin(.broadcastFinished)
        IPC->>App: Reset state to .idle
    end
```

---

## 4. Key Subsystem Implementations

### 4.1 SampleHandler.swift (RPBroadcastSampleHandler Subclass)
- Subclasses Apple's `RPBroadcastSampleHandler`.
- Wraps every sample buffer in an explicit `@autoreleasepool` block.
- Implements adaptive frame rate throttling (defaults to 3.0 FPS).
- Uses Apple's Metal-accelerated `CIContext` for downsampling to `maxResolutionDimension` (default 1280px) and JPEG compression.
- Actively polls resident memory via Mach kernel `mach_task_basic_info`. If RAM exceeds 42 MB, caches are cleared; if RAM reaches 46 MB, the extension terminates gracefully with a user-facing error rather than suffering an unhandled Jetsam crash.

### 4.2 PerceptualHash.swift (Zero-Allocation dHash)
- Evaluates a 9x8 luminance grid across the screen image directly from `CVPixelBuffer`.
- On YUV planar buffers (`kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange` / `FullRange`), it accesses the luminance plane (Plane 0) directly without color conversions.
- On packed 32-bit BGRA buffers, it uses ITU-R BT.601 integer coefficients: `Y = (299*R + 587*G + 114*B) / 1000`.
- Compares adjacent horizontal pixels: `pixel[x, y] > pixel[x + 1, y]`, producing 64 bits.
- Hamming distance is evaluated using hardware POPCNT (`nonzeroBitCount`).

### 4.3 AppGroupIPC.swift (Inter-Process Bridge)
- Shared container suite: `group.com.astercompanion.app`.
- Darwin notification center: `CFNotificationCenterGetDarwinNotifyCenter()`.
- Thread-safe access to session configurations, active profile isolation boundaries, and real-time telemetry metrics.

### 4.4 AwarenessTransportClient.swift (Resilient Transport)
- Primary transport: Secure WebSocket (`wss://<project>.supabase.co/functions/v1/awareness-stream`).
- Fallback: HTTP chunk upload to `/functions/v1/awareness-ingest`.
- Bounded backpressure queue (maximum 5 packets in memory).
- Drops non-keyframe visual frames during network congestion while guaranteeing delivery of keyframes, audio chunks, and session lifecycle packets.
- Employs Apple's `CryptoKit` to calculate SHA-256 payload checksums.

### 4.5 ReplayKitController.swift (Main App Coordinator)
- SwiftUI / UIKit coordinator conforming to `ObservableObject`.
- Programmatic trigger for `RPSystemBroadcastPickerView`.
- Robust detection of OS broadcast termination events via status bar polling and Darwin notifications.
- Exposes `@Published` telemetry (capture FPS, upload FPS, skipped frames, memory usage) for the UI Contextual Control Panel.

### 4.6 ScreenCaptureKitAdapter.swift (macOS & Mac Catalyst Support)
- Built on `ScreenCaptureKit` (`SCStream`) for macOS 12.3+ and Mac Catalyst 15.4+.
- Filters out Aster Companion's own application window to prevent infinite recursive mirroring.
- Supports display selection, cursor capture, and system audio loopback.
- Conforms to the unified `ScreenAwarenessProvider` protocol.

---

## 5. Xcode Target Configuration Guide

When building the native iOS application and extension on a macOS workstation:

### 5.1 Main App Target (`AsterCompanion`)
- **Bundle Identifier**: `com.astercompanion.app`
- **Capabilities**:
  - `App Groups`: Enable `group.com.astercompanion.app`
  - `Background Modes`: Audio, AirPlay, and Background fetch (for full-duplex voice)
- **Info.plist**:
  - `NSMicrophoneUsageDescription`: "Aster uses the microphone for conversational voice and environmental audio awareness when enabled."

### 5.2 Broadcast Upload Extension Target (`AsterCompanionReplayKitExtension`)
- **Template**: Broadcast Upload Extension
- **Bundle Identifier**: `com.astercompanion.app.AsterCompanion.ReplayKitExtension`
- **Principal Class**: `$(PRODUCT_MODULE_NAME).SampleHandler`
- **NSExtension**:
  ```xml
  <key>NSExtension</key>
  <dict>
      <key>NSExtensionPointIdentifier</key>
      <string>com.apple.broadcast-services-upload</string>
      <key>NSExtensionPrincipalClass</key>
      <string>$(PRODUCT_MODULE_NAME).SampleHandler</string>
  </dict>
  ```
- **Capabilities**:
  - `App Groups`: Enable `group.com.astercompanion.app`

### 5.3 macOS Desktop Target (ScreenCaptureKit)
- **Entitlements**:
  ```xml
  <key>com.apple.security.device.screen-recording</key>
  <true/>
  <key>com.apple.security.device.audio-input</key>
  <true/>
  ```

---

## 6. Verification and Testing

All unit tests in `Tests/ReplayKitTests.swift` validate:
1. Perceptual hashing accuracy on identical, slightly modified, and distinct frames.
2. Lossless JSON serialization of `AwarenessPacket` envelopes with ISO 8601 timestamps and checksums.
3. Profile isolation enforcement and cross-profile rejection.
4. App Group configuration persistence.
5. Mach kernel resident memory querying.
