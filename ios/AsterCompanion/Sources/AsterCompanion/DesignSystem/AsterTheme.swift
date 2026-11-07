import SwiftUI

/// Aster Companion authoritative design tokens and styling system.
/// Strictly conforms to PRD v1.1 and reference screenshots.
public enum AsterTheme {
    // MARK: - Primary Color Tokens
    
    /// Graphite / Black screen ground base (#121110)
    public static let ground = Color(hex: "121110")
    
    /// Laboratory and card surface (#1C1A18)
    public static let surface = Color(hex: "1C1A18")
    
    /// Slightly elevated surface for dialogs, pills, inputs (#242220)
    public static let elevatedSurface = Color(hex: "242220")
    
    /// Pressed or focused item surface (#2D2A27)
    public static let activeSurface = Color(hex: "2D2A27")
    
    /// Warm Amber signature accent (#E59843)
    public static let warmAmber = Color(hex: "E59843")
    
    /// Warm Amber glow tint for radiant halos and ambient visualizers
    public static let warmAmberGlow = Color(hex: "E59843").opacity(0.40)
    
    /// Restrained Violet signature chat & accent (#7966F3)
    public static let restrainedViolet = Color(hex: "7966F3")
    
    /// Cream high-contrast text (#FAF8F5) - 15:1 AAA contrast
    public static let creamText = Color(hex: "FAF8F5")
    
    /// Secondary muted typography ink (#A09D98) - 6.5:1 AA contrast
    public static let mutedText = Color(hex: "A09D98")
    
    /// Tertiary faint label ink (#6C6863)
    public static let faintText = Color(hex: "6C6863")
    
    /// Online telemetry emerald green (#34D399)
    public static let onlineGreen = Color(hex: "34D399")
    
    /// 1px Structural divider rule (#2B2825)
    public static let outline = Color(hex: "2B2825")
    
    /// Focused or interactive control border (#48443F)
    public static let outlineActive = Color(hex: "48443F")
    
    /// Destructive signal red (#EF4444)
    public static let destructiveRed = Color(hex: "EF4444")
    
    // MARK: - Corner Radii
    public static let radiusSmall: CGFloat = 8
    public static let radiusCard: CGFloat = 18
    public static let radiusDialog: CGFloat = 24
    public static let radiusPill: CGFloat = 9999
    
    // MARK: - Spacing Tokens
    public static let spacingXXS: CGFloat = 2
    public static let spacingXS: CGFloat = 4
    public static let spacingSM: CGFloat = 8
    public static let spacingMD: CGFloat = 16
    public static let spacingLG: CGFloat = 24
    public static let spacingXL: CGFloat = 32
}

// MARK: - Color Hex Initializer
public extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3: // RGB (12-bit)
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6: // RGB (24-bit)
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8: // ARGB (32-bit)
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (255, 0, 0, 0)
        }
        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue: Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}

// MARK: - Custom View Modifiers
public struct AsterCardModifier: ViewModifier {
    var padding: CGFloat = AsterTheme.spacingMD
    var cornerRadius: CGFloat = AsterTheme.radiusCard
    
    public func body(content: Content) -> some View {
        content
            .padding(padding)
            .background(AsterTheme.surface)
            .clipShape(RoundedRectangle(cornerRadius: cornerRadius, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                    .stroke(AsterTheme.outline, lineWidth: 1)
            )
    }
}

public struct AsterHaloGlowModifier: ViewModifier {
    var color: Color = AsterTheme.warmAmber
    var radius: CGFloat = 28
    var opacity: Double = 0.55
    
    public func body(content: Content) -> some View {
        content
            .background(
                Circle()
                    .fill(
                        RadialGradient(
                            gradient: Gradient(colors: [
                                color.opacity(opacity),
                                color.opacity(opacity * 0.4),
                                Color.clear
                            ]),
                            center: .center,
                            startRadius: 10,
                            endRadius: radius * 2.2
                        )
                    )
                    .blur(radius: radius * 0.75)
            )
    }
}

public extension View {
    func asterCard(padding: CGFloat = AsterTheme.spacingMD, cornerRadius: CGFloat = AsterTheme.radiusCard) -> some View {
        modifier(AsterCardModifier(padding: padding, cornerRadius: cornerRadius))
    }
    
    func asterHaloGlow(color: Color = AsterTheme.warmAmber, radius: CGFloat = 28, opacity: Double = 0.55) -> some View {
        modifier(AsterHaloGlowModifier(color: color, radius: radius, opacity: opacity))
    }
}
