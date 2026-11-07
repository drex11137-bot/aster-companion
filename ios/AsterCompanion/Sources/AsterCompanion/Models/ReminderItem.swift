import SwiftUI

public struct ReminderItem: Identifiable, Codable, Equatable {
    public let id: UUID
    public let profileId: UUID
    public var title: String
    public var dateLabel: String
    public var isSnoozed: Bool
    public var snoozeMinutes: Int
    public var isCompleted: Bool
    
    public init(
        id: UUID = UUID(),
        profileId: UUID,
        title: String = "Call Dad at 7:30 PM",
        dateLabel: String = "Today",
        isSnoozed: Bool = false,
        snoozeMinutes: Int = 15,
        isCompleted: Bool = false
    ) {
        self.id = id
        self.profileId = profileId
        self.title = title
        self.dateLabel = dateLabel
        self.isSnoozed = isSnoozed
        self.snoozeMinutes = snoozeMinutes
        self.isCompleted = isCompleted
    }
}
