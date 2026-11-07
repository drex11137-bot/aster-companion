//
//  ReplayKitController.swift
//  AsterCompanion
//
//  Created for Aster Companion iOS & macOS Screen Awareness System.
//  Coordinates ReplayKit broadcast lifecycle, RPSystemBroadcastPickerView triggers,
//  state management, profile isolation enforcement, Darwin notification IPC,
//  and OS broadcast finish event detection from the Main Application.
//

import Combine
import Foundation
import ReplayKit
import SwiftUI

#if canImport(UIKit)
import UIKit
#endif

/// Main Application Controller managing iOS Screen Awareness and ReplayKit Broadcast Extension.
@MainActor
public final class ReplayKitController: ObservableObject {

    // MARK: - Published State for UI & Contextual Control Panel

    @Published public private(set) var state: AwarenessState = .idle
    @Published public private(set) var telemetry: AwarenessTelemetry = AwarenessTelemetry()
    @Published public private(set) var activeProfileId: String?
    @Published public private(set) var activeProfileName: String = "Aster"
    @Published public private(set) var lastErrorMessage: String?
    @Published public var isMicEnabled: Bool = false
    @Published public var isSystemAudioEnabled: Bool = false
    @Published public private(set) var isSupportedOnDevice: Bool = true

    // MARK: - Internal Configuration & Dependencies

    private let extensionBundleId: String
    private let ipc = AppGroupIPC.shared
    private var cancellables = Set<AnyCancellable>()

    // Status polling timer to detect external OS stop events (e.g., status bar red pill tapped)
    private var osStateObserverTimer: Timer?
    private var currentSessionId: String?

    #if canImport(UIKit)
    // Hidden system broadcast picker view used for programmatic triggering
    private var hiddenPickerView: RPSystemBroadcastPickerView?
    #endif

    // MARK: - Initialization

    public init(
        extensionBundleId: String = "com.astercompanion.app.AsterCompanion.ReplayKitExtension"
    ) {
        self.extensionBundleId = extensionBundleId
        self.activeProfileId = ipc.getActiveProfileId()
        self.isMicEnabled = ipc.isMicOptIn()
        self.isSystemAudioEnabled = ipc.isAppAudioOptIn()

        #if os(iOS)
        self.isSupportedOnDevice = true
        setupHiddenPickerView()
        #else
        self.isSupportedOnDevice = false
        #endif

        setupDarwinNotificationObservers()
        checkInitialBroadcastState()
    }

    deinit {
        osStateObserverTimer?.invalidate()
        ipc.removeDarwinObserver(self)
    }

    // MARK: - RPSystemBroadcastPickerView Setup & Programmatic Trigger

    #if canImport(UIKit)
    private func setupHiddenPickerView() {
        let picker = RPSystemBroadcastPickerView(frame: CGRect(x: 0, y: 0, width: 44, height: 44))
        picker.preferredExtension = extensionBundleId
        picker.showsMicrophoneButton = true
        picker.autoresizingMask = [.flexibleTopMargin, .flexibleBottomMargin, .flexibleLeftMargin, .flexibleRightMargin]
        self.hiddenPickerView = picker
    }

    /// Programmatically triggers the iOS System Broadcast Picker view.
    /// Finds the internal system button inside `RPSystemBroadcastPickerView` and synthesizes
    /// a touch event, allowing custom Aster Companion UI buttons to present the system picker.
    public func triggerBroadcastPicker() {
        guard let activeProfile = activeProfileId, !activeProfile.isEmpty else {
            let error = AwarenessError.noActiveProfile
            self.lastErrorMessage = error.localizedDescription
            self.state = .error(error)
            return
        }

        guard let picker = hiddenPickerView else {
            setupHiddenPickerView()
            triggerBroadcastPicker()
            return
        }

        // Find the internal UIButton inside RPSystemBroadcastPickerView subviews
        for subview in picker.subviews {
            if let button = subview as? UIButton {
                button.sendActions(for: .touchUpInside)
                return
            }
        }

        // If no UIButton found in subviews, send action to the picker itself
        picker.sendActions(for: .touchUpInside)
    }
    #else
    public func triggerBroadcastPicker() {
        // macOS or unsupported platform fallback
        print("[ReplayKitController] RPSystemBroadcastPickerView is only available on iOS.")
    }
    #endif

    // MARK: - Awareness Session Management

    /// Prepares and activates screen awareness for the specified authenticated profile.
    /// Writes session configuration to shared App Group storage prior to broadcast launch.
    public func prepareAwarenessSession(
        profileId: String,
        profileName: String,
        deviceId: String,
        supabaseUrl: URL,
        supabaseAuthToken: String,
        targetFrameRate: Double = 3.0,
        maxResolutionDimension: Int = 1280
    ) -> Bool {
        // 1. Strict Profile Isolation Check: Must have a valid profile ID
        guard !profileId.isEmpty else {
            let error = AwarenessError.noActiveProfile
            self.lastErrorMessage = error.localizedDescription
            self.state = .error(error)
            return false
        }

        let newSessionId = UUID().uuidString
        self.currentSessionId = newSessionId
        self.activeProfileId = profileId
        self.activeProfileName = profileName

        // 2. Build configuration
        let config = AwarenessSessionConfig(
            activeProfileId: profileId,
            deviceId: deviceId,
            sessionId: newSessionId,
            supabaseUrl: supabaseUrl,
            supabaseAuthToken: supabaseAuthToken,
            micOptIn: isMicEnabled,
            appAudioOptIn: isSystemAudioEnabled,
            targetFrameRate: targetFrameRate,
            maxResolutionDimension: maxResolutionDimension
        )

        // 3. Save to App Group storage
        ipc.saveSessionConfig(config)
        self.state = .starting(sessionId: newSessionId, profileId: profileId)
        startOSStateObserver()

        return true
    }

    /// Explicitly pauses the screen awareness session.
    public func pauseAwareness() {
        guard case .active(let sessionId, let profileId, _) = state else { return }
        ipc.setBroadcastPaused(true)
        ipc.postDarwinNotification(.broadcastPaused)
        self.state = .paused(sessionId: sessionId, profileId: profileId)
    }

    /// Resumes the paused screen awareness session.
    public func resumeAwareness() {
        guard case .paused(let sessionId, let profileId) = state else { return }
        ipc.setBroadcastPaused(false)
        ipc.postDarwinNotification(.broadcastResumed)
        self.state = .active(sessionId: sessionId, profileId: profileId, startedAt: Date())
    }

    /// Stops the active screen awareness session.
    public func stopAwareness() {
        guard let currentSession = currentSessionId ?? ipc.loadSessionConfig()?.sessionId else {
            handleBroadcastFinished()
            return
        }

        self.state = .stopping(sessionId: currentSession)

        // Signal extension to finish
        ipc.setBroadcastActive(false)
        ipc.postDarwinNotification(.broadcastFinished)

        // Clear local session state
        handleBroadcastFinished()
    }

    // MARK: - Profile Switching & Isolation Enforcement

    /// Handles profile switching from the companion UI.
    /// Immediately halts any active awareness session to ensure zero context transfer.
    public func handleProfileSwitched(newProfileId: String, newProfileName: String) {
        if state != .idle {
            print("[ReplayKitController] Profile switched to \(newProfileId). Stopping active broadcast.")
            stopAwareness()
        }

        self.activeProfileId = newProfileId
        self.activeProfileName = newProfileName
        ipc.updateActiveProfileId(newProfileId)
    }

    // MARK: - Audio Opt-In Toggles

    public func setMicOptIn(enabled: Bool) {
        self.isMicEnabled = enabled
        ipc.setMicOptIn(enabled)
    }

    public func setSystemAudioOptIn(enabled: Bool) {
        self.isSystemAudioEnabled = enabled
        ipc.setAppAudioOptIn(enabled)
    }

    // MARK: - OS Broadcast Finish Detection & Darwin Observers

    private func setupDarwinNotificationObservers() {
        // 1. Broadcast Started notification from Extension
        ipc.addDarwinObserver(for: .broadcastStarted, observer: self) { [weak self] _ in
            Task { @MainActor [weak self] in
                guard let self = self else { return }
                let sessionId = self.currentSessionId ?? self.ipc.loadSessionConfig()?.sessionId ?? UUID().uuidString
                let profileId = self.activeProfileId ?? self.ipc.getActiveProfileId() ?? ""
                self.state = .active(sessionId: sessionId, profileId: profileId, startedAt: Date())
                self.lastErrorMessage = nil
                self.startOSStateObserver()
            }
        }

        // 2. Broadcast Paused notification from Extension
        ipc.addDarwinObserver(for: .broadcastPaused, observer: self) { [weak self] _ in
            Task { @MainActor [weak self] in
                guard let self = self else { return }
                if case .active(let sessionId, let profileId, _) = self.state {
                    self.state = .paused(sessionId: sessionId, profileId: profileId)
                }
            }
        }

        // 3. Broadcast Resumed notification from Extension
        ipc.addDarwinObserver(for: .broadcastResumed, observer: self) { [weak self] _ in
            Task { @MainActor [weak self] in
                guard let self = self else { return }
                if case .paused(let sessionId, let profileId) = self.state {
                    self.state = .active(sessionId: sessionId, profileId: profileId, startedAt: Date())
                }
            }
        }

        // 4. Broadcast Finished notification from Extension
        ipc.addDarwinObserver(for: .broadcastFinished, observer: self) { [weak self] _ in
            Task { @MainActor [weak self] in
                self?.handleBroadcastFinished()
            }
        }

        // 5. Broadcast Error notification from Extension
        ipc.addDarwinObserver(for: .broadcastError, observer: self) { [weak self] _ in
            Task { @MainActor [weak self] in
                guard let self = self else { return }
                if let errorMsg = self.ipc.getLastBroadcastError() {
                    self.lastErrorMessage = errorMsg
                    self.state = .error(.unknown(errorMsg))
                }
            }
        }

        // 6. Live Telemetry update from Extension
        ipc.addDarwinObserver(for: .telemetryUpdated, observer: self) { [weak self] _ in
            Task { @MainActor [weak self] in
                guard let self = self, let latest = self.ipc.loadTelemetry() else { return }
                self.telemetry = latest
            }
        }
    }

    /// Polling fallback to detect when user stops recording via iOS red status bar indicator.
    private func startOSStateObserver() {
        osStateObserverTimer?.invalidate()
        osStateObserverTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in
                guard let self = self else { return }

                // Check ReplayKit screen recorder state & App Group state
                let isExtensionActive = self.ipc.isBroadcastActive()
                let isRecording = RPScreenRecorder.shared().isRecording

                if self.state != .idle && !isExtensionActive && !isRecording {
                    print("[ReplayKitController] Detected OS broadcast termination via status bar.")
                    self.handleBroadcastFinished()
                }
            }
        }
    }

    private func checkInitialBroadcastState() {
        if ipc.isBroadcastActive() {
            let sessionId = ipc.loadSessionConfig()?.sessionId ?? UUID().uuidString
            let profileId = ipc.getActiveProfileId() ?? ""
            self.state = .active(sessionId: sessionId, profileId: profileId, startedAt: Date())
            startOSStateObserver()
        } else {
            self.state = .idle
        }
    }

    private func handleBroadcastFinished() {
        osStateObserverTimer?.invalidate()
        osStateObserverTimer = nil
        currentSessionId = nil
        ipc.setBroadcastActive(false)
        ipc.clearSessionConfig()

        self.state = .idle
        self.telemetry = AwarenessTelemetry()
    }
}

// MARK: - SwiftUI View Wrapper for RPSystemBroadcastPickerView

#if canImport(UIKit)
/// SwiftUI Representable wrapper enabling RPSystemBroadcastPickerView integration in SwiftUI layouts.
public struct ReplayKitPickerRepresentable: UIViewRepresentable {
    public let preferredExtension: String
    public let showsMicrophoneButton: Bool

    public init(
        preferredExtension: String = "com.astercompanion.app.AsterCompanion.ReplayKitExtension",
        showsMicrophoneButton: Bool = true
    ) {
        self.preferredExtension = preferredExtension
        self.showsMicrophoneButton = showsMicrophoneButton
    }

    public func makeUIView(context: Context) -> RPSystemBroadcastPickerView {
        let picker = RPSystemBroadcastPickerView(frame: .zero)
        picker.preferredExtension = preferredExtension
        picker.showsMicrophoneButton = showsMicrophoneButton
        return picker
    }

    public func updateUIView(_ uiView: RPSystemBroadcastPickerView, context: Context) {
        uiView.preferredExtension = preferredExtension
        uiView.showsMicrophoneButton = showsMicrophoneButton
    }
}
#endif
