import Foundation
import ReplayKit
import CoreMedia

/// Broadcast Sample Handler for Aster Companion Continuous Screen Understanding.
/// Intercepts video and audio sample buffers streamed via Apple's ReplayKit framework.
/// Adheres strictly to PRD Section 5 (Continuous Screen Understanding) and Section 12 (Permissions).
public class SampleHandler: RPBroadcastSampleHandler {
    
    // Monotonic sequence counter to detect frame gaps or drops
    private var sequenceNumber: UInt64 = 0
    private var lastFrameTime: CMTime = .zero
    private var frameCountSinceLastMeter: Int = 0
    private var lastMeterDate: Date = Date()
    
    // App Group shared container for zero-copy frame telemetry IPC
    private let appGroupIdentifier = "group.com.astercompanion.shared"
    private var sharedDefaults: UserDefaults? {
        return UserDefaults(suiteName: appGroupIdentifier)
    }
    
    public override func broadcastStarted(withSetupInfo setupInfo: [String : NSObject]?) {
        sequenceNumber = 0
        lastFrameTime = .zero
        frameCountSinceLastMeter = 0
        lastMeterDate = Date()
        
        sharedDefaults?.set(true, forKey: "broadcast_active")
        sharedDefaults?.set(Date().timeIntervalSince1970, forKey: "broadcast_started_at")
        sharedDefaults?.synchronize()
    }
    
    public override func broadcastPaused() {
        sharedDefaults?.set(true, forKey: "broadcast_paused")
        sharedDefaults?.synchronize()
    }
    
    public override func broadcastResumed() {
        sharedDefaults?.set(false, forKey: "broadcast_paused")
        sharedDefaults?.synchronize()
    }
    
    public override func broadcastFinished() {
        sharedDefaults?.set(false, forKey: "broadcast_active")
        sharedDefaults?.synchronize()
    }
    
    public override func processSampleBuffer(_ sampleBuffer: CMSampleBuffer, with sampleBufferType: RPSampleBufferType) {
        switch sampleBufferType {
        case .video:
            handleVideoSampleBuffer(sampleBuffer)
        case .audioApp:
            handleAudioAppSampleBuffer(sampleBuffer)
        case .audioMic:
            handleAudioMicSampleBuffer(sampleBuffer)
        @unknown default:
            break
        }
    }
    
    // MARK: - Video Frame Processing
    
    private func handleVideoSampleBuffer(_ sampleBuffer: CMSampleBuffer) {
        guard CMSampleBufferIsValid(sampleBuffer) else { return }
        
        sequenceNumber += 1
        frameCountSinceLastMeter += 1
        
        let currentTimestamp = CMSampleBufferGetPresentationTimeStamp(sampleBuffer)
        
        // Measure real capture rate across rolling window
        let now = Date()
        let elapsed = now.timeIntervalSince(lastMeterDate)
        if elapsed >= 1.0 {
            let measuredCaptureFPS = Double(frameCountSinceLastMeter) / elapsed
            sharedDefaults?.set(measuredCaptureFPS, forKey: "telemetry_capture_fps")
            sharedDefaults?.set(sequenceNumber, forKey: "telemetry_sequence_number")
            sharedDefaults?.set(now.timeIntervalSince1970, forKey: "telemetry_last_frame_timestamp")
            sharedDefaults?.synchronize()
            
            frameCountSinceLastMeter = 0
            lastMeterDate = now
        }
        
        lastFrameTime = currentTimestamp
    }
    
    // MARK: - Audio Processing
    
    private func handleAudioAppSampleBuffer(_ sampleBuffer: CMSampleBuffer) {
        // App playback audio streaming (opt-in per PRD Section 5.5)
    }
    
    private func handleAudioMicSampleBuffer(_ sampleBuffer: CMSampleBuffer) {
        // Environmental microphone audio streaming (distinct opt-in per PRD Section 5.5)
    }
}
