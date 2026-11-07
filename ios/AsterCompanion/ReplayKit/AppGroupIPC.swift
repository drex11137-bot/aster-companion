//
//  AppGroupIPC.swift
//  AsterCompanion
//
//  Created for Aster Companion iOS & macOS Screen Awareness System.
//  Inter-Process Communication (IPC) bridge coordinating configuration,
//  profile isolation checks, broadcast lifecycle, and telemetry between
//  the Main Application and the ReplayKit Broadcast Upload Extension.
//

import Foundation

/// Bridge for shared configuration and Darwin notifications across process boundaries.
public final class AppGroupIPC: @unchecked Sendable {

    // MARK: - App Group Identifier

    /// Standard Apple App Group container identifier shared between host app and extension.
    public static let appGroupIdentifier = "group.com.astercompanion.app"

    // MARK: - Darwin Notification Identifiers

    public enum NotificationName: String, CaseIterable {
        case broadcastStarted = "com.astercompanion.app.replaykit.started"
        case broadcastPaused = "com.astercompanion.app.replaykit.paused"
        case broadcastResumed = "com.astercompanion.app.replaykit.resumed"
        case broadcastFinished = "com.astercompanion.app.replaykit.finished"
        case profileChanged = "com.astercompanion.app.replaykit.profileChanged"
        case broadcastError = "com.astercompanion.app.replaykit.error"
        case telemetryUpdated = "com.astercompanion.app.replaykit.telemetry"

        public var cfName: CFNotificationName {
            return CFNotificationName(rawValue as CFString)
        }
    }

    // MARK: - Shared Keys

    private enum Keys {
        static let sessionConfig = "com.astercompanion.ipc.session_config"
        static let activeProfileId = "com.astercompanion.ipc.active_profile_id"
        static let deviceId = "com.astercompanion.ipc.device_id"
        static let sessionId = "com.astercompanion.ipc.session_id"
        static let isBroadcastActive = "com.astercompanion.ipc.is_broadcast_active"
        static let isBroadcastPaused = "com.astercompanion.ipc.is_broadcast_paused"
        static let broadcastStartedAt = "com.astercompanion.ipc.broadcast_started_at"
        static let lastBroadcastError = "com.astercompanion.ipc.last_broadcast_error"
        static let lastTelemetry = "com.astercompanion.ipc.last_telemetry"
        static let micOptIn = "com.astercompanion.ipc.mic_opt_in"
        static let appAudioOptIn = "com.astercompanion.ipc.app_audio_opt_in"
    }

    // MARK: - Singleton & Storage

    public static let shared = AppGroupIPC()

    private let defaults: UserDefaults?
    private let lock = NSLock()

    public init(suiteName: String = appGroupIdentifier) {
        self.defaults = UserDefaults(suiteName: suiteName)
    }

    // MARK: - Configuration Publishing (Main App -> Extension)

    /// Saves the active broadcast session configuration to shared App Group defaults.
    public func saveSessionConfig(_ config: AwarenessSessionConfig) {
        lock.lock()
        defer { lock.unlock() }

        guard let defaults = defaults else { return }
        do {
            let data = try JSONEncoder().encode(config)
            defaults.set(data, forKey: Keys.sessionConfig)
            defaults.set(config.activeProfileId, forKey: Keys.activeProfileId)
            defaults.set(config.deviceId, forKey: Keys.deviceId)
            defaults.set(config.sessionId, forKey: Keys.sessionId)
            defaults.set(config.micOptIn, forKey: Keys.micOptIn)
            defaults.set(config.appAudioOptIn, forKey: Keys.appAudioOptIn)
            defaults.synchronize()
        } catch {
            print("[AppGroupIPC] Failed to encode session config: \(error.localizedDescription)")
        }
    }

    /// Loads the active broadcast session configuration from shared App Group defaults.
    public func loadSessionConfig() -> AwarenessSessionConfig? {
        lock.lock()
        defer { lock.unlock() }

        guard let defaults = defaults,
              let data = defaults.data(forKey: Keys.sessionConfig) else {
            return nil
        }

        do {
            return try JSONDecoder().decode(AwarenessSessionConfig.self, from: data)
        } catch {
            print("[AppGroupIPC] Failed to decode session config: \(error.localizedDescription)")
            return nil
        }
    }

    /// Clears the session config upon broadcast termination.
    public func clearSessionConfig() {
        lock.lock()
        defer { lock.unlock() }

        guard let defaults = defaults else { return }
        defaults.removeObject(forKey: Keys.sessionConfig)
        defaults.removeObject(forKey: Keys.sessionId)
        defaults.synchronize()
    }

    // MARK: - Profile Isolation Enforcement

    /// Updates the active profile ID. Called by main app whenever the user switches profiles.
    /// Immediately notifies extension via Darwin notification to trigger instant session abort.
    public func updateActiveProfileId(_ profileId: String) {
        lock.lock()
        defaults?.set(profileId, forKey: Keys.activeProfileId)
        defaults?.synchronize()
        lock.unlock()

        postDarwinNotification(.profileChanged)
    }

    /// Retrieves the currently authorized profile ID.
    public func getActiveProfileId() -> String? {
        lock.lock()
        defer { lock.unlock() }
        return defaults?.string(forKey: Keys.activeProfileId)
    }

    /// Validates that the executing session's profile matches the currently active profile.
    public func validateProfileIsolation(sessionProfileId: String) -> Bool {
        guard let activeProfile = getActiveProfileId() else {
            return false
        }
        return activeProfile == sessionProfileId
    }

    // MARK: - Broadcast Lifecycle State

    public func setBroadcastActive(_ isActive: Bool, sessionId: String? = nil) {
        lock.lock()
        defer { lock.unlock() }

        defaults?.set(isActive, forKey: Keys.isBroadcastActive)
        if isActive {
            defaults?.set(Date().timeIntervalSince1970, forKey: Keys.broadcastStartedAt)
            if let sessionId = sessionId {
                defaults?.set(sessionId, forKey: Keys.sessionId)
            }
        } else {
            defaults?.set(false, forKey: Keys.isBroadcastPaused)
            defaults?.removeObject(forKey: Keys.broadcastStartedAt)
        }
        defaults?.synchronize()
    }

    public func isBroadcastActive() -> Bool {
        lock.lock()
        defer { lock.unlock() }
        return defaults?.bool(forKey: Keys.isBroadcastActive) ?? false
    }

    public func setBroadcastPaused(_ isPaused: Bool) {
        lock.lock()
        defer { lock.unlock() }

        defaults?.set(isPaused, forKey: Keys.isBroadcastPaused)
        defaults?.synchronize()
    }

    public func isBroadcastPaused() -> Bool {
        lock.lock()
        defer { lock.unlock() }
        return defaults?.bool(forKey: Keys.isBroadcastPaused) ?? false
    }

    public func recordBroadcastError(_ errorMessage: String) {
        lock.lock()
        defaults?.set(errorMessage, forKey: Keys.lastBroadcastError)
        defaults?.synchronize()
        lock.unlock()

        postDarwinNotification(.broadcastError)
    }

    public func getLastBroadcastError() -> String? {
        lock.lock()
        defer { lock.unlock() }
        return defaults?.string(forKey: Keys.lastBroadcastError)
    }

    // MARK: - Audio Opt-In Controls

    public func setMicOptIn(_ enabled: Bool) {
        lock.lock()
        defer { lock.unlock() }
        defaults?.set(enabled, forKey: Keys.micOptIn)
        defaults?.synchronize()
    }

    public func isMicOptIn() -> Bool {
        lock.lock()
        defer { lock.unlock() }
        return defaults?.bool(forKey: Keys.micOptIn) ?? false
    }

    public func setAppAudioOptIn(_ enabled: Bool) {
        lock.lock()
        defer { lock.unlock() }
        defaults?.set(enabled, forKey: Keys.appAudioOptIn)
        defaults?.synchronize()
    }

    public func isAppAudioOptIn() -> Bool {
        lock.lock()
        defer { lock.unlock() }
        return defaults?.bool(forKey: Keys.appAudioOptIn) ?? false
    }

    // MARK: - Telemetry Publishing

    public func publishTelemetry(_ telemetry: AwarenessTelemetry) {
        lock.lock()
        defer { lock.unlock() }

        guard let defaults = defaults else { return }
        do {
            let data = try JSONEncoder().encode(telemetry)
            defaults.set(data, forKey: Keys.lastTelemetry)
            defaults.synchronize()
        } catch {
            print("[AppGroupIPC] Failed to encode telemetry: \(error.localizedDescription)")
        }
    }

    public func loadTelemetry() -> AwarenessTelemetry? {
        lock.lock()
        defer { lock.unlock() }

        guard let defaults = defaults,
              let data = defaults.data(forKey: Keys.lastTelemetry) else {
            return nil
        }

        do {
            return try JSONDecoder().decode(AwarenessTelemetry.self, from: data)
        } catch {
            return nil
        }
    }

    // MARK: - Darwin Notifications (Cross-Process Signaling)

    /// Dispatches a Darwin notification to notify listening processes across sandbox boundaries.
    public func postDarwinNotification(_ name: NotificationName) {
        let center = CFNotificationCenterGetDarwinNotifyCenter()
        CFNotificationCenterPostNotification(
            center,
            name.cfName,
            nil,
            nil,
            true
        )
    }

    /// Registers a listener for cross-process Darwin notifications.
    public func addDarwinObserver(
        for name: NotificationName,
        observer: AnyObject,
        callback: @escaping (NotificationName) -> Void
    ) {
        let center = CFNotificationCenterGetDarwinNotifyCenter()
        let observerPointer = Unmanaged.passUnretained(observer).toOpaque()

        // Darwin callback bridge
        let notificationCallback: CFNotificationCallback = { _, observerPtr, name, _, _ in
            guard let observerPtr = observerPtr,
                  let name = name else { return }

            let rawName = name.rawValue as String
            if let matched = NotificationName(rawValue: rawName) {
                // Call back through observer registry
                AppGroupNotificationRegistry.shared.dispatch(name: matched, for: observerPtr)
            }
        }

        AppGroupNotificationRegistry.shared.register(
            observerPtr: observerPointer,
            notification: name,
            handler: callback
        )

        CFNotificationCenterAddObserver(
            center,
            observerPointer,
            notificationCallback,
            name.rawValue as CFString,
            nil,
            .deliverImmediately
        )
    }

    /// Unregisters an observer from Darwin notifications.
    public func removeDarwinObserver(_ observer: AnyObject, for name: NotificationName? = nil) {
        let center = CFNotificationCenterGetDarwinNotifyCenter()
        let observerPointer = Unmanaged.passUnretained(observer).toOpaque()

        if let name = name {
            CFNotificationCenterRemoveObserver(
                center,
                observerPointer,
                name.cfName,
                nil
            )
            AppGroupNotificationRegistry.shared.unregister(observerPtr: observerPointer, notification: name)
        } else {
            for notif in NotificationName.allCases {
                CFNotificationCenterRemoveObserver(
                    center,
                    observerPointer,
                    notif.cfName,
                    nil
                )
            }
            AppGroupNotificationRegistry.shared.unregisterAll(observerPtr: observerPointer)
        }
    }
}

// MARK: - Internal Notification Handler Registry

private final class AppGroupNotificationRegistry: @unchecked Sendable {
    static let shared = AppGroupNotificationRegistry()
    private let lock = NSLock()
    private var handlers: [UnsafeMutableRawPointer: [String: (AppGroupIPC.NotificationName) -> Void]] = [:]

    func register(
        observerPtr: UnsafeMutableRawPointer,
        notification: AppGroupIPC.NotificationName,
        handler: @escaping (AppGroupIPC.NotificationName) -> Void
    ) {
        lock.lock()
        defer { lock.unlock() }

        var observerMap = handlers[observerPtr] ?? [:]
        observerMap[notification.rawValue] = handler
        handlers[observerPtr] = observerMap
    }

    func unregister(observerPtr: UnsafeMutableRawPointer, notification: AppGroupIPC.NotificationName) {
        lock.lock()
        defer { lock.unlock() }

        handlers[observerPtr]?.removeValue(forKey: notification.rawValue)
        if handlers[observerPtr]?.isEmpty == true {
            handlers.removeValue(forKey: observerPtr)
        }
    }

    func unregisterAll(observerPtr: UnsafeMutableRawPointer) {
        lock.lock()
        defer { lock.unlock() }
        handlers.removeValue(forKey: observerPtr)
    }

    func dispatch(name: AppGroupIPC.NotificationName, for observerPtr: UnsafeMutableRawPointer) {
        lock.lock()
        let handler = handlers[observerPtr]?[name.rawValue]
        lock.unlock()

        handler?(name)
    }
}
