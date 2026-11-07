//
//  ScreenCaptureKitAdapter.swift
//  AsterCompanion
//
//  Created for Aster Companion iOS & macOS Screen Awareness System.
//  Integrates Apple's macOS ScreenCaptureKit (SCStream) for laptop and desktop
//  screen awareness, with window-exclusion filters, adaptive framerates,
//  perceptual hashing (dHash) to skip static frames, and Supabase streaming.
//

import Combine
import CoreGraphics
import CoreMedia
import CoreVideo
import Foundation

#if os(macOS) || targetEnvironment(macCatalyst)
import ScreenCaptureKit
#endif

#if canImport(AppKit)
import AppKit
#endif

// MARK: - Unified Screen Awareness Provider Protocol

/// Common protocol implemented by ReplayKitController (iOS) and ScreenCaptureKitAdapter (macOS).
@MainActor
public protocol ScreenAwarenessProvider: AnyObject {
    var state: AwarenessState { get }
    var telemetry: AwarenessTelemetry { get }
    var activeProfileId: String? { get }
    var isSupportedOnCurrentPlatform: Bool { get }

    func startAwareness(
        config: AwarenessSessionConfig,
        excludedWindowTitles: [String]
    ) async throws

    func pauseAwareness()
    func resumeAwareness()
    func stopAwareness()
}

// MARK: - ScreenCaptureKit Adapter Implementation

/// Production adapter integrating ScreenCaptureKit for macOS and Mac Catalyst screen awareness.
@MainActor
public final class ScreenCaptureKitAdapter: NSObject, ObservableObject, ScreenAwarenessProvider {

    // MARK: - Published State

    @Published public private(set) var state: AwarenessState = .idle
    @Published public private(set) var telemetry: AwarenessTelemetry = AwarenessTelemetry()
    @Published public private(set) var activeProfileId: String?
    @Published public private(set) var isSupportedOnCurrentPlatform: Bool = false
    @Published public private(set) var lastErrorMessage: String?

    // MARK: - Internal Dependencies

    private var sessionConfig: AwarenessSessionConfig?
    private var transportClient: AwarenessTransportClient?
    private let ipc = AppGroupIPC.shared

    #if os(macOS) || targetEnvironment(macCatalyst)
    private var activeStream: SCStream?
    private var streamDelegateHandler: SCStreamDelegateHandler?
    private var streamOutputHandler: SCStreamOutputHandler?
    #endif

    // MARK: - Initialization

    public override init() {
        super.init()

        #if os(macOS) || targetEnvironment(macCatalyst)
        if #available(macOS 12.3, macCatalyst 15.4, *) {
            self.isSupportedOnCurrentPlatform = true
        } else {
            self.isSupportedOnCurrentPlatform = false
        }
        #else
        self.isSupportedOnCurrentPlatform = false
        #endif
    }

    // MARK: - Permissions Preflight

    /// Checks whether macOS Screen Recording permission has been granted by the user.
    public static func checkScreenRecordingPermission() -> Bool {
        #if os(macOS)
        return CGPreflightScreenCaptureAccess()
        #else
        return true
        #endif
    }

    /// Requests macOS Screen Recording permission, prompting the system permission dialog.
    public static func requestScreenRecordingPermission() -> Bool {
        #if os(macOS)
        return CGRequestScreenCaptureAccess()
        #else
        return true
        #endif
    }

    // MARK: - ScreenAwarenessProvider Lifecycle

    /// Initializes and starts continuous screen awareness on macOS via ScreenCaptureKit.
    public func startAwareness(
        config: AwarenessSessionConfig,
        excludedWindowTitles: [String] = ["Aster Companion", "Aster"]
    ) async throws {
        // 1. Strict Profile Isolation Check
        guard !config.activeProfileId.isEmpty else {
            let error = AwarenessError.noActiveProfile
            self.state = .error(error)
            throw error
        }

        #if os(macOS) || targetEnvironment(macCatalyst)
        guard #available(macOS 12.3, macCatalyst 15.4, *) else {
            let error = AwarenessError.permissionDenied("ScreenCaptureKit requires macOS 12.3+ or Mac Catalyst 15.4+.")
            self.state = .error(error)
            throw error
        }

        // 2. Permissions validation
        #if os(macOS)
        guard Self.checkScreenRecordingPermission() else {
            _ = Self.requestScreenRecordingPermission()
            let error = AwarenessError.permissionDenied("Screen recording permission is required in macOS System Settings.")
            self.state = .error(error)
            throw error
        }
        #endif

        self.sessionConfig = config
        self.activeProfileId = config.activeProfileId
        self.state = .starting(sessionId: config.sessionId, profileId: config.activeProfileId)

        // 3. Initialize transport client
        let client = AwarenessTransportClient(config: config)
        self.transportClient = client
        client.connect()
        client.send(type: .sessionStart)

        do {
            // 4. Retrieve available displays and windows
            let shareableContent = try await SCShareableContent.excludingDesktopWindows(
                false,
                onScreenWindowsOnly: true
            )

            guard let primaryDisplay = shareableContent.displays.first else {
                throw AwarenessError.unknown("No active display found for screen awareness capture.")
            }

            // 5. Exclude Aster Companion's own windows to avoid infinite feedback mirroring
            var windowsToExclude: [SCWindow] = []
            #if os(macOS)
            let ownPID = NSRunningApplication.current.processIdentifier
            windowsToExclude = shareableContent.windows.filter { window in
                window.owningApplication?.processID == ownPID ||
                excludedWindowTitles.contains(where: { (window.title ?? "").contains($0) })
            }
            #endif

            let contentFilter = SCContentFilter(
                display: primaryDisplay,
                excludingWindows: windowsToExclude
            )

            // 6. Configure capture stream
            let streamConfig = SCStreamConfiguration()
            streamConfig.width = min(primaryDisplay.width, config.maxResolutionDimension)
            let aspect = Double(primaryDisplay.height) / Double(max(primaryDisplay.width, 1))
            streamConfig.height = Int(Double(streamConfig.width) * aspect)
            streamConfig.pixelFormat = kCVPixelFormatType_32BGRA
            streamConfig.minimumFrameInterval = CMTime(value: 1, timescale: CMTimeScale(max(config.targetFrameRate, 1.0)))
            streamConfig.showsCursor = true
            streamConfig.scalesToFit = true

            // Optional audio capture
            if config.appAudioOptIn {
                streamConfig.capturesAudio = true
                streamConfig.sampleRate = 48000
                streamConfig.channelCount = 2
            }

            // 7. Initialize SCStream
            let stream = SCStream(filter: contentFilter, configuration: streamConfig, delegate: nil)

            let delegateHandler = SCStreamDelegateHandler(adapter: self)
            stream.delegate = delegateHandler
            self.streamDelegateHandler = delegateHandler

            let outputHandler = SCStreamOutputHandler(
                config: config,
                transportClient: client
            )
            self.streamOutputHandler = outputHandler

            try stream.addStreamOutput(
                outputHandler,
                type: .screen,
                sampleHandlerQueue: DispatchQueue(label: "com.astercompanion.screencapture.screen", qos: .userInteractive)
            )

            if config.appAudioOptIn {
                try stream.addStreamOutput(
                    outputHandler,
                    type: .audio,
                    sampleHandlerQueue: DispatchQueue(label: "com.astercompanion.screencapture.audio", qos: .userInteractive)
                )
            }

            try await stream.startCapture()
            self.activeStream = stream
            self.state = .active(sessionId: config.sessionId, profileId: config.activeProfileId, startedAt: Date())

        } catch {
            client.send(type: .sessionEnd)
            client.disconnect()
            self.transportClient = nil
            let awarenessError = (error as? AwarenessError) ?? AwarenessError.unknown(error.localizedDescription)
            self.state = .error(awarenessError)
            self.lastErrorMessage = awarenessError.localizedDescription
            throw awarenessError
        }

        #else
        let error = AwarenessError.unknown("ScreenCaptureKit is unavailable on this device.")
        self.state = .error(error)
        throw error
        #endif
    }

    /// Pauses screen capture stream.
    public func pauseAwareness() {
        guard case .active(let sessionId, let profileId, _) = state else { return }
        transportClient?.send(type: .sessionPause)
        self.state = .paused(sessionId: sessionId, profileId: profileId)
    }

    /// Resumes screen capture stream.
    public func resumeAwareness() {
        guard case .paused(let sessionId, let profileId) = state else { return }
        transportClient?.send(type: .sessionResume)
        self.state = .active(sessionId: sessionId, profileId: profileId, startedAt: Date())
    }

    /// Stops screen capture stream cleanly and flushes transport.
    public func stopAwareness() {
        #if os(macOS) || targetEnvironment(macCatalyst)
        if #available(macOS 12.3, macCatalyst 15.4, *) {
            if let stream = activeStream {
                Task {
                    try? await stream.stopCapture()
                }
                self.activeStream = nil
            }
        }
        #endif

        transportClient?.send(type: .sessionEnd)
        transportClient?.disconnect()
        transportClient = nil
        streamOutputHandler = nil
        streamDelegateHandler = nil
        sessionConfig = nil

        self.state = .idle
        self.telemetry = AwarenessTelemetry()
    }

    // MARK: - Internal Delegate Handlers

    fileprivate func handleStreamStopped(error: Error?) {
        if let error = error {
            let msg = error.localizedDescription
            self.lastErrorMessage = msg
            self.state = .error(.unknown("Stream stopped unexpectedly: \(msg)"))
        } else {
            self.state = .idle
        }
        stopAwareness()
    }
}

// MARK: - ScreenCaptureKit Stream Output Handler

#if os(macOS) || targetEnvironment(macCatalyst)
@available(macOS 12.3, macCatalyst 15.4, *)
private final class SCStreamOutputHandler: NSObject, SCStreamOutput, @unchecked Sendable {

    private let config: AwarenessSessionConfig
    private let transportClient: AwarenessTransportClient
    private var lastPerceptualHash: UInt64?
    private var consecutiveStaticSkips: Int = 0

    private lazy var ciContext: CIContext = {
        return CIContext(options: [.useSoftwareRenderer: false])
    }()

    init(config: AwarenessSessionConfig, transportClient: AwarenessTransportClient) {
        self.config = config
        self.transportClient = transportClient
        super.init()
    }

    func stream(_ stream: SCStream, didOutputSampleBuffer sampleBuffer: CMSampleBuffer, of type: SCStreamOutputType) {
        autoreleasepool {
            switch type {
            case .screen:
                processScreenSample(sampleBuffer)
            case .audio:
                processAudioSample(sampleBuffer)
            @unknown default:
                break
            }
        }
    }

    private func processScreenSample(_ sampleBuffer: CMSampleBuffer) {
        guard let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }

        // Compute perceptual difference hash
        guard let currentHash = PerceptualHash.computeDHash(from: pixelBuffer) else { return }

        let hammingDistance: Int
        let isStatic: Bool

        if let prev = lastPerceptualHash {
            hammingDistance = PerceptualHash.hammingDistance(currentHash, prev)
            isStatic = (hammingDistance <= config.staticSkipThresholdBits)
        } else {
            hammingDistance = 64
            isStatic = false
        }

        // Static frame skipping
        if isStatic && consecutiveStaticSkips < config.maxConsecutiveStaticSkips {
            consecutiveStaticSkips += 1
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
                transportClient.send(type: .staticHeartbeat, frame: frameMeta)
            }
            return
        }

        // Frame has changed or keyframe sync reached
        let isKeyframe = (consecutiveStaticSkips >= config.maxConsecutiveStaticSkips || lastPerceptualHash == nil)
        let skippedCount = consecutiveStaticSkips

        let srcWidth = CVPixelBufferGetWidth(pixelBuffer)
        let srcHeight = CVPixelBufferGetHeight(pixelBuffer)

        var ciImage = CIImage(cvPixelBuffer: pixelBuffer)
        let maxSrc = max(srcWidth, srcHeight)
        let targetWidth: Int
        let targetHeight: Int

        if maxSrc > config.maxResolutionDimension {
            let scale = CGFloat(config.maxResolutionDimension) / CGFloat(maxSrc)
            targetWidth = Int(CGFloat(srcWidth) * scale)
            targetHeight = Int(CGFloat(srcHeight) * scale)
            ciImage = ciImage.transformed(by: CGAffineTransform(scaleX: scale, y: scale))
        } else {
            targetWidth = srcWidth
            targetHeight = srcHeight
        }

        guard let jpegData = ciContext.jpegRepresentation(
            of: ciImage,
            colorSpace: CGColorSpaceCreateDeviceRGB(),
            options: [kCGImageDestinationLossyFactor as CIImageRepresentationOption: config.jpegCompressionQuality]
        ) else {
            return
        }

        let frameMeta = FrameMetadata(
            width: targetWidth,
            height: targetHeight,
            format: "jpeg",
            perceptualHash: PerceptualHash.hexString(from: currentHash),
            hammingDistance: hammingDistance,
            isKeyframe: isKeyframe,
            skippedSinceLastKeyframe: skippedCount,
            captureFPS: config.targetFrameRate,
            targetFPS: config.targetFrameRate
        )

        transportClient.send(
            type: .frame,
            frame: frameMeta,
            payloadData: jpegData
        )

        lastPerceptualHash = currentHash
        consecutiveStaticSkips = 0
    }

    private func processAudioSample(_ sampleBuffer: CMSampleBuffer) {
        guard config.appAudioOptIn else { return }

        guard let formatDesc = CMSampleBufferGetFormatDescription(sampleBuffer),
              let asbd = CMAudioFormatDescriptionGetStreamBasicDescription(formatDesc)?.pointee else {
            return
        }

        let numSamples = CMSampleBufferGetNumSamples(sampleBuffer)
        guard numSamples > 0, let blockBuffer = CMSampleBufferGetDataBuffer(sampleBuffer) else { return }

        var totalLength = 0
        var dataPointer: UnsafeMutablePointer<Int8>?

        let status = CMBlockBufferGetDataPointer(
            blockBuffer,
            atOffset: 0,
            lengthAtOffsetOut: nil,
            totalLengthOut: &totalLength,
            dataPointerOut: &dataPointer
        )

        guard status == kCMBlockBufferNoErr, let ptr = dataPointer, totalLength > 0 else { return }

        let rawData = Data(bytes: ptr, count: totalLength)
        let durationMs = (Double(numSamples) / max(asbd.mSampleRate, 1.0)) * 1000.0

        let audioMeta = AudioMetadata(
            sourceType: .appAudio,
            sampleRate: asbd.mSampleRate,
            channelCount: Int(asbd.mChannelsPerFrame),
            format: "pcm_f32le",
            sampleCount: numSamples,
            durationMs: durationMs
        )

        transportClient.send(
            type: .audioChunk,
            audio: audioMeta,
            payloadData: rawData
        )
    }
}

// MARK: - ScreenCaptureKit Stream Delegate Handler

@available(macOS 12.3, macCatalyst 15.4, *)
private final class SCStreamDelegateHandler: NSObject, SCStreamDelegate, @unchecked Sendable {
    private weak var adapter: ScreenCaptureKitAdapter?

    init(adapter: ScreenCaptureKitAdapter) {
        self.adapter = adapter
        super.init()
    }

    func stream(_ stream: SCStream, didStopWithError error: Error) {
        Task { @MainActor [weak adapter] in
            adapter?.handleStreamStopped(error: error)
        }
    }
}
#endif
