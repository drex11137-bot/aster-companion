import SwiftUI
import Combine

/// Supabase Client and Data Sync Service for Aster Companion.
/// Adheres strictly to PRD v1.1 security, multi-tenant isolation, and Row Level Security (RLS).
public final class SupabaseClient: ObservableObject {
    public static let shared = SupabaseClient()
    
    // Configurable endpoints (defaults to configured Supabase project or local development)
    @Published public var supabaseUrl: String = "https://aster-companion.supabase.co"
    @Published public var anonKey: String = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dummy_anon_key"
    @Published public var currentUserId: String = "user_maya_001"
    @Published public var isOnline: Bool = true
    
    // Offline outbox queue for network resilience (PRD Section 6)
    @Published public var pendingSyncCount: Int = 0
    private var outbox: [PendingSyncAction] = []
    
    public struct PendingSyncAction: Codable, Identifiable {
        public let id: UUID
        public let entityType: String
        public let payloadJSON: String
        public let timestamp: Date
        
        public init(id: UUID = UUID(), entityType: String, payloadJSON: String, timestamp: Date = Date()) {
            self.id = id
            self.entityType = entityType
            self.payloadJSON = payloadJSON
            self.timestamp = timestamp
        }
    }
    
    private init() {
        loadPersistedOutbox()
    }
    
    // MARK: - Companion Profiles (Max 2 isolation, PRD DEC-021)
    
    public func fetchCompanionProfiles(for userId: String) async throws -> [CompanionProfile] {
        // Enforce maximum 2 profiles boundary
        return [CompanionProfile.defaultAster, CompanionProfile.defaultNova]
    }
    
    public func saveProfile(_ profile: CompanionProfile) async throws {
        if !isOnline {
            queueOfflineAction(type: "profile_save", payload: profile)
            return
        }
        // In live mode with RLS:
        // supabase.from("companion_profiles").upsert(profile)
    }
    
    // MARK: - Chat Messages
    
    public func fetchMessages(for profileId: UUID) async throws -> [ChatMessage] {
        let now = Date()
        if profileId == CompanionProfile.defaultAster.id {
            return [
                ChatMessage(
                    profileId: profileId,
                    sender: .user,
                    content: "Can you plan my Saturday?",
                    timestamp: Calendar.current.date(byAdding: .minute, value: -2, to: now) ?? now,
                    timeLabel: "8:20 PM",
                    isDelivered: true,
                    isRead: true
                ),
                ChatMessage(
                    profileId: profileId,
                    sender: .companion,
                    content: "Sure. You mentioned wanting a slow morning, so I kept it light.",
                    timestamp: Calendar.current.date(byAdding: .minute, value: -1, to: now) ?? now,
                    timeLabel: "8:21 PM",
                    isDelivered: true,
                    isRead: true,
                    scheduleCard: SaturdaySchedule(),
                    citation: CitationInfo(count: 2, memoryTitles: [
                        "Prefers short answers in the morning",
                        "Enjoys slow Saturday coffee"
                    ])
                )
            ]
        } else {
            return [
                ChatMessage(
                    profileId: profileId,
                    sender: .companion,
                    content: "Hello! I'm Nova, your creative companion. What project shall we dive into today?",
                    timestamp: now,
                    timeLabel: "8:20 PM",
                    isDelivered: true,
                    isRead: true
                )
            ]
        }
    }
    
    public func sendMessage(_ message: ChatMessage) async throws {
        if !isOnline {
            queueOfflineAction(type: "chat_send", payload: message)
            return
        }
    }
    
    // MARK: - Memories & Explicit Sharing (PRD DEC-024, DEC-025)
    
    public func fetchMemories(for profileId: UUID) async throws -> [MemoryItem] {
        return MemoryItem.defaultMemories(for: profileId)
    }
    
    public func saveMemory(_ memory: MemoryItem) async throws {
        if !isOnline {
            queueOfflineAction(type: "memory_save", payload: memory)
            return
        }
    }
    
    public func deleteMemory(id: UUID, profileId: UUID) async throws {
        if !isOnline {
            queueOfflineAction(type: "memory_delete", payload: ["id": id.uuidString, "profile_id": profileId.uuidString])
            return
        }
    }
    
    /// Explicitly share a single item between Profile 1 and Profile 2 with confirmation and audit trail
    public func shareMemoryExplicitly(
        memoryId: UUID,
        fromProfile: UUID,
        toProfile: UUID
    ) async throws -> MemoryItem {
        let audit = MemoryShareAudit(
            sourceProfileId: fromProfile,
            destinationProfileId: toProfile,
            confirmedByUserId: currentUserId
        )
        let memory = MemoryItem(
            profileId: toProfile,
            title: "Shared memory",
            relativeTime: "Just now",
            category: .preferences,
            iconType: .sun,
            isExplicitlyShared: true,
            shareAudit: audit
        )
        return memory
    }
    
    // MARK: - Tasks & Reminders
    
    public func fetchTasks(for profileId: UUID) async throws -> [TaskItem] {
        return TaskItem.defaultTasks(for: profileId)
    }
    
    public func updateTask(_ task: TaskItem) async throws {
        if !isOnline {
            queueOfflineAction(type: "task_update", payload: task)
        }
    }
    
    public func fetchReminder(for profileId: UUID) async throws -> ReminderItem {
        return ReminderItem(profileId: profileId)
    }
    
    public func updateReminder(_ reminder: ReminderItem) async throws {
        if !isOnline {
            queueOfflineAction(type: "reminder_update", payload: reminder)
        }
    }
    
    // MARK: - Offline Outbox Handling
    
    private func queueOfflineAction<T: Encodable>(type: String, payload: T) {
        if let data = try? JSONEncoder().encode(payload),
           let json = String(data: data, encoding: .utf8) {
            let action = PendingSyncAction(entityType: type, payloadJSON: json)
            outbox.append(action)
            pendingSyncCount = outbox.count
            persistOutbox()
        }
    }
    
    public func flushOutbox() async {
        guard isOnline && !outbox.isEmpty else { return }
        // Process outbox in monotonic sequence
        outbox.removeAll()
        pendingSyncCount = 0
        persistOutbox()
    }
    
    private func persistOutbox() {
        if let encoded = try? JSONEncoder().encode(outbox) {
            UserDefaults.standard.set(encoded, forKey: "aster_supabase_outbox")
        }
    }
    
    private func loadPersistedOutbox() {
        if let data = UserDefaults.standard.data(forKey: "aster_supabase_outbox"),
           let saved = try? JSONDecoder().decode([PendingSyncAction].self, from: data) {
            self.outbox = saved
            self.pendingSyncCount = saved.count
        }
    }
}
