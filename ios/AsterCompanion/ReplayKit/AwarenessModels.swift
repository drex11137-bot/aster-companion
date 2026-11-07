//
//  AwarenessModels.swift
//  AsterCompanion
//
//  Created for Aster Companion iOS & macOS Screen Awareness System.
//  Strictly adheres to PRD v1.1: profile isolation, monotonic sequence tracking,
//  perceptual hashing, audio opt-in segregation, and telemetry transparency.
//

import Foundation

// MARK: - Capture Source

/// The platform capture mechanism producing awareness packets.
public enum CaptureSource: String, Codable, Sendable {
    case iosReplayKitExtension = "ios_replaykit_extension"
    case macosScreenCaptureKit = "macos_screencapturekit"
    case browserCapture = "browser_capture"
}

// MARK: - Packet Type

/// The classification of data or lifecycle events in the awareness stream.
public enum AwarenessPacketType: String, Codable, Sendable {
    case sessionStart = "session_start"
    case frame = "frame"
    case staticHeartbeat = "static_heartbeat"
    case audioChunk = "audio_chunk"
    case sessionPause = "session_pause"
    case sessionResume = "session_resume"
    case sessionEnd = "session_end"
}

// MARK: - Consent Metadata

/// Granular, per-session user consent indicators.
/// Must never assume consent for audio or other-app playback without explicit opt-in.
public struct AwarenessConsentMetadata: Codable, Sendable, Equatable {
    public let screenCaptureGranted: Bool
    public let micAudioGranted: Bool
    public let appAudioPlaybackGranted: Bool
    public let consentTimestamp: Date

    public init(
        screenCaptureGranted: Bool = true,
        micAudioGranted: Bool = false,
        appAudioPlaybackGranted: Bool = false,
        consentTimestamp: Date = Date()
    ) {
        self.screenCaptureGranted = screenCaptureGranted
        self.micAudioGranted = micAudioGranted
        self.appAudioPlaybackGranted = appAudioPlaybackGranted
        self.consentTimestamp = consentTimestamp
    }
}

// MARK: - Frame Metadata

/// Visual frame metrics, dimensions, compression format, and perceptual hash metadata.
public struct FrameMetadata: Codable, Sendable, Equatable {
    public let width: Int
    public let height: Int
    public let format: String // "jpeg" or "yuv"
    public let perceptualHash: String // 64-bit difference hash formatted as hex string
    public let hammingDistance: Int // Distance from immediately preceding frame
    public let isKeyframe: Bool // Forced sync keyframe vs intermediate change frame
    public let skippedSinceLastKeyframe: Int // Count of static frames suppressed prior to this frame
    public let captureFPS: Double
    public let targetFPS: Double

    public init(
        width: Int,
        height: Int,
        format: String = "jpeg",
        perceptualHash: String,
        hammingDistance: Int,
        isKeyframe: Bool,
        skippedSinceLastKeyframe: Int,
        captureFPS: Double,
        targetFPS: Double
    ) {
        self.width = width
        self.height = height
        self.format = format
        self.perceptualHash = perceptualHash
        self.hammingDistance = hammingDistance
        self.isKeyframe = isKeyframe
        self.skippedSinceLastKeyframe = skippedSinceLastKeyframe
        self.captureFPS = captureFPS
        self.targetFPS = targetFPS
    }
}

// MARK: - Audio Source Type

/// Segregated audio channel types. Environmental mic and system playback are distinct opt-ins.
public enum AudioSourceType: String, Codable, Sendable {
    case micAudio = "mic_audio"
    case appAudio = "app_audio"
}

// MARK: - Audio Metadata

/// Audio stream properties and sample specifications.
public struct AudioMetadata: Codable, Sendable, Equatable {
    public let sourceType: AudioSourceType
    public let sampleRate: Double
    public let channelCount: Int
    public let format: String // e.g. "pcm_f32le", "aac", "opus"
    public let sampleCount: Int
    public let durationMs: Double

    public init(
        sourceType: AudioSourceType,
        sampleRate: Double,
        channelCount: Int,
        format: String = "pcm_f32le",
        sampleCount: Int,
        durationMs: Double
    ) {
        self.sourceType = sourceType
        self.sampleRate = sampleRate
        self.channelCount = channelCount
        self.format = format
        self.sampleCount = sampleCount
        self.durationMs = durationMs
    }
}

// MARK: - Awareness Packet Envelope

/// Canonical packet format sent across WebSocket or HTTP chunk upload to Supabase backend.
/// Strictly enforces profile isolation, device attribution, and monotonic sequencing.
public struct AwarenessPacket: Codable, Sendable, Equatable {
    /// Globally unique, immutable packet identifier.
    public let id: UUID

    /// Monotonically increasing sequence number per device & session.
    /// Backend uses this to detect packet loss, reordering, and duplicate delivery.
    public let sequenceNumber: UInt64

    /// High-precision ISO 8601 UTC timestamp.
    public let timestamp: Date

    /// Epoch millisecond timestamp for low-latency synchronization and jitter measurement.
    public let timestampEpochMs: Int64

    /// Hardware capture source.
    public let source: CaptureSource

    /// Unique identifier for the capturing device (persisted in Keychain).
    public let deviceId: String

    /// Unique session identifier generated at broadcast start.
    public let sessionId: String

    /// Active companion profile ID. ReplayKit must terminate if active profile changes.
    public let profileId: String

    /// Explicit user consent flags validated at capture time.
    public let consent: AwarenessConsentMetadata

    /// Packet payload classification.
    public let type: AwarenessPacketType

    /// Visual frame metadata if packet carries or describes a video frame.
    public let frame: FrameMetadata?

    /// Audio sample metadata if packet carries audio.
    public let audio: AudioMetadata?

    /// Base64-encoded compressed image or audio payload (optional for heartbeat packets).
    public let payloadBase64: String?

    /// Cryptographic SHA-256 checksum of raw unencoded payload for tamper detection.
    public let payloadChecksum: String?

    public init(
        id: UUID = UUID(),
        sequenceNumber: UInt64,
        timestamp: Date = Date(),
        timestampEpochMs: Int64 = Int64(Date().timeIntervalSince1970 * 1000),
        source: CaptureSource,
        deviceId: String,
        sessionId: String,
        profileId: String,
        consent: AwarenessConsentMetadata,
        type: AwarenessPacketType,
        frame: FrameMetadata? = nil,
        audio: AudioMetadata? = nil,
        payloadBase64: String? = nil,
        payloadChecksum: String? = nil
    ) {
        self.id = id
        self.sequenceNumber = sequenceNumber
        self.timestamp = timestamp
        self.timestampEpochMs = timestampEpochMs
        self.source = source
        self.deviceId = deviceId
        self.sessionId = sessionId
        self.profileId = profileId
        self.consent = consent
        self.type = type
        self.frame = frame
        self.audio = audio
        self.payloadBase64 = payloadBase64
        self.payloadChecksum = payloadChecksum
    }
}

// MARK: - Awareness Session Configuration

/// Configuration passed from the main application to the ReplayKit extension via App Group storage.
public struct AwarenessSessionConfig: Codable, Sendable, Equatable {
    public let activeProfileId: String
    public let deviceId: String
    public let sessionId: String
    public let supabaseUrl: URL
    public let supabaseAuthToken: String
    public let micOptIn: Bool
    public let appAudioOptIn: Bool
    public let targetFrameRate: Double
    public let maxResolutionDimension: Int
    public let jpegCompressionQuality: Double
    public let staticSkipThresholdBits: Int
    public let maxConsecutiveStaticSkips: Int

    public init(
        activeProfileId: String,
        deviceId: String,
        sessionId: String = UUID().uuidString,
        supabaseUrl: URL,
        supabaseAuthToken: String,
        micOptIn: Bool = false,
        appAudioOptIn: Bool = false,
        targetFrameRate: Double = 3.0,
        maxResolutionDimension: Int = 1280,
        jpegCompressionQuality: Double = 0.70,
        staticSkipThresholdBits: Int = 2,
        maxConsecutiveStaticSkips: Int = 10
    ) {
        self.activeProfileId = activeProfileId
        self.deviceId = deviceId
        self.sessionId = sessionId
        self.supabaseUrl = supabaseUrl
        self.supabaseAuthToken = supabaseAuthToken
        self.micOptIn = micOptIn
        self.appAudioOptIn = appAudioOptIn
        self.targetFrameRate = targetFrameRate
        self.maxResolutionDimension = maxResolutionDimension
        self.jpegCompressionQuality = jpegCompressionQuality
        self.staticSkipThresholdBits = staticSkipThresholdBits
        self.maxConsecutiveStaticSkips = maxConsecutiveStaticSkips
    }
}

// MARK: - Awareness State

/// The runtime awareness operating state displayed in the UI contextual control panel.
public enum AwarenessState: Equatable, Sendable {
    case idle
    case starting(sessionId: String, profileId: String)
    case active(sessionId: String, profileId: String, startedAt: Date)
    case paused(sessionId: String, profileId: String)
    case stopping(sessionId: String)
    case error(AwarenessError)
}

// MARK: - Awareness Errors

/// Typed errors covering permission denials, profile mismatches, OS restrictions, and network failures.
public enum AwarenessError: LocalizedError, Equatable, Sendable {
    case unauthenticated
    case noActiveProfile
    case profileMismatch(expected: String, actual: String)
    case permissionDenied(String)
    case memoryPressureExceeded(currentMB: Double, limitMB: Double)
    case broadcastTerminatedByOS
    case networkUnavailable(String)
    case payloadEncodingFailed(String)
    case configurationMissing
    case unknown(String)

    public var errorDescription: String? {
        switch self {
        case .unauthenticated:
            return "User session is unauthenticated. Please sign in to activate screen awareness."
        case .noActiveProfile:
            return "No active companion profile is selected. Profile isolation requires an active profile."
        case .profileMismatch(let expected, let actual):
            return "Security violation: active profile '\(actual)' does not match session profile '\(expected)'."
        case .permissionDenied(let reason):
            return "Screen capture permission denied: \(reason)"
        case .memoryPressureExceeded(let currentMB, let limitMB):
            return "Memory limit exceeded: \(String(format: "%.1f", currentMB))MB / \(String(format: "%.1f", limitMB))MB limit."
        case .broadcastTerminatedByOS:
            return "The operating system stopped the broadcast session."
        case .networkUnavailable(let reason):
            return "Network connection to Supabase failed: \(reason)"
        case .payloadEncodingFailed(let reason):
            return "Failed to compress or encode frame: \(reason)"
        case .configurationMissing:
            return "Broadcast extension configuration missing in App Group shared storage."
        case .unknown(let message):
            return "Screen awareness error: \(message)"
        }
    }
}

// MARK: - Telemetry Metrics

/// Live telemetry metrics reported to the contextual control panel.
public struct AwarenessTelemetry: Codable, Sendable, Equatable {
    public var captureFPS: Double
    public var uploadFPS: Double
    public var skippedFramesTotal: UInt64
    public var uploadedFramesTotal: UInt64
    public var totalBytesUploaded: UInt64
    public var memoryUsageMB: Double
    public var lastSequenceNumber: UInt64
    public var lastEventTimestamp: Date?
    public var isConnected: Bool

    public init(
        captureFPS: Double = 0.0,
        uploadFPS: Double = 0.0,
        skippedFramesTotal: UInt64 = 0,
        uploadedFramesTotal: UInt64 = 0,
        totalBytesUploaded: UInt64 = 0,
        memoryUsageMB: Double = 0.0,
        lastSequenceNumber: UInt64 = 0,
        lastEventTimestamp: Date? = nil,
        isConnected: Bool = false
    ) {
        self.captureFPS = captureFPS
        self.uploadFPS = uploadFPS
        self.skippedFramesTotal = skippedFramesTotal
        self.uploadedFramesTotal = uploadedFramesTotal
        self.totalBytesUploaded = totalBytesUploaded
        self.memoryUsageMB = memoryUsageMB
        self.lastSequenceNumber = lastSequenceNumber
        self.lastEventTimestamp = lastEventTimestamp
        self.isConnected = isConnected
    }
}
