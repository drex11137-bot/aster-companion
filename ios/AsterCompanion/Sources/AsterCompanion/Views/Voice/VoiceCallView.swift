import SwiftUI

/// Full-Duplex Realtime Voice Call View with Ambient Visualizer and Live Transcript.
/// Conforms to PRD Section 7 & 10.
public struct VoiceCallView: View {
    @ObservedObject var appState: AppState = AppState.shared
    @Environment(\.dismiss) var dismiss
    
    // Waveform animation phase
    @State private var wavePhase: Double = 0.0
    @State private var pulseScale: CGFloat = 1.0
    @State private var isListening: Bool = false
    
    public init() {}
    
    public var body: some View {
        ZStack {
            AsterTheme.ground.ignoresSafeArea()
            
            VStack(spacing: 24) {
                // MARK: - Header
                callHeader
                    .padding(.top, 20)
                
                Spacer()
                
                // MARK: - Ambient Sound-Reactive Fluid Visualizer
                ambientVisualizer
                    .frame(height: 280)
                
                Spacer()
                
                // MARK: - Live Streaming Transcript & Barge-in Indicator
                transcriptSection
                
                // MARK: - Call Controls Toolbar
                callControls
                    .padding(.bottom, 30)
            }
            .padding(.horizontal, 24)
        }
        .onAppear {
            appState.startVoiceCall()
            startAnimationLoop()
        }
        .onDisappear {
            appState.endVoiceCall()
        }
    }
    
    // MARK: - Header
    private var callHeader: some View {
        VStack(spacing: 8) {
            ZStack {
                Circle()
                    .fill(AsterTheme.warmAmber.opacity(0.3))
                    .frame(width: 74, height: 74)
                    .blur(radius: 8)
                
                Image(appState.activeProfile.avatarImageName, bundle: .main)
                    .resizable()
                    .aspectRatio(contentMode: .fill)
                    .frame(width: 60, height: 60)
                    .clipShape(Circle())
                    .overlay(Circle().stroke(AsterTheme.outline, lineWidth: 1.5))
            }
            
            Text(appState.activeProfile.name)
                .font(.system(size: 22, weight: .bold))
                .foregroundColor(AsterTheme.creamText)
            
            HStack(spacing: 6) {
                Circle()
                    .fill(AsterTheme.onlineGreen)
                    .frame(width: 8, height: 8)
                Text("Connected • Low Latency Realtime")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(AsterTheme.mutedText)
            }
        }
    }
    
    // MARK: - Ambient Sound-Reactive Visualizer
    private var ambientVisualizer: some View {
        ZStack {
            // Layer 1: Outermost Violet Radial Glow
            Circle()
                .fill(
                    RadialGradient(
                        gradient: Gradient(colors: [
                            AsterTheme.restrainedViolet.opacity(0.40),
                            AsterTheme.restrainedViolet.opacity(0.10),
                            Color.clear
                        ]),
                        center: .center,
                        startRadius: 40,
                        endRadius: 150
                    )
                )
                .scaleEffect(pulseScale * (1.0 + appState.audioWaveformLevel * 0.25))
                .blur(radius: 20)
            
            // Layer 2: Warm Amber Core Aura
            Circle()
                .fill(
                    RadialGradient(
                        gradient: Gradient(colors: [
                            AsterTheme.warmAmber.opacity(0.70),
                            AsterTheme.warmAmber.opacity(0.25),
                            Color.clear
                        ]),
                        center: .center,
                        startRadius: 20,
                        endRadius: 110
                    )
                )
                .scaleEffect(pulseScale * (0.9 + appState.audioWaveformLevel * 0.35))
                .blur(radius: 12)
            
            // Layer 3: Concentric Waveform Rings
            ForEach(0..<3) { i in
                Circle()
                    .stroke(
                        i % 2 == 0 ? AsterTheme.warmAmber.opacity(0.6) : AsterTheme.restrainedViolet.opacity(0.6),
                        lineWidth: 2
                    )
                    .frame(width: CGFloat(90 + i * 40), height: CGFloat(90 + i * 40))
                    .scaleEffect(1.0 + (appState.audioWaveformLevel * CGFloat(i + 1) * 0.15))
                    .rotationEffect(.degrees(wavePhase + Double(i * 45)))
            }
            
            // Center Floating Orb
            Circle()
                .fill(
                    LinearGradient(
                        gradient: Gradient(colors: [
                            AsterTheme.warmAmber,
                            AsterTheme.restrainedViolet
                        ]),
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .frame(width: 80, height: 80)
                .shadow(color: AsterTheme.warmAmber.opacity(0.6), radius: 16)
                .scaleEffect(1.0 + appState.audioWaveformLevel * 0.15)
        }
    }
    
    // MARK: - Live Transcript & Barge-in Status
    private var transcriptSection: some View {
        VStack(spacing: 8) {
            // Barge-in Status Pill
            HStack(spacing: 6) {
                Circle()
                    .fill(appState.audioWaveformLevel > 0.5 ? AsterTheme.warmAmber : AsterTheme.onlineGreen)
                    .frame(width: 6, height: 6)
                Text(appState.audioWaveformLevel > 0.5 ? "\(appState.activeProfile.name) is speaking..." : "Listening for you (Barge-in ready)...")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(AsterTheme.creamText)
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 6)
            .background(AsterTheme.surface)
            .clipShape(Capsule())
            .overlay(Capsule().stroke(AsterTheme.outline, lineWidth: 1))
            
            // Transcript Box
            VStack(alignment: .leading, spacing: 6) {
                ForEach(appState.liveTranscript, id: \.self) { line in
                    Text(line)
                        .font(.system(size: 14, weight: .regular))
                        .foregroundColor(AsterTheme.creamText)
                        .lineLimit(2)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(14)
            .background(AsterTheme.surface.opacity(0.7))
            .clipShape(RoundedRectangle(cornerRadius: 14))
            .overlay(RoundedRectangle(cornerRadius: 14).stroke(AsterTheme.outline, lineWidth: 1))
        }
    }
    
    // MARK: - Call Controls
    private var callControls: some View {
        HStack(spacing: 24) {
            // Mute Button
            Button(action: {
                withAnimation { appState.isMicMuted.toggle() }
            }) {
                ZStack {
                    Circle()
                        .fill(appState.isMicMuted ? AsterTheme.warmAmber : AsterTheme.surface)
                        .frame(width: 56, height: 56)
                        .overlay(Circle().stroke(AsterTheme.outline, lineWidth: 1))
                    
                    Image(systemName: appState.isMicMuted ? "mic.slash.fill" : "mic.fill")
                        .font(.system(size: 20))
                        .foregroundColor(appState.isMicMuted ? AsterTheme.ground : AsterTheme.creamText)
                }
            }
            
            // Speaker Button
            Button(action: {
                withAnimation { appState.isSpeakerOn.toggle() }
            }) {
                ZStack {
                    Circle()
                        .fill(appState.isSpeakerOn ? AsterTheme.elevatedSurface : AsterTheme.surface)
                        .frame(width: 56, height: 56)
                        .overlay(Circle().stroke(AsterTheme.outline, lineWidth: 1))
                    
                    Image(systemName: appState.isSpeakerOn ? "speaker.wave.3.fill" : "speaker.slash.fill")
                        .font(.system(size: 20))
                        .foregroundColor(AsterTheme.creamText)
                }
            }
            
            // End Call Button (Destructive Red)
            Button(action: {
                appState.endVoiceCall()
                dismiss()
            }) {
                ZStack {
                    Circle()
                        .fill(AsterTheme.destructiveRed)
                        .frame(width: 64, height: 64)
                        .shadow(color: AsterTheme.destructiveRed.opacity(0.5), radius: 10)
                    
                    Image(systemName: "phone.down.fill")
                        .font(.system(size: 24, weight: .bold))
                        .foregroundColor(AsterTheme.creamText)
                }
            }
        }
    }
    
    private func startAnimationLoop() {
        withAnimation(Animation.linear(duration: 8.0).repeatForever(autoreverses: false)) {
            wavePhase = 360.0
        }
        withAnimation(Animation.easeInOut(duration: 2.0).repeatForever(autoreverses: true)) {
            pulseScale = 1.15
        }
    }
}
