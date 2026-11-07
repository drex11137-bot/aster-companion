import SwiftUI

/// Hair color swatch options matching reference screenshot
public enum HairColor: String, CaseIterable, Identifiable, Codable {
    case auburn = "Auburn"
    case black = "Black"
    case brown = "Brown"
    case blonde = "Blonde"
    case silver = "Silver"
    
    public var id: String { rawValue }
    
    public var color: Color {
        switch self {
        case .auburn: return Color(hex: "7A3E26")
        case .black: return Color(hex: "1F1F1F")
        case .brown: return Color(hex: "4A3728")
        case .blonde: return Color(hex: "D9C58F")
        case .silver: return Color(hex: "9E9E9E")
        }
    }
}

/// Eye color swatch options matching reference screenshot
public enum EyeColor: String, CaseIterable, Identifiable, Codable {
    case hazel = "Hazel"
    case brown = "Brown"
    case blue = "Blue"
    case green = "Green"
    case grey = "Grey"
    
    public var id: String { rawValue }
    
    public var color: Color {
        switch self {
        case .hazel: return Color(hex: "8C6239")
        case .brown: return Color(hex: "3B2219")
        case .blue: return Color(hex: "4A6B82")
        case .green: return Color(hex: "4D5D3B")
        case .grey: return Color(hex: "6B7280")
        }
    }
}

/// Companion conversational style chips matching reference screenshot
public enum CompanionStyle: String, CaseIterable, Identifiable, Codable {
    case natural = "Natural"
    case casual = "Casual"
    case professional = "Professional"
    case creative = "Creative"
    
    public var id: String { rawValue }
}

/// Companion voice chips matching reference screenshot
public enum VoiceOption: String, CaseIterable, Identifiable, Codable {
    case warmVoice = "Warm voice"
    case calm = "Calm"
    case energetic = "Energetic"
    case playful = "Playful"
    
    public var id: String { rawValue }
}

/// Companion Profile model.
/// Per PRD DEC-021: Exactly maximum 2 isolated profiles per user account.
public struct CompanionProfile: Identifiable, Codable, Equatable {
    public let id: UUID
    public var name: String
    public var avatarImageName: String
    public var hairColor: HairColor
    public var eyeColor: EyeColor
    public var style: CompanionStyle
    public var voice: VoiceOption
    public var isOnline: Bool
    public var createdAt: Date
    public var updatedAt: Date
    
    public init(
        id: UUID = UUID(),
        name: String,
        avatarImageName: String,
        hairColor: HairColor = .auburn,
        eyeColor: EyeColor = .hazel,
        style: CompanionStyle = .natural,
        voice: VoiceOption = .warmVoice,
        isOnline: Bool = true,
        createdAt: Date = Date(),
        updatedAt: Date = Date()
    ) {
        self.id = id
        self.name = name
        self.avatarImageName = avatarImageName
        self.hairColor = hairColor
        self.eyeColor = eyeColor
        self.style = style
        self.voice = voice
        self.isOnline = isOnline
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }
    
    /// Default isolated profile 1 ("Aster")
    public static let defaultAster = CompanionProfile(
        id: UUID(uuidString: "11111111-1111-1111-1111-111111111111") ?? UUID(),
        name: "Aster",
        avatarImageName: "aster_avatar",
        hairColor: .auburn,
        eyeColor: .hazel,
        style: .natural,
        voice: .warmVoice,
        isOnline: true
    )
    
    /// Default isolated profile 2 ("Nova")
    public static let defaultNova = CompanionProfile(
        id: UUID(uuidString: "22222222-2222-2222-2222-222222222222") ?? UUID(),
        name: "Nova",
        avatarImageName: "nova_avatar",
        hairColor: .black,
        eyeColor: .brown,
        style: .creative,
        voice: .playful,
        isOnline: true
    )
}
