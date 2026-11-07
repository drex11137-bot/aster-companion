//
//  SampleHandler.swift
//  AsterCompanion
//
//  Created for Aster Companion iOS & macOS Screen Awareness System.
//  Subclasses RPBroadcastSampleHandler to process screen video and audio buffers.
//  Strictly conforms to iOS Broadcast Upload Extension constraints (< 50MB RAM limit)
//  utilizing hardware-accelerated downsampled JPEG compression, perceptual difference
//  hashing (dHash) to eliminate static frames, and secure streaming to Supabase backend.
//

import Accelerate
import CoreImage
import CoreMedia
import CoreVideo
import Foundation
import ReplayKit

/// Primary entry point for the Aster Companion ReplayKit Broadcast Upload Extension.
public class SampleHandler: RPBroadcastSampleHandler, AwarenessTransportDelegate, @unchecked Sendable {

    // MARK: - Configuration & Transport

    private var config: AwarenessSessionConfig?
    private var transportClient: AwarenessTransportClient?
    private let ipc = AppGroupIPC.shared

    // MARK: - Frame Processing State

    private var lastProcessedFrameTime: CMTime = .zero
    private var lastPerceptualHash: UInt64?
    private var consecutiveStaticSkips: Int = 0
    private var totalFramesReceived: UInt64 = 0
    private var totalFramesProcessed: UInt64 = 0

    // Shared reusable CIContext for hardware-accelerated Metal JPEG encoding
    private lazy var ciContext: CIContext = {
        return CIContext(options: [
            .useSoftwareRenderer: false,
            .priorityRequestLow: true
        ])
    }()

    private let processingQueue = DispatchQueue(
        label: "com.astercompanion.replaykit.processor",
        qos: .userInteractive
    )

    // Critical memory safety ceiling for iOS extensions (42 MB warning threshold, 50 MB hard jetsam)
    private let memorySafetyLimitMB: Double = 42.0

    // MARK: - RPBroadcastSampleHandler Lifecycle

    public override func broadcastStarted(withSetupInfo setupInfo: [String: NSObject]?) {
        // 1. Retrieve configuration from shared App Group storage
        guard let sessionConfig = ipc.loadSessionConfig() else {
            let error = NSError(
                domain: "com.astercompanion.replaykit",
                code: 401,
                userInfo: [NSLocalizedDescriptionKey: AwarenessError.configurationMissing.localizedDescription]
            )
            finishBroadcastWithError(error)
            return
        }

        // 2. Validate Profile Isolation: Broadcast cannot proceed if no profile is active
        guard !sessionConfig.activeProfileId.isEmpty else {
            let error = NSError(
                domain: "com.astercompanion.replaykit",
                code: 403,
                userInfo: [NSLocalizedDescriptionKey: AwarenessError.noActiveProfile.localizedDescription]
            )
            finishBroadcastWithError(error)
            return
        }

        self.config = sessionConfig

        // 3. Initialize secure streaming transport to Supabase
        let client = AwarenessTransportClient(config: sessionConfig)
        client.delegate = self
        self.transportClient = client
        client.connect()

        // 4. Update shared IPC state
        ipc.setBroadcastActive(true, sessionId: sessionConfig.sessionId)
        ipc.postDarwinNotification(.broadcastStarted)

        // 5. Send session start lifecycle packet
        client.send(type: .sessionStart)

        // 6. Observe cross-process Darwin profile changes: abort immediately if profile changes
        ipc.addDarwinObserver(for: .profileChanged, observer: self) { [weak self] _ in
            self?.handleProfileChangedAcrossProcesses()
        }
    }

    public override func broadcastPaused() {
        ipc.setBroadcastPaused(true)
        ipc.postDarwinNotification(.broadcastPaused)
        transportClient?.send(type: .sessionPause)
    }

    public override func broadcastResumed() {
        ipc.setBroadcastPaused(false)
        ipc.postDarwinNotification(.broadcastResumed)
        transportClient?.send(type: .sessionResume)
    }

    public override func broadcastFinished() {
        ipc.removeDarwinObserver(self)

        // Flush session end packet and clean up
        transportClient?.send(type: .sessionEnd)
        transportClient?.disconnect()
        transportClient = nil

        ipc.setBroadcastActive(false)
        ipc.postDarwinNotification(.broadcastFinished)
        ipc.clearSessionConfig()
    }

    // MARK: - CMSampleBuffer Processing

    public override func processSampleBuffer(
        _ sampleBuffer: CMSampleBuffer,
        with sampleBufferType: RPSampleBufferType
    ) {
        // Enforce autoreleasepool around every single sample buffer invocation
        // to prevent accumulation of autoreleased temporary objects in extension memory
        autoreleasepool {
            guard let config = self.config else { return }

            // Guard against operating system memory limits
            let currentRAM = AwarenessTransportClient.getResidentMemoryMB()
            if currentRAM >= memorySafetyLimitMB {
                handleMemoryPressure(currentMB: currentRAM)
                return
            }

            switch sampleBufferType {
            case .video:
                processVideoBuffer(sampleBuffer, config: config)
            case .audioApp:
                if config.appAudioOptIn {
                    processAudioBuffer(sampleBuffer, sourceType: .appAudio)
                }
            case .audioMic:
                if config.micOptIn {
                    processAudioBuffer(sampleBuffer, sourceType: .micAudio)
                }
            @unknown default:
                break
            }
        }
    }

    // MARK: - Video Processing & Perceptual Hashing

    private func processVideoBuffer(_ sampleBuffer: CMSampleBuffer, config: AwarenessSessionConfig) {
        totalFramesReceived += 1

        let presentationTime = CMSampleBufferGetPresentationTimeStamp(sampleBuffer)
        if lastProcessedFrameTime != .zero {
            let elapsed = CMTimeGetSeconds(CMTimeSubtract(presentationTime, lastProcessedFrameTime))
            let minimumInterval = 1.0 / max(config.targetFrameRate, 0.5)

            // Adaptive rate limiting: drop incoming frame if interval has not elapsed
            if elapsed < minimumInterval {
                return
            }
        }

        guard let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else {
            return
        }

        // 1. Compute 64-bit perceptual difference hash (dHash) directly on pixel buffer
        guard let currentHash = PerceptualHash.computeDHash(from: pixelBuffer) else {
            return
        }

        let isStaticFrame: Bool
        let hammingDistance: Int

        if let prevHash = lastPerceptualHash {
            hammingDistance = PerceptualHash.hammingDistance(currentHash, prevHash)
            isStaticFrame = (hammingDistance <= config.staticSkipThresholdBits)
        } else {
            // First frame in session is always a keyframe
            hammingDistance = 64
            isStaticFrame = false
        }

        // 2. Evaluate static frame suppression
        if isStaticFrame && consecutiveStaticSkips < config.maxConsecutiveStaticSkips {
            consecutiveStaticSkips += 1
            lastProcessedFrameTime = presentationTime

            // Send periodic lightweight heartbeat without image payload every 5 static frames
            if consecutiveStaticSkips % 5 == 0 {
                let frameMeta = FrameMetadata(
                    width: CVPixelBufferGetWidth(pixelBuffer),
                    height: CVPixelBufferGetHeight(pixelBuffer),
                    format: "jpeg",
                    perceptualHash: PerceptualHash.hexString(from: currentHash),
                    hammingDistance: hammingDistance,
                    isKeyframe: false,
                    skippedSinceLastKeyframe: consecutiveStaticSkips,
                    captureFPS: config.targetFrameRate,
                    targetFPS: config.targetFrameRate
                )
                transportClient?.send(type: .staticHeartbeat, frame: frameMeta)
            }
            return
        }

        // 3. Frame has visual changes or keyframe interval has arrived: compress & upload
        let isKeyframe = (consecutiveStaticSkips >= config.maxConsecutiveStaticSkips || lastPerceptualHash == nil)
        let skippedCount = consecutiveStaticSkips

        // Downsample and compress to JPEG using hardware-accelerated CIContext
        guard let (jpegData, outputWidth, outputHeight) = downsampleAndCompress(
            pixelBuffer: pixelBuffer,
            maxDimension: config.maxResolutionDimension,
            quality: config.jpegCompressionQuality
        ) else {
            return
        }

        let frameMeta = FrameMetadata(
            width: outputWidth,
            height: outputHeight,
            format: "jpeg",
            perceptualHash: PerceptualHash.hexString(from: currentHash),
            hammingDistance: hammingDistance,
            isKeyframe: isKeyframe,
            skippedSinceLastKeyframe: skippedCount,
            captureFPS: config.targetFrameRate,
            targetFPS: config.targetFrameRate
        )

        transportClient?.send(
            type: .frame,
            frame: frameMeta,
            payloadData: jpegData
        )

        // Update state
        lastPerceptualHash = currentHash
        consecutiveStaticSkips = 0
        lastProcessedFrameTime = presentationTime
        totalFramesProcessed += 1
    }

    // MARK: - Hardware-Accelerated Image Downsampling & JPEG Compression

    private func downsampleAndCompress(
        pixelBuffer: CVPixelBuffer,
        maxDimension: Int,
        quality: Double
    ) -> (data: Data, width: Int, height: Int)? {
        let srcWidth = CVPixelBufferGetWidth(pixelBuffer)
        let srcHeight = CVPixelBufferGetHeight(pixelBuffer)
        guard srcWidth > 0 && srcHeight > 0 else { return nil }

        var ciImage = CIImage(cvPixelBuffer: pixelBuffer)

        // Calculate downsampled aspect ratio
        let maxSrc = max(srcWidth, srcHeight)
        let scale: CGFloat
        let targetWidth: Int
        let targetHeight: Int

        if maxSrc > maxDimension {
            scale = CGFloat(maxDimension) / CGFloat(maxSrc)
            targetWidth = Int(CGFloat(srcWidth) * scale)
            targetHeight = Int(CGFloat(srcHeight) * scale)
            ciImage = ciImage.transformed(by: CGAffineTransform(scaleX: scale, y: scale))
        } else {
            scale = 1.0
            targetWidth = srcWidth
            targetHeight = srcHeight
        }

        let colorSpace = CGColorSpaceCreateDeviceRGB()
        let options: [CIImageRepresentationOption: Any] = [
            kCGImageDestinationLossyFactor as CIImageRepresentationOption: quality
        ]

        guard let jpegData = ciContext.jpegRepresentation(
            of: ciImage,
            colorSpace: colorSpace,
            options: options
        ) else {
            return nil
        }

        return (jpegData, targetWidth, targetHeight)
    }

    // MARK: - Audio Buffer Processing

    private func processAudioBuffer(_ sampleBuffer: CMSampleBuffer, sourceType: AudioSourceType) {
        guard let formatDesc = CMSampleBufferGetFormatDescription(sampleBuffer),
              let asbd = CMAudioFormatDescriptionGetStreamBasicDescription(formatDesc)?.pointee else {
            return
        }

        let numSamples = CMSampleBufferGetNumSamples(sampleBuffer)
        guard numSamples > 0 else { return }

        let sampleRate = asbd.mSampleRate
        let channels = Int(asbd.mChannelsPerFrame)
        let durationMs = (Double(numSamples) / max(sampleRate, 1.0)) * 1000.0

        // Extract raw audio data from CMBlockBuffer
        guard let blockBuffer = CMSampleBufferGetDataBuffer(sampleBuffer) else { return }
        var totalLength = 0
        var dataPointer: UnsafeMutablePointer<Int8>?

        let status = CMBlockBufferGetDataPointer(
            blockBuffer,
            atOffset: 0,
            lengthAtOffsetOut: nil,
            totalLengthOut: &totalLength,
            dataPointerOut: &dataPointer
        )

        guard status == kCMBlockBufferNoErr, let ptr = dataPointer, totalLength > 0 else {
            return
        }

        let rawAudioData = Data(bytes: ptr, count: totalLength)

        let audioMeta = AudioMetadata(
            sourceType: sourceType,
            sampleRate: sampleRate,
            channelCount: channels,
            format: "pcm_s16le",
            sampleCount: numSamples,
            durationMs: durationMs
        )

        transportClient?.send(
            type: .audioChunk,
            audio: audioMeta,
            payloadData: rawAudioData
        )
    }

    // MARK: - Memory Pressure & Profile Isolation Guards

    private func handleMemoryPressure(currentMB: Double) {
        // Emergency memory mitigation: clear reusable context caches
        ciContext.clearCaches()

        ipc.recordBroadcastError("High memory pressure: \(String(format: "%.1f", currentMB))MB")

        // If RAM still exceeds 46 MB, terminate cleanly rather than getting killed ungracefully by jetsam
        if currentMB >= 46.0 {
            let error = NSError(
                domain: "com.astercompanion.replaykit",
                code: 429,
                userInfo: [NSLocalizedDescriptionKey: AwarenessError.memoryPressureExceeded(currentMB: currentMB, limitMB: 50.0).localizedDescription]
            )
            finishBroadcastWithError(error)
        }
    }

    private func handleProfileChangedAcrossProcesses() {
        guard let currentConfig = config else { return }
        let activeProfile = ipc.getActiveProfileId()

        if activeProfile != currentConfig.activeProfileId {
            print("[SampleHandler] Active profile changed to \(activeProfile ?? "none"). Terminating broadcast.")
            let error = NSError(
                domain: "com.astercompanion.replaykit",
                code: 403,
                userInfo: [NSLocalizedDescriptionKey: "Active profile switched. Broadcast terminated to preserve profile isolation."]
            )
            finishBroadcastWithError(error)
        }
    }

    // MARK: - AwarenessTransportDelegate

    public func transportDidConnect(_ transport: AwarenessTransportClient) {
        print("[SampleHandler] Transport connected to Supabase.")
    }

    public func transportDidDisconnect(_ transport: AwarenessTransportClient, error: Error?) {
        if let error = error {
            print("[SampleHandler] Transport disconnected with error: \(error.localizedDescription)")
            ipc.recordBroadcastError("Transport disconnected: \(error.localizedDescription)")
        }
    }

    public func transport(_ transport: AwarenessTransportClient, didAcknowledgeSequence sequenceNumber: UInt64) {
        // Backend received packet
    }

    public func transport(_ transport: AwarenessTransportClient, didDropPacket packet: AwarenessPacket, reason: String) {
        print("[SampleHandler] Dropped packet seq=\(packet.sequenceNumber) due to: \(reason)")
    }

    public func transport(_ transport: AwarenessTransportClient, didUpdateTelemetry telemetry: AwarenessTelemetry) {
        // Publish live telemetry into App Group for main app UI contextual control panel
        ipc.publishTelemetry(telemetry)
        ipc.postDarwinNotification(.telemetryUpdated)
    }
}
