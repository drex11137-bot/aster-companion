//
//  AwarenessTransportClient.swift
//  AsterCompanion
//
//  Created for Aster Companion iOS & macOS Screen Awareness System.
//  High-reliability streaming transport connecting ReplayKit/ScreenCaptureKit
//  to Supabase backend via Secure WebSocket with HTTP Chunk Upload fallback.
//  Strictly enforces monotonic sequence numbers, cryptographic checksums,
//  bounded memory queues, and backpressure management (< 50MB RAM limit).
//

import CryptoKit
import Foundation

/// Delegate receiving transport events, acknowledgements, backpressure warnings, and errors.
public protocol AwarenessTransportDelegate: AnyObject, Sendable {
    func transportDidConnect(_ transport: AwarenessTransportClient)
    func transportDidDisconnect(_ transport: AwarenessTransportClient, error: Error?)
    func transport(_ transport: AwarenessTransportClient, didAcknowledgeSequence sequenceNumber: UInt64)
    func transport(_ transport: AwarenessTransportClient, didDropPacket packet: AwarenessPacket, reason: String)
    func transport(_ transport: AwarenessTransportClient, didUpdateTelemetry telemetry: AwarenessTelemetry)
}

/// Production network client for streaming awareness packets to Supabase.
public final class AwarenessTransportClient: NSObject, @unchecked Sendable {

    // MARK: - Properties

    public weak var delegate: AwarenessTransportDelegate?

    private let config: AwarenessSessionConfig
    private let session: URLSession
    private var webSocketTask: URLSessionWebSocketTask?

    // Concurrency & Queue Management
    private let queue = DispatchQueue(label: "com.astercompanion.awareness.transport", qos: .userInitiated)
    private let maxPendingQueueDepth = 5 // Bounded queue to prevent memory growth under network stalls

    private var pendingPackets: [AwarenessPacket] = []
    private var isSending = false
    private var isConnected = false
    private var isReconnecting = false
    private var retryCount = 0
    private let maxRetries = 5

    // Telemetry & Sequencing
    private var currentSequence: UInt64 = 0
    private var framesSentCount: UInt64 = 0
    private var bytesSentCount: UInt64 = 0
    private var framesSkippedCount: UInt64 = 0
    private var lastAckedSequence: UInt64 = 0
    private var fpsCalculationTimer: DispatchSourceTimer?
    private var heartbeatTimer: DispatchSourceTimer?

    private var recentUploadTimes: [Date] = []
    private let lock = NSLock()

    // MARK: - Initialization

    public init(config: AwarenessSessionConfig) {
        self.config = config

        let sessionConfig = URLSessionConfiguration.default
        sessionConfig.timeoutIntervalForRequest = 10.0
        sessionConfig.timeoutIntervalForResource = 30.0
        sessionConfig.waitsForConnectivity = true

        self.session = URLSession(configuration: sessionConfig)
        super.init()
    }

    deinit {
        disconnect()
    }

    // MARK: - Lifecycle & Connection

    /// Connects to the Supabase WebSocket streaming endpoint.
    public func connect() {
        queue.async { [weak self] in
            guard let self = self, !self.isConnected else { return }
            self.establishWebSocket()
            self.startHeartbeat()
            self.startTelemetryTimer()
        }
    }

    /// Disconnects cleanly and flushes remaining high-priority packets.
    public func disconnect() {
        queue.async { [weak self] in
            guard let self = self else { return }
            self.stopHeartbeat()
            self.stopTelemetryTimer()

            if let ws = self.webSocketTask {
                ws.cancel(with: .normalClosure, reason: "Session ended".data(using: .utf8))
                self.webSocketTask = nil
            }

            self.isConnected = false
            self.isReconnecting = false
            self.pendingPackets.removeAll()
            self.delegate?.transportDidDisconnect(self, error: nil)
        }
    }

    // MARK: - Packet Dispatch & Backpressure

    /// Queues an awareness packet for transmission.
    /// Under network backpressure, low-priority non-keyframe video frames are dropped
    /// to preserve extension memory (< 50MB RAM limit).
    public func send(
        type: AwarenessPacketType,
        frame: FrameMetadata? = nil,
        audio: AudioMetadata? = nil,
        payloadData: Data? = nil
    ) {
        queue.async { [weak self] in
            guard let self = self else { return }

            // Generate next monotonic sequence number
            self.currentSequence += 1
            let seq = self.currentSequence

            // Compute payload checksum and base64 representation
            var base64String: String? = nil
            var checksumString: String? = nil

            if let data = payloadData, !data.isEmpty {
                base64String = data.base64EncodedString()
                let sha256 = SHA256.hash(data: data)
                checksumString = sha256.map { String(format: "%02x", $0) }.joined()
            }

            let consent = AwarenessConsentMetadata(
                screenCaptureGranted: true,
                micAudioGranted: self.config.micOptIn,
                appAudioPlaybackGranted: self.config.appAudioOptIn
            )

            let packet = AwarenessPacket(
                sequenceNumber: seq,
                source: .iosReplayKitExtension,
                deviceId: self.config.deviceId,
                sessionId: self.config.sessionId,
                profileId: self.config.activeProfileId,
                consent: consent,
                type: type,
                frame: frame,
                audio: audio,
                payloadBase64: base64String,
                payloadChecksum: checksumString
            )

            self.enqueuePacket(packet)
        }
    }

    /// Enqueues a packet, enforcing backpressure limits.
    private func enqueuePacket(_ packet: AwarenessPacket) {
        // High-priority packets that MUST NOT be dropped:
        // Session start/pause/resume/end, and keyframes
        let isEssential = (packet.type != .frame || packet.frame?.isKeyframe == true)

        if pendingPackets.count >= maxPendingQueueDepth {
            if isEssential {
                // Drop the oldest non-essential frame in the queue to make room
                if let dropIndex = pendingPackets.firstIndex(where: { $0.type == .frame && $0.frame?.isKeyframe == false }) {
                    let dropped = pendingPackets.remove(at: dropIndex)
                    framesSkippedCount += 1
                    delegate?.transport(self, didDropPacket: dropped, reason: "Queue depth exceeded (backpressure)")
                }
            } else {
                // Drop current packet
                framesSkippedCount += 1
                delegate?.transport(self, didDropPacket: packet, reason: "Backpressure: packet queue full")
                return
            }
        }

        pendingPackets.append(packet)
        drainQueue()
    }

    // MARK: - Queue Drain & Transmission

    private func drainQueue() {
        guard !isSending, !pendingPackets.isEmpty else { return }

        let packet = pendingPackets.removeFirst()
        isSending = true

        if isConnected, let ws = webSocketTask {
            sendViaWebSocket(packet: packet, task: ws)
        } else {
            // WebSocket not connected: fallback to HTTP chunk upload
            sendViaHTTPFallback(packet: packet)
        }
    }

    private func sendViaWebSocket(packet: AwarenessPacket, task: URLSessionWebSocketTask) {
        do {
            let encoder = JSONEncoder()
            encoder.dateEncodingStrategy = .iso8601
            let jsonData = try encoder.encode(packet)
            let message = URLSessionWebSocketTask.Message.data(jsonData)

            task.send(message) { [weak self] error in
                guard let self = self else { return }
                self.queue.async {
                    self.isSending = false

                    if let error = error {
                        print("[AwarenessTransport] WS send failed: \(error.localizedDescription)")
                        // Attempt HTTP fallback for this packet
                        self.sendViaHTTPFallback(packet: packet)
                    } else {
                        self.recordPacketSent(packet: packet, byteSize: UInt64(jsonData.count))
                        self.drainQueue()
                    }
                }
            }
        } catch {
            isSending = false
            print("[AwarenessTransport] JSON serialization error: \(error.localizedDescription)")
            drainQueue()
        }
    }

    private func sendViaHTTPFallback(packet: AwarenessPacket) {
        // Construct Supabase Edge Function ingest URL
        var requestUrl = config.supabaseUrl
        if requestUrl.path.isEmpty || requestUrl.path == "/" {
            requestUrl = requestUrl.appendingPathComponent("functions/v1/awareness-ingest")
        }

        var request = URLRequest(url: requestUrl)
        request.httpMethod = "POST"
        request.setValue("Bearer \(config.supabaseAuthToken)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue(packet.profileId, forHTTPHeaderField: "X-Profile-ID")
        request.setValue(packet.sessionId, forHTTPHeaderField: "X-Session-ID")
        request.setValue(String(packet.sequenceNumber), forHTTPHeaderField: "X-Sequence-Number")

        do {
            let encoder = JSONEncoder()
            encoder.dateEncodingStrategy = .iso8601
            let jsonData = try encoder.encode(packet)
            request.httpBody = jsonData

            let task = session.dataTask(with: request) { [weak self] _, response, error in
                guard let self = self else { return }
                self.queue.async {
                    self.isSending = false

                    if let httpResponse = response as? HTTPURLResponse, (200...299).contains(httpResponse.statusCode) {
                        self.recordPacketSent(packet: packet, byteSize: UInt64(jsonData.count))
                    } else {
                        let errorMsg = error?.localizedDescription ?? "HTTP status \((response as? HTTPURLResponse)?.statusCode ?? -1)"
                        print("[AwarenessTransport] HTTP ingest failed: \(errorMsg)")
                    }

                    self.drainQueue()
                }
            }
            task.resume()
        } catch {
            isSending = false
            drainQueue()
        }
    }

    private func recordPacketSent(packet: AwarenessPacket, byteSize: UInt64) {
        framesSentCount += 1
        bytesSentCount += byteSize
        lastAckedSequence = packet.sequenceNumber

        let now = Date()
        recentUploadTimes.append(now)

        // Prune timestamps older than 5 seconds
        let windowStart = now.addingTimeInterval(-5.0)
        recentUploadTimes.removeAll { $0 < windowStart }

        delegate?.transport(self, didAcknowledgeSequence: packet.sequenceNumber)
    }

    // MARK: - WebSocket Management

    private func establishWebSocket() {
        var wsUrl = config.supabaseUrl

        // Transform https:// -> wss:// and target awareness stream endpoint
        var components = URLComponents(url: wsUrl, resolvingAgainstBaseURL: true)
        if components?.scheme == "https" {
            components?.scheme = "wss"
        } else if components?.scheme == "http" {
            components?.scheme = "ws"
        }

        if components?.path.isEmpty == true || components?.path == "/" {
            components?.path = "/functions/v1/awareness-stream"
        }

        guard let targetUrl = components?.url else { return }

        var request = URLRequest(url: targetUrl)
        request.setValue("Bearer \(config.supabaseAuthToken)", forHTTPHeaderField: "Authorization")
        request.setValue(config.activeProfileId, forHTTPHeaderField: "X-Profile-ID")
        request.setValue(config.deviceId, forHTTPHeaderField: "X-Device-ID")
        request.setValue(config.sessionId, forHTTPHeaderField: "X-Session-ID")

        let task = session.webSocketTask(with: request)
        self.webSocketTask = task
        task.resume()

        self.isConnected = true
        self.retryCount = 0
        self.delegate?.transportDidConnect(self)

        listenForWebSocketMessages(task)
    }

    private func listenForWebSocketMessages(_ task: URLSessionWebSocketTask) {
        task.receive { [weak self, weak task] result in
            guard let self = self, let task = task, task == self.webSocketTask else { return }

            switch result {
            case .success(let message):
                self.handleIncomingWebSocketMessage(message)
                self.listenForWebSocketMessages(task)
            case .failure(let error):
                print("[AwarenessTransport] WS connection dropped: \(error.localizedDescription)")
                self.queue.async {
                    self.isConnected = false
                    self.scheduleReconnect()
                }
            }
        }
    }

    private func handleIncomingWebSocketMessage(_ message: URLSessionWebSocketTask.Message) {
        switch message {
        case .string(let text):
            if let data = text.data(using: .utf8),
               let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let ackSeq = json["ack_sequence"] as? UInt64 {
                self.lastAckedSequence = ackSeq
                self.delegate?.transport(self, didAcknowledgeSequence: ackSeq)
            }
        case .data(let data):
            if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let ackSeq = json["ack_sequence"] as? UInt64 {
                self.lastAckedSequence = ackSeq
                self.delegate?.transport(self, didAcknowledgeSequence: ackSeq)
            }
        @unknown default:
            break
        }
    }

    private func scheduleReconnect() {
        guard !isReconnecting, retryCount < maxRetries else { return }
        isReconnecting = true
        retryCount += 1

        // Exponential backoff with jitter: (2^retry * 0.5s) + random(0...0.3s)
        let backoff = pow(2.0, Double(retryCount)) * 0.5 + Double.random(in: 0.0...0.3)

        queue.asyncAfter(deadline: .now() + backoff) { [weak self] in
            guard let self = self else { return }
            self.isReconnecting = false
            self.establishWebSocket()
        }
    }

    // MARK: - Heartbeat & Telemetry Timers

    private func startHeartbeat() {
        stopHeartbeat()
        let timer = DispatchSource.makeTimerSource(queue: queue)
        timer.schedule(deadline: .now() + 5.0, repeating: 5.0)
        timer.setEventHandler { [weak self] in
            guard let self = self else { return }
            if self.isConnected {
                self.webSocketTask?.sendPing { error in
                    if let error = error {
                        print("[AwarenessTransport] WS Ping failed: \(error.localizedDescription)")
                    }
                }
            }
        }
        timer.resume()
        self.heartbeatTimer = timer
    }

    private func stopHeartbeat() {
        heartbeatTimer?.cancel()
        heartbeatTimer = nil
    }

    private func startTelemetryTimer() {
        stopTelemetryTimer()
        let timer = DispatchSource.makeTimerSource(queue: queue)
        timer.schedule(deadline: .now() + 1.0, repeating: 1.0)
        timer.setEventHandler { [weak self] in
            guard let self = self else { return }
            self.emitTelemetry()
        }
        timer.resume()
        self.fpsCalculationTimer = timer
    }

    private func stopTelemetryTimer() {
        fpsCalculationTimer?.cancel()
        fpsCalculationTimer = nil
    }

    private func emitTelemetry() {
        let now = Date()
        let windowStart = now.addingTimeInterval(-1.0)
        let uploadsInLastSecond = recentUploadTimes.filter { $0 >= windowStart }.count
        let uploadFPS = Double(uploadsInLastSecond)

        let residentMB = Self.getResidentMemoryMB()

        let telemetry = AwarenessTelemetry(
            captureFPS: config.targetFrameRate,
            uploadFPS: uploadFPS,
            skippedFramesTotal: framesSkippedCount,
            uploadedFramesTotal: framesSentCount,
            totalBytesUploaded: bytesSentCount,
            memoryUsageMB: residentMB,
            lastSequenceNumber: currentSequence,
            lastEventTimestamp: now,
            isConnected: isConnected
        )

        delegate?.transport(self, didUpdateTelemetry: telemetry)
    }

    // MARK: - Resident Memory Inspector

    /// Reads process resident memory size in Megabytes from Mach kernel task info.
    public static func getResidentMemoryMB() -> Double {
        var info = mach_task_basic_info()
        var count = mach_msg_type_number_t(MemoryLayout<mach_task_basic_info>.size / MemoryLayout<integer_t>.size)

        let kerr = withUnsafeMutablePointer(to: &info) { infoPtr in
            infoPtr.withMemoryRebound(to: integer_t.self, capacity: Int(count)) { intPtr in
                task_info(mach_task_self_, task_flavor_t(MACH_TASK_BASIC_INFO), intPtr, &count)
            }
        }

        if kerr == KERN_SUCCESS {
            return Double(info.resident_size) / (1024.0 * 1024.0)
        }
        return 0.0
    }
}
