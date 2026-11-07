import SwiftUI

public struct TaskItem: Identifiable, Codable, Equatable {
    public let id: UUID
    public let profileId: UUID
    public var title: String
    public var dueDateLabel: String
    public var isCompleted: Bool
    
    public init(
        id: UUID = UUID(),
        profileId: UUID,
        title: String,
        dueDateLabel: String,
        isCompleted: Bool = false
    ) {
        self.id = id
        self.profileId = profileId
        self.title = title
        self.dueDateLabel = dueDateLabel
        self.isCompleted = isCompleted
    }
    
    public static func defaultTasks(for profileId: UUID) -> [TaskItem] {
        [
            TaskItem(profileId: profileId, title: "Book dentist", dueDateLabel: "Today", isCompleted: false),
            TaskItem(profileId: profileId, title: "Finish budget draft", dueDateLabel: "Tomorrow", isCompleted: false),
            TaskItem(profileId: profileId, title: "Pick up parcel", dueDateLabel: "This week", isCompleted: false)
        ]
    }
}
