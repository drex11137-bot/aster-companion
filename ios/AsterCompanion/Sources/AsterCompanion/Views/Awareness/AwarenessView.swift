import SwiftUI
import ReplayKit

#if os(iOS)
import UIKit

/// Wraps Apple's RPSystemBroadcastPickerView for initiating ReplayKit broadcast extension
struct ReplayKitBroadcastPickerRepresentable: UIViewRepresentable {
    let preferredExtension: String = "com.astercompanion.AsterCompanion.ScreenBroadcast"
    
    func makeUIView(context: Context) -> RPSystemBroadcastPickerView {
        let pickerView = RPSystemBroadcastPickerView(frame: CGRect(x: 0, y: 0, width: 44, height: 44))
        pickerView.preferredExtension = preferredExtension
        pickerView.showsMicrophoneButton = true
        
        // Find internal button and tint it to warm amber
        for subview in pickerView.subviews {
            if let button = subview as? UIButton {
                button.tintColor = UIColor(Color(hex: "E59843"))
            }
        }
        return pickerView
    }
    
    func updateUIView(_ uiView: RPSystemBroadcastPickerView, context: Context) {}
}
#endif

/// Contextual Awareness Control Panel conforming strictly to PRD Section 5 & 13.
public struct AwarenessView: View {
    @ObservedObject var appState: AppState = AppState.shared
    @Environment(\.dismiss) var dismiss
    
    public init() {}
    
    public var body: some View {
        NavigationStack {
            ScrollView(.vertical, showsIndicators: false) {
                VStack(alignment: .leading, spacing: 20) {
                    // MARK: - Active Session Card
                    activeSessionHeader
                    
                    // MARK: - ReplayKit Broadcast Trigger Card
                    broadcastControlCard
                    
                    // MARK: - Telemetry & Honest FPS Meters
                    telemetryMetersGrid
                    
                    // MARK: - Quick Toggles
                    quickTogglesSection
                    
                    // MARK: - Honest Disclosure & Privacy Policy Notice
                    privacyDisclosureCard
                    
                    Spacer(minLength: 30)
                }
                .padding(.horizontal, 20)
                .padding(.top, 16)
            }
            .background(AsterTheme.ground.ignoresSafeArea())
            .navigationTitle("Awareness Panel")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                        .foregroundColor(AsterTheme.warmAmber)
                        .fontWeight(.semibold)
                }
            }
        }
    }
    
    // MARK: - Active Session Header
    private var activeSessionHeader: some View {
        HStack(spacing: 14) {
            ZStack {
                Circle()
                    .fill(appState.telemetry.status.color.opacity(0.2))
                    .frame(width: 48, height: 48)
                
                Circle()
                    .fill(appState.telemetry.status.color)
                    .frame(width: 14, height: 14)
            }
            
            VStack(alignment: .leading, spacing: 3) {
                HStack(spacing: 6) {
                    Text("State:")
                        .foregroundColor(AsterTheme.mutedText)
                    Text(appState.telemetry.status.rawValue)
                        .fontWeight(.bold)
                        .foregroundColor(appState.telemetry.status.color)
                }
                .font(.system(size: 15))
                
                Text("Companion: \(appState.activeProfile.name) • iPhone")
                    .font(.system(size: 13))
                    .foregroundColor(AsterTheme.mutedText)
            }
            
            Spacer()
            
            // Emergency Stop Button
            Button(action: {
                withAnimation { appState.stopAwareness() }
            }) {
                Text("Stop")
                    .font(.system(size: 13, weight: .bold))
                    .foregroundColor(AsterTheme.destructiveRed)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 8)
                    .background(AsterTheme.surface)
                    .clipShape(Capsule())
                    .overlay(Capsule().stroke(AsterTheme.destructiveRed.opacity(0.6), lineWidth: 1))
            }
        }
        .padding(16)
        .background(AsterTheme.surface)
        .clipShape(RoundedRectangle(cornerRadius: AsterTheme.radiusCard, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: AsterTheme.radiusCard).stroke(AsterTheme.outline, lineWidth: 1))
    }
    
    // MARK: - Broadcast Control Card
    private var broadcastControlCard: some View {
        HStack(alignment: .center, spacing: 16) {
            VStack(alignment: .leading, spacing: 4) {
                Text("ReplayKit Screen Broadcast")
                    .font(.system(size: 16, weight: .bold))
                    .foregroundColor(AsterTheme.creamText)
                
                Text("Tap the broadcast icon to launch Apple's native system picker.")
                    .font(.system(size: 13))
                    .foregroundColor(AsterTheme.mutedText)
            }
            
            Spacer()
            
            #if os(iOS)
            ReplayKitBroadcastPickerRepresentable()
                .frame(width: 50, height: 50)
                .background(AsterTheme.elevatedSurface)
                .clipShape(Circle())
                .overlay(Circle().stroke(AsterTheme.warmAmber, lineWidth: 1.5))
            #else
            Button(action: { appState.toggleScreenAwareness() }) {
                Image(systemName: "record.circle")
                    .font(.system(size: 24))
                    .foregroundColor(AsterTheme.warmAmber)
            }
            #endif
        }
        .padding(16)
        .background(AsterTheme.surface)
        .clipShape(RoundedRectangle(cornerRadius: AsterTheme.radiusCard, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: AsterTheme.radiusCard).stroke(AsterTheme.outline, lineWidth: 1))
    }
    
    // MARK: - Telemetry Grid (Honest Reporting, PRD Section 5.3)
    private var telemetryMetersGrid: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Realtime Perception Telemetry")
                .font(.system(size: 17, weight: .bold))
                .foregroundColor(AsterTheme.creamText)
            
            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                meterCard(
                    title: "Capture FPS",
                    value: String(format: "%.1f", appState.telemetry.captureFPS),
                    unit: "FPS",
                    note: "Aspirational 120 FPS target",
                    color: AsterTheme.onlineGreen
                )
                
                meterCard(
                    title: "Upload FPS",
                    value: String(format: "%.1f", appState.telemetry.uploadFPS),
                    unit: "FPS",
                    note: "Network encoded rate",
                    color: AsterTheme.warmAmber
                )
                
                meterCard(
                    title: "Analysis FPS",
                    value: String(format: "%.1f", appState.telemetry.analysisFPS),
                    unit: "FPS",
                    note: "Deep multimodal inference",
                    color: AsterTheme.restrainedViolet
                )
                
                meterCard(
                    title: "Pipeline Latency",
                    value: String(format: "%.0f", appState.telemetry.latencyMs),
                    unit: "ms",
                    note: "Perception-to-response",
                    color: AsterTheme.creamText
                )
            }
        }
    }
    
    private func meterCard(title: String, value: String, unit: String, note: String, color: Color) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(AsterTheme.mutedText)
            
            HStack(alignment: .lastTextBaseline, spacing: 4) {
                Text(value)
                    .font(.system(size: 24, weight: .bold))
                    .foregroundColor(color)
                Text(unit)
                    .font(.system(size: 12, weight: .regular))
                    .foregroundColor(AsterTheme.mutedText)
            }
            
            Text(note)
                .font(.system(size: 11, weight: .regular))
                .foregroundColor(AsterTheme.faintText)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(14)
        .background(AsterTheme.surface)
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 14).stroke(AsterTheme.outline, lineWidth: 1))
    }
    
    // MARK: - Quick Toggles
    private var quickTogglesSection: some View {
        VStack(spacing: 12) {
            Toggle(isOn: Binding(
                get: { !appState.telemetry.isScreenPaused },
                set: { _ in appState.toggleScreenAwareness() }
            )) {
                HStack(spacing: 12) {
                    Image(systemName: "display")
                        .foregroundColor(AsterTheme.warmAmber)
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Screen Capture Stream")
                            .font(.system(size: 15, weight: .medium))
                            .foregroundColor(AsterTheme.creamText)
                        Text("Pause instantly at any moment")
                            .font(.system(size: 12))
                            .foregroundColor(AsterTheme.mutedText)
                    }
                }
            }
            .toggleStyle(SwitchToggleStyle(tint: AsterTheme.warmAmber))
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .background(AsterTheme.surface)
            .clipShape(RoundedRectangle(cornerRadius: 14))
            
            Toggle(isOn: Binding(
                get: { !appState.telemetry.isAudioMuted },
                set: { _ in appState.toggleAudioAwareness() }
            )) {
                HStack(spacing: 12) {
                    Image(systemName: "mic.fill")
                        .foregroundColor(AsterTheme.warmAmber)
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Environmental Audio Stream")
                            .font(.system(size: 15, weight: .medium))
                            .foregroundColor(AsterTheme.creamText)
                        Text("Distinct opt-in for ambient speech")
                            .font(.system(size: 12))
                            .foregroundColor(AsterTheme.mutedText)
                    }
                }
            }
            .toggleStyle(SwitchToggleStyle(tint: AsterTheme.warmAmber))
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .background(AsterTheme.surface)
            .clipShape(RoundedRectangle(cornerRadius: 14))
        }
    }
    
    // MARK: - Privacy & Honest Disclosure
    private var privacyDisclosureCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 8) {
                Image(systemName: "hand.raised.shield.fill")
                    .foregroundColor(AsterTheme.warmAmber)
                Text("Honest Operating Boundary")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(AsterTheme.creamText)
            }
            
            Text("Aster strictly honors Apple ReplayKit constraints. There is zero silent background capture. Encrypted in transit, RLS-isolated per profile, with no indefinite raw video retention.")
                .font(.system(size: 12, weight: .regular))
                .foregroundColor(AsterTheme.mutedText)
                .lineSpacing(3)
        }
        .padding(16)
        .background(AsterTheme.elevatedSurface)
        .clipShape(RoundedRectangle(cornerRadius: 14))
        .overlay(RoundedRectangle(cornerRadius: 14).stroke(AsterTheme.outline, lineWidth: 1))
    }
}
