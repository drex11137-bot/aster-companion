import SwiftUI

/// Multimodal Chat View conforming strictly to reference screenshot 3.
public struct ChatView: View {
    @ObservedObject var appState: AppState = AppState.shared
    @State private var inputText: String = ""
    @State private var showingCitationSheet: Bool = false
    @State private var selectedCitations: CitationInfo? = nil
    @State private var showingVoiceCall: Bool = false
    @State private var showingAwareness: Bool = false
    
    public init() {}
    
    public var body: some View {
        VStack(spacing: 0) {
            // MARK: - Header
            chatHeader
            
            Divider()
                .background(AsterTheme.outline)
            
            // MARK: - Message History List
            ScrollViewReader { proxy in
                ScrollView(.vertical, showsIndicators: false) {
                    LazyVStack(spacing: 16) {
                        // Date Separator
                        Text("Today 8:20 PM")
                            .font(.system(size: 13, weight: .regular))
                            .foregroundColor(AsterTheme.mutedText)
                            .padding(.top, 12)
                            .padding(.bottom, 4)
                        
                        // Message Bubbles
                        ForEach(appState.messages) { message in
                            messageBubble(message)
                                .id(message.id)
                        }
                    }
                    .padding(.horizontal, 16)
                    .padding(.bottom, 12)
                }
                .onChange(of: appState.messages.count) { _ in
                    if let lastMsg = appState.messages.last {
                        withAnimation {
                            proxy.scrollTo(lastMsg.id, anchor: .bottom)
                        }
                    }
                }
            }
            
            // MARK: - Quick Action Pills
            quickActionPills
            
            // MARK: - Input Composer Bar
            composerBar
                .padding(.horizontal, 16)
                .padding(.bottom, 12)
        }
        .background(AsterTheme.ground.ignoresSafeArea())
        .sheet(isPresented: $showingVoiceCall) {
            VoiceCallView()
        }
        .sheet(isPresented: $showingAwareness) {
            AwarenessView()
        }
        .sheet(item: $selectedCitations) { citation in
            CitationDetailSheet(citation: citation)
        }
    }
    
    // MARK: - Chat Header
    private var chatHeader: some View {
        HStack(spacing: 12) {
            // Companion Avatar with Halo and Green Dot
            ZStack(alignment: .bottomTrailing) {
                // Amber Halo
                Circle()
                    .fill(
                        RadialGradient(
                            gradient: Gradient(colors: [
                                AsterTheme.warmAmber.opacity(0.55),
                                AsterTheme.warmAmber.opacity(0.15),
                                Color.clear
                            ]),
                            center: .center,
                            startRadius: 4,
                            endRadius: 26
                        )
                    )
                    .frame(width: 52, height: 52)
                    .blur(radius: 4)
                
                Image(appState.activeProfile.avatarImageName, bundle: .main)
                    .resizable()
                    .aspectRatio(contentMode: .fill)
                    .frame(width: 44, height: 44)
                    .clipShape(Circle())
                    .overlay(Circle().stroke(AsterTheme.outline, lineWidth: 1))
                
                Circle()
                    .fill(AsterTheme.onlineGreen)
                    .frame(width: 12, height: 12)
                    .overlay(Circle().stroke(AsterTheme.ground, lineWidth: 2))
                    .offset(x: 1, y: 1)
            }
            
            // Name & Status
            VStack(alignment: .leading, spacing: 2) {
                Text(appState.activeProfile.name)
                    .font(.system(size: 18, weight: .bold))
                    .foregroundColor(AsterTheme.creamText)
                
                Text("Online")
                    .font(.system(size: 13, weight: .regular))
                    .foregroundColor(AsterTheme.mutedText)
            }
            
            Spacer()
            
            // Awareness Status / Shortcut Button
            Button(action: { showingAwareness = true }) {
                HStack(spacing: 4) {
                    Circle()
                        .fill(appState.telemetry.status.color)
                        .frame(width: 8, height: 8)
                    Text("Live")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(AsterTheme.creamText)
                }
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
                .background(AsterTheme.surface)
                .clipShape(Capsule())
                .overlay(Capsule().stroke(AsterTheme.outline, lineWidth: 1))
            }
            
            // Search Button
            Button(action: {}) {
                Image(systemName: "magnifyingglass")
                    .font(.system(size: 18, weight: .medium))
                    .foregroundColor(AsterTheme.creamText)
                    .padding(6)
            }
            
            // Menu / Call Button
            Button(action: { showingVoiceCall = true }) {
                Image(systemName: "ellipsis")
                    .font(.system(size: 18, weight: .medium))
                    .foregroundColor(AsterTheme.creamText)
                    .padding(6)
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
    }
    
    // MARK: - Message Bubble
    @ViewBuilder
    private func messageBubble(_ message: ChatMessage) -> some View {
        if message.sender == .user {
            // User Message (Restrained Violet)
            VStack(alignment: .trailing, spacing: 4) {
                Text(message.content)
                    .font(.system(size: 16, weight: .regular))
                    .foregroundColor(AsterTheme.creamText)
                    .padding(.horizontal, 18)
                    .padding(.vertical, 12)
                    .background(AsterTheme.restrainedViolet)
                    .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
                
                HStack(spacing: 4) {
                    Text(message.timeLabel)
                        .font(.system(size: 12, weight: .regular))
                        .foregroundColor(AsterTheme.mutedText)
                    
                    // Double Checks
                    HStack(spacing: -3) {
                        Image(systemName: "checkmark")
                        Image(systemName: "checkmark")
                    }
                    .font(.system(size: 10, weight: .bold))
                    .foregroundColor(AsterTheme.restrainedViolet)
                }
            }
            .frame(maxWidth: .infinity, alignment: .trailing)
        } else {
            // Companion Message (Dark Bubble + Schedule Card + Citations)
            HStack(alignment: .top, spacing: 8) {
                // Small Companion Avatar
                Image(appState.activeProfile.avatarImageName, bundle: .main)
                    .resizable()
                    .aspectRatio(contentMode: .fill)
                    .frame(width: 30, height: 30)
                    .clipShape(Circle())
                    .overlay(Circle().stroke(AsterTheme.outline, lineWidth: 1))
                    .padding(.top, 4)
                
                VStack(alignment: .leading, spacing: 10) {
                    // Text Bubble
                    Text(message.content)
                        .font(.system(size: 16, weight: .regular))
                        .foregroundColor(AsterTheme.creamText)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 12)
                        .background(AsterTheme.surface)
                        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
                        .overlay(
                            RoundedRectangle(cornerRadius: 18, style: .continuous)
                                .stroke(AsterTheme.outline, lineWidth: 1)
                        )
                    
                    // Rich Embedded Interactive Schedule Card
                    if let schedule = message.scheduleCard {
                        scheduleCardView(schedule)
                    }
                    
                    // Citation Chip: "Used 2 memories"
                    if let citation = message.citation {
                        Button(action: { selectedCitations = citation }) {
                            HStack(spacing: 6) {
                                Image(systemName: "doc.text")
                                    .font(.system(size: 13, weight: .medium))
                                Text("Used \(citation.count) memories")
                                    .font(.system(size: 13, weight: .medium))
                            }
                            .foregroundColor(AsterTheme.creamText)
                            .padding(.horizontal, 14)
                            .padding(.vertical, 7)
                            .background(AsterTheme.elevatedSurface)
                            .clipShape(Capsule())
                            .overlay(Capsule().stroke(AsterTheme.outline, lineWidth: 1))
                        }
                    }
                    
                    // Timestamp
                    Text(message.timeLabel)
                        .font(.system(size: 12, weight: .regular))
                        .foregroundColor(AsterTheme.mutedText)
                        .padding(.leading, 4)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }
    
    // MARK: - Interactive Saturday Schedule Card
    private func scheduleCardView(_ schedule: SaturdaySchedule) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            // Header
            VStack(alignment: .leading, spacing: 3) {
                Text(schedule.title)
                    .font(.system(size: 17, weight: .bold))
                    .foregroundColor(AsterTheme.creamText)
                
                Text(schedule.subtitle)
                    .font(.system(size: 13, weight: .regular))
                    .foregroundColor(AsterTheme.mutedText)
            }
            
            // Timeline Items with Connected Vertical Line
            VStack(alignment: .leading, spacing: 0) {
                ForEach(Array(schedule.items.enumerated()), id: \.element.id) { index, item in
                    HStack(alignment: .top, spacing: 14) {
                        // Timeline Line + Badge
                        VStack(spacing: 0) {
                            ZStack {
                                Circle()
                                    .fill(AsterTheme.elevatedSurface)
                                    .frame(width: 36, height: 36)
                                    .overlay(Circle().stroke(AsterTheme.outline, lineWidth: 1))
                                
                                Image(systemName: item.iconSystemName)
                                    .font(.system(size: 15, weight: .medium))
                                    .foregroundColor(AsterTheme.warmAmber)
                            }
                            
                            if index < schedule.items.count - 1 {
                                Rectangle()
                                    .fill(AsterTheme.outline)
                                    .frame(width: 2, height: 36)
                            }
                        }
                        
                        // Content
                        VStack(alignment: .leading, spacing: 2) {
                            Text(item.time)
                                .font(.system(size: 12, weight: .medium))
                                .foregroundColor(AsterTheme.mutedText)
                            
                            Text(item.title)
                                .font(.system(size: 15, weight: .semibold))
                                .foregroundColor(AsterTheme.creamText)
                            
                            Text(item.description)
                                .font(.system(size: 13, weight: .regular))
                                .foregroundColor(AsterTheme.mutedText)
                        }
                        .padding(.top, 2)
                        
                        Spacer()
                    }
                }
            }
        }
        .padding(18)
        .background(AsterTheme.surface)
        .clipShape(RoundedRectangle(cornerRadius: AsterTheme.radiusCard, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: AsterTheme.radiusCard, style: .continuous)
                .stroke(AsterTheme.outline, lineWidth: 1)
        )
    }
    
    // MARK: - Quick Action Pills
    private var quickActionPills: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 10) {
                // Add Reminder Pill
                Button(action: {
                    inputText = "Add reminder to "
                }) {
                    HStack(spacing: 6) {
                        Image(systemName: "calendar.badge.plus")
                            .font(.system(size: 13))
                        Text("Add reminder")
                            .font(.system(size: 13, weight: .medium))
                    }
                    .foregroundColor(AsterTheme.creamText)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 8)
                    .background(AsterTheme.surface)
                    .clipShape(Capsule())
                    .overlay(Capsule().stroke(AsterTheme.outline, lineWidth: 1))
                }
                
                // Summarize Pill
                Button(action: {
                    appState.sendMessage("Summarize today's highlights")
                }) {
                    HStack(spacing: 6) {
                        Image(systemName: "doc.plaintext")
                            .font(.system(size: 13))
                        Text("Summarize")
                            .font(.system(size: 13, weight: .medium))
                    }
                    .foregroundColor(AsterTheme.creamText)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 8)
                    .background(AsterTheme.surface)
                    .clipShape(Capsule())
                    .overlay(Capsule().stroke(AsterTheme.outline, lineWidth: 1))
                }
                
                // Voice Call Shortcut Pill
                Button(action: { showingVoiceCall = true }) {
                    HStack(spacing: 6) {
                        Image(systemName: "waveform")
                            .font(.system(size: 13))
                            .foregroundColor(AsterTheme.warmAmber)
                        Text("Voice Mode")
                            .font(.system(size: 13, weight: .medium))
                    }
                    .foregroundColor(AsterTheme.creamText)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 8)
                    .background(AsterTheme.surface)
                    .clipShape(Capsule())
                    .overlay(Capsule().stroke(AsterTheme.outline, lineWidth: 1))
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
        }
    }
    
    // MARK: - Input Composer Bar
    private var composerBar: some View {
        HStack(spacing: 10) {
            // Text Input Container
            HStack(spacing: 10) {
                TextField("Message \(appState.activeProfile.name)", text: $inputText)
                    .font(.system(size: 15, weight: .regular))
                    .foregroundColor(AsterTheme.creamText)
                    .accentColor(AsterTheme.warmAmber)
                
                // Microphone Button
                Button(action: { showingVoiceCall = true }) {
                    Image(systemName: "mic.fill")
                        .font(.system(size: 17, weight: .medium))
                        .foregroundColor(AsterTheme.mutedText)
                }
            }
            .padding(.horizontal, 18)
            .padding(.vertical, 12)
            .background(AsterTheme.surface)
            .clipShape(Capsule())
            .overlay(Capsule().stroke(AsterTheme.outline, lineWidth: 1))
            
            // Warm Amber Circular Send Button
            Button(action: {
                let text = inputText
                inputText = ""
                appState.sendMessage(text)
            }) {
                ZStack {
                    Circle()
                        .fill(AsterTheme.warmAmber)
                        .frame(width: 44, height: 44)
                    
                    Image(systemName: "arrow.right")
                        .font(.system(size: 17, weight: .bold))
                        .foregroundColor(AsterTheme.ground)
                }
            }
            .disabled(inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            .opacity(inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? 0.6 : 1.0)
        }
    }
}

// MARK: - Citation Detail Sheet
struct CitationDetailSheet: View, Identifiable {
    var id: String { citation.memoryTitles.joined() }
    let citation: CitationInfo
    @Environment(\.dismiss) var dismiss
    
    var body: some View {
        NavigationStack {
            ZStack {
                AsterTheme.ground.ignoresSafeArea()
                
                VStack(alignment: .leading, spacing: 16) {
                    Text("Aster referenced these memories to construct this response:")
                        .font(.system(size: 14))
                        .foregroundColor(AsterTheme.mutedText)
                        .padding(.horizontal)
                        .padding(.top)
                    
                    ForEach(citation.memoryTitles, id: \.self) { title in
                        HStack(spacing: 12) {
                            Image(systemName: "checkmark.seal.fill")
                                .foregroundColor(AsterTheme.warmAmber)
                            Text(title)
                                .font(.system(size: 15, weight: .medium))
                                .foregroundColor(AsterTheme.creamText)
                            Spacer()
                        }
                        .padding()
                        .background(AsterTheme.surface)
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                        .overlay(RoundedRectangle(cornerRadius: 12).stroke(AsterTheme.outline, lineWidth: 1))
                        .padding(.horizontal)
                    }
                    
                    Spacer()
                }
            }
            .navigationTitle("Cited Memories")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                        .foregroundColor(AsterTheme.warmAmber)
                }
            }
        }
    }
}
