import SwiftUI
import Combine

public enum AsterTab: String, CaseIterable, Identifiable {
    case today = "Today"
    case chat = "Chat"
    case memory = "Memory"
    case companion = "Companion"
    
    public var id: String { rawValue }
    
    public var iconName: String {
        switch self {
        case .today: return "house.fill"
        case .chat: return "message"
        case .memory: return "book.pages"
        case .companion: return "person.fill"
        }
    }
}

/// Central App State for Aster Companion.
/// Coordinates profiles, sessions, local offline caching, and real-time updates.
@MainActor
public final class AppState: ObservableObject {
    public static let shared = AppState()
    
    // MARK: - User Information
    @Published public var userName: String = "Maya"
    @Published public var selectedTab: AsterTab = .today
    
    // MARK: - Companion Profiles (Max 2 Isolation, PRD DEC-021)
    @Published public var profiles: [CompanionProfile] = [
        CompanionProfile.defaultAster,
        CompanionProfile.defaultNova
    ]
    @Published public var activeProfileId: UUID = CompanionProfile.defaultAster.id
    
    public var activeProfile: CompanionProfile {
        profiles.first(where: { $0.id == activeProfileId }) ?? CompanionProfile.defaultAster
    }
    
    // MARK: - Profile Isolated Data
    @Published public var messages: [ChatMessage] = []
    @Published public var memories: [MemoryItem] = []
    @Published public var tasks: [TaskItem] = []
    @Published public var nextReminder: ReminderItem
    
    // MARK: - Awareness Telemetry
    @Published public var telemetry: AwarenessTelemetry = AwarenessTelemetry()
    @Published public var isAwarenessSheetPresented: Bool = false
    
    // MARK: - Voice Call State
    @Published public var isVoiceCallActive: Bool = false
    @Published public var isMicMuted: Bool = false
    @Published public var isSpeakerOn: Bool = true
    @Published public var audioWaveformLevel: CGFloat = 0.2
    @Published public var liveTranscript: [String] = [
        "Maya: Can we go through my schedule?",
        "Aster: Absolutely, I've cleared the morning for you."
    ]
    
    // MARK: - Offline & Sync Status
    @Published public var isOffline: Bool = false
    @Published public var lastSavedTimestamp: Date = Date()
    
    private var cancellables = Set<AnyCancellable>()
    private var visualizerTimer: Timer?
    
    private init() {
        self.nextReminder = ReminderItem(profileId: CompanionProfile.defaultAster.id)
        loadInitialDataForActiveProfile()
    }
    
    // MARK: - Profile Switching & Isolation (PRD Section 9.6)
    
    /// Switches the active profile on this device.
    /// Strictly suspends previous session without context transfer.
    public func switchProfile(to profileId: UUID) {
        guard profileId != activeProfileId else { return }
        guard profiles.contains(where: { $0.id == profileId }) else { return }
        
        // 1. Suspend active voice/awareness if running
        if isVoiceCallActive {
            endVoiceCall()
        }
        
        // 2. Set new active profile ID
        activeProfileId = profileId
        
        // 3. Load cleanly isolated data for the new profile
        loadInitialDataForActiveProfile()
    }
    
    public func loadInitialDataForActiveProfile() {
        Task {
            do {
                let msgs = try await SupabaseClient.shared.fetchMessages(for: activeProfileId)
                let mems = try await SupabaseClient.shared.fetchMemories(for: activeProfileId)
                let tsks = try await SupabaseClient.shared.fetchTasks(for: activeProfileId)
                let rem = try await SupabaseClient.shared.fetchReminder(for: activeProfileId)
                
                await MainActor.run {
                    self.messages = msgs
                    self.memories = mems
                    self.tasks = tsks
                    self.nextReminder = rem
                }
            } catch {
                print("Error loading profile data: \(error)")
            }
        }
    }
    
    // MARK: - Studio Customization
    
    public func updateActiveProfileName(_ newName: String) {
        guard let index = profiles.firstIndex(where: { $0.id == activeProfileId }) else { return }
        profiles[index].name = newName.trimmingCharacters(in: .whitespacesAndNewlines)
        profiles[index].updatedAt = Date()
    }
    
    public func updateActiveProfileHair(_ hair: HairColor) {
        guard let index = profiles.firstIndex(where: { $0.id == activeProfileId }) else { return }
        profiles[index].hairColor = hair
        profiles[index].updatedAt = Date()
    }
    
    public func updateActiveProfileEyes(_ eyes: EyeColor) {
        guard let index = profiles.firstIndex(where: { $0.id == activeProfileId }) else { return }
        profiles[index].eyeColor = eyes
        profiles[index].updatedAt = Date()
    }
    
    public func updateActiveProfileStyle(_ style: CompanionStyle) {
        guard let index = profiles.firstIndex(where: { $0.id == activeProfileId }) else { return }
        profiles[index].style = style
        profiles[index].updatedAt = Date()
    }
    
    public func updateActiveProfileVoice(_ voice: VoiceOption) {
        guard let index = profiles.firstIndex(where: { $0.id == activeProfileId }) else { return }
        profiles[index].voice = voice
        profiles[index].updatedAt = Date()
    }
    
    public func saveActiveProfile() {
        guard let profile = profiles.first(where: { $0.id == activeProfileId }) else { return }
        lastSavedTimestamp = Date()
        Task {
            try? await SupabaseClient.shared.saveProfile(profile)
        }
    }
    
    // MARK: - Chat Actions
    
    public func sendMessage(_ text: String) {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        
        let userMsg = ChatMessage(
            profileId: activeProfileId,
            sender: .user,
            content: trimmed,
            timestamp: Date(),
            timeLabel: formattedCurrentTime(),
            isDelivered: true,
            isRead: true
        )
        messages.append(userMsg)
        
        // Intelligent contextual response
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.8) {
            let companionName = self.activeProfile.name
            let reply: ChatMessage
            
            if trimmed.localizedCaseInsensitiveContains("schedule") || trimmed.localizedCaseInsensitiveContains("saturday") {
                reply = ChatMessage(
                    profileId: self.activeProfileId,
                    sender: .companion,
                    content: "Sure. You mentioned wanting a slow morning, so I kept it light.",
                    timestamp: Date(),
                    timeLabel: self.formattedCurrentTime(),
                    isDelivered: true,
                    isRead: true,
                    scheduleCard: SaturdaySchedule(),
                    citation: CitationInfo(count: 2, memoryTitles: [
                        "Prefers short answers in the morning",
                        "Enjoys slow Saturday coffee"
                    ])
                )
            } else if trimmed.localizedCaseInsensitiveContains("reminder") {
                reply = ChatMessage(
                    profileId: self.activeProfileId,
                    sender: .companion,
                    content: "I've added that to your reminders for today.",
                    timestamp: Date(),
                    timeLabel: self.formattedCurrentTime(),
                    isDelivered: true,
                    isRead: true
                )
            } else {
                reply = ChatMessage(
                    profileId: self.activeProfileId,
                    sender: .companion,
                    content: "I've noted that, Maya. Anything else you'd like me to look into?",
                    timestamp: Date(),
                    timeLabel: self.formattedCurrentTime(),
                    isDelivered: true,
                    isRead: true
                )
            }
            self.messages.append(reply)
        }
    }
    
    // MARK: - Memory Management & Explicit Sharing (PRD Section 9.4)
    
    public func addMemory(title: String, category: MemoryCategory, iconType: MemoryIconType) {
        let newMemory = MemoryItem(
            profileId: activeProfileId,
            title: title,
            relativeTime: "Just now",
            category: category,
            iconType: iconType
        )
        memories.insert(newMemory, at: 0)
        Task {
            try? await SupabaseClient.shared.saveMemory(newMemory)
        }
    }
    
    public func updateMemory(_ memory: MemoryItem) {
        guard let index = memories.firstIndex(where: { $0.id == memory.id }) else { return }
        memories[index] = memory
        Task {
            try? await SupabaseClient.shared.saveMemory(memory)
        }
    }
    
    public func deleteMemory(id: UUID) {
        memories.removeAll(where: { $0.id == id })
        Task {
            try? await SupabaseClient.shared.deleteMemory(id: id, profileId: activeProfileId)
        }
    }
    
    public func explicitlyShareMemory(memory: MemoryItem) {
        // Find other profile
        guard let otherProfile = profiles.first(where: { $0.id != activeProfileId }) else { return }
        Task {
            let shared = try? await SupabaseClient.shared.shareMemoryExplicitly(
                memoryId: memory.id,
                fromProfile: activeProfileId,
                toProfile: otherProfile.id
            )
            if let shared = shared {
                print("Explicitly shared memory \(shared.id) with profile \(otherProfile.name)")
            }
        }
    }
    
    // MARK: - Task & Reminder Actions
    
    public func toggleTask(_ task: TaskItem) {
        guard let index = tasks.firstIndex(where: { $0.id == task.id }) else { return }
        tasks[index].isCompleted.toggle()
        let updated = tasks[index]
        Task {
            try? await SupabaseClient.shared.updateTask(updated)
        }
    }
    
    public func snoozeReminder() {
        nextReminder.isSnoozed = true
        nextReminder.snoozeMinutes += 15
        nextReminder.title = "Call Dad at 7:45 PM"
        Task {
            try? await SupabaseClient.shared.updateReminder(nextReminder)
        }
    }
    
    // MARK: - Awareness Controls
    
    public func toggleScreenAwareness() {
        telemetry.isScreenPaused.toggle()
        telemetry.status = telemetry.isScreenPaused ? .paused : .active
    }
    
    public func toggleAudioAwareness() {
        telemetry.isAudioMuted.toggle()
    }
    
    public func stopAwareness() {
        telemetry.status = .idle
        telemetry.isScreenPaused = true
    }
    
    // MARK: - Voice Call Simulation
    
    public func startVoiceCall() {
        isVoiceCallActive = true
        startVisualizerAnimation()
    }
    
    public func endVoiceCall() {
        isVoiceCallActive = false
        visualizerTimer?.invalidate()
        visualizerTimer = nil
    }
    
    private func startVisualizerAnimation() {
        visualizerTimer?.invalidate()
        visualizerTimer = Timer.scheduledTimer(withTimeInterval: 0.08, repeats: true) { [weak self] _ in
            guard let self = self else { return }
            self.audioWaveformLevel = CGFloat.random(in: 0.15...0.95)
        }
    }
    
    private func formattedCurrentTime() -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "h:mm a"
        return formatter.string(from: Date())
    }
}
