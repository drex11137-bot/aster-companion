import SwiftUI

public enum AwarenessStatus: String, Codable {
    case idle = "Idle"
    case active = "Active"
    case paused = "Paused"
    case disconnected = "Disconnected"
    
    public var color: Color {
        switch self {
        case .idle: return AsterTheme.mutedText
        case .active: return AsterTheme.onlineGreen
        case .paused: return AsterTheme.warmAmber
        case .disconnected: return AsterTheme.destructiveRed
        }
    }
}

public struct AwarenessTelemetry: Codable, Equatable {
    public var status: AwarenessStatus
    public var captureFPS: Double
    public var uploadFPS: Double
    public var ingestFPS: Double
    public var analysisFPS: Double
    public var latencyMs: Double
    public var continuityRatio: Double
    public var gapsDetected: Int
    public var isScreenPaused: Bool
    public var isAudioMuted: Bool
    public var totalFramesProcessed: Int
    public var lastUpdated: Date
    
    public init(
        status: AwarenessStatus = .active,
        captureFPS: Double = 60.0,
        uploadFPS: Double = 30.0,
        ingestFPS: Double = 30.0,
        analysisFPS: Double = 5.0,
        latencyMs: Double = 142.0,
        continuityRatio: Double = 1.0,
        gapsDetected: Int = 0,
        isScreenPaused: Bool = false,
        isAudioMuted: Bool = false,
        totalFramesProcessed: Int = 1845,
        lastUpdated: Date = Date()
    ) {
        self.status = status
        self.captureFPS = captureFPS
        self.uploadFPS = uploadFPS
        self.ingestFPS = ingestFPS
        self.analysisFPS = analysisFPS
        self.latencyMs = latencyMs
        self.continuityRatio = continuityRatio
        self.gapsDetected = gapsDetected
        self.isScreenPaused = isScreenPaused
        self.isAudioMuted = isAudioMuted
        self.totalFramesProcessed = totalFramesProcessed
        self.lastUpdated = lastUpdated
    }
}
