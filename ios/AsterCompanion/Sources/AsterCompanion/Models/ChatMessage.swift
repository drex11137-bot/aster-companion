import SwiftUI

public enum MessageSender: String, Codable {
    case user
    case companion
}

public struct ScheduleTimelineItem: Identifiable, Codable, Equatable {
    public let id: UUID
    public var time: String
    public var title: String
    public var description: String
    public var iconSystemName: String
    public var isCompleted: Bool
    
    public init(
        id: UUID = UUID(),
        time: String,
        title: String,
        description: String,
        iconSystemName: String,
        isCompleted: Bool = false
    ) {
        self.id = id
        self.time = time
        self.title = title
        self.description = description
        self.iconSystemName = iconSystemName
        self.isCompleted = isCompleted
    }
}

public struct SaturdaySchedule: Codable, Equatable {
    public var title: String
    public var subtitle: String
    public var items: [ScheduleTimelineItem]
    
    public init(
        title: String = "Saturday, Nov 15",
        subtitle: String = "A calm and balanced day",
        items: [ScheduleTimelineItem] = SaturdaySchedule.defaultItems
    ) {
        self.title = title
        self.subtitle = subtitle
        self.items = items
    }
    
    public static let defaultItems: [ScheduleTimelineItem] = [
        ScheduleTimelineItem(
            time: "9:00 AM",
            title: "Slow morning",
            description: "Coffee, a good book, no rush",
            iconSystemName: "cup.and.saucer.fill"
        ),
        ScheduleTimelineItem(
            time: "11:30 AM",
            title: "Gentle workout",
            description: "Yoga or a walk outside",
            iconSystemName: "dumbbell.fill"
        ),
        ScheduleTimelineItem(
            time: "1:00 PM",
            title: "Lunch",
            description: "Something fresh and local",
            iconSystemName: "fork.knife"
        ),
        ScheduleTimelineItem(
            time: "3:00 PM",
            title: "Personal time",
            description: "Read, journal, or a creative project",
            iconSystemName: "book.fill"
        ),
        ScheduleTimelineItem(
            time: "7:00 PM",
            title: "Wind down",
            description: "A quiet evening",
            iconSystemName: "moon.fill"
        )
    ]
}

public struct CitationInfo: Codable, Equatable {
    public var count: Int
    public var memoryTitles: [String]
    
    public init(count: Int = 2, memoryTitles: [String] = ["Prefers short answers in the morning", "Enjoys slow Saturday coffee"]) {
        self.count = count
        self.memoryTitles = memoryTitles
    }
}

public struct ChatMessage: Identifiable, Codable, Equatable {
    public let id: UUID
    public let profileId: UUID
    public var sender: MessageSender
    public var content: String
    public var timestamp: Date
    public var timeLabel: String
    public var isDelivered: Bool
    public var isRead: Bool
    public var scheduleCard: SaturdaySchedule?
    public var citation: CitationInfo?
    
    public init(
        id: UUID = UUID(),
        profileId: UUID,
        sender: MessageSender,
        content: String,
        timestamp: Date = Date(),
        timeLabel: String,
        isDelivered: Bool = true,
        isRead: Bool = true,
        scheduleCard: SaturdaySchedule? = nil,
        citation: CitationInfo? = nil
    ) {
        self.id = id
        self.profileId = profileId
        self.sender = sender
        self.content = content
        self.timestamp = timestamp
        self.timeLabel = timeLabel
        self.isDelivered = isDelivered
        self.isRead = isRead
        self.scheduleCard = scheduleCard
        self.citation = citation
    }
}
