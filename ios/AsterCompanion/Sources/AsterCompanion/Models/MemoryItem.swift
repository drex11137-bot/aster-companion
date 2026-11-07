import SwiftUI

public enum MemoryCategory: String, CaseIterable, Identifiable, Codable {
    case all = "All"
    case people = "People"
    case preferences = "Preferences"
    case plans = "Plans"
    case health = "Health"
    
    public var id: String { rawValue }
}

public enum MemoryIconType: String, Codable {
    case sun
    case person
    case health
    case running
    case coffee
    case flower
    
    public var systemName: String {
        switch self {
        case .sun: return "sun.max"
        case .person: return "person"
        case .health: return "plus"
        case .running: return "figure.run"
        case .coffee: return "cup.and.saucer"
        case .flower: return "leaf"
        }
    }
}

public struct MemoryShareAudit: Codable, Equatable {
    public let sharedAt: Date
    public let sourceProfileId: UUID
    public let destinationProfileId: UUID
    public let confirmedByUserId: String
    
    public init(
        sharedAt: Date = Date(),
        sourceProfileId: UUID,
        destinationProfileId: UUID,
        confirmedByUserId: String
    ) {
        self.sharedAt = sharedAt
        self.sourceProfileId = sourceProfileId
        self.destinationProfileId = destinationProfileId
        self.confirmedByUserId = confirmedByUserId
    }
}

public struct MemoryItem: Identifiable, Codable, Equatable {
    public let id: UUID
    public let profileId: UUID
    public var title: String
    public var relativeTime: String
    public var category: MemoryCategory
    public var iconType: MemoryIconType
    public var imageThumbnailName: String?
    public var confidence: Double
    public var isExplicitlyShared: Bool
    public var shareAudit: MemoryShareAudit?
    public var createdAt: Date
    
    public init(
        id: UUID = UUID(),
        profileId: UUID,
        title: String,
        relativeTime: String,
        category: MemoryCategory,
        iconType: MemoryIconType,
        imageThumbnailName: String? = nil,
        confidence: Double = 0.98,
        isExplicitlyShared: Bool = false,
        shareAudit: MemoryShareAudit? = nil,
        createdAt: Date = Date()
    ) {
        self.id = id
        self.profileId = profileId
        self.title = title
        self.relativeTime = relativeTime
        self.category = category
        self.iconType = iconType
        self.imageThumbnailName = imageThumbnailName
        self.confidence = confidence
        self.isExplicitlyShared = isExplicitlyShared
        self.shareAudit = shareAudit
        self.createdAt = createdAt
    }
    
    public static func defaultMemories(for profileId: UUID) -> [MemoryItem] {
        [
            MemoryItem(
                profileId: profileId,
                title: "Prefers short answers\nin the morning",
                relativeTime: "Added 3 days ago",
                category: .preferences,
                iconType: .sun,
                imageThumbnailName: "coffee_memory"
            ),
            MemoryItem(
                profileId: profileId,
                title: "Dad's number saved",
                relativeTime: "Added 1 week ago",
                category: .people,
                iconType: .person
            ),
            MemoryItem(
                profileId: profileId,
                title: "Allergic to peanuts",
                relativeTime: "Added 2 weeks ago",
                category: .health,
                iconType: .health
            ),
            MemoryItem(
                profileId: profileId,
                title: "Running a half marathon\nin March",
                relativeTime: "Added 3 weeks ago",
                category: .plans,
                iconType: .running
            ),
            MemoryItem(
                profileId: profileId,
                title: "You love oat flat whites",
                relativeTime: "Noted 3 days ago",
                category: .preferences,
                iconType: .coffee,
                imageThumbnailName: "coffee_memory"
            ),
            MemoryItem(
                profileId: profileId,
                title: "Sister's birthday: Nov 14",
                relativeTime: "Added last week",
                category: .people,
                iconType: .flower,
                imageThumbnailName: "flowers_memory"
            )
        ]
    }
}
