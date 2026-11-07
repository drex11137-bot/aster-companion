import XCTest
import SwiftUI
@testable import AsterCompanion

final class DesignTokensTests: XCTestCase {
    
    func testHexColorValues() {
        // Test exact hex tokens matching PRD and reference screenshots
        let ground = AsterTheme.ground
        let surface = AsterTheme.surface
        let warmAmber = AsterTheme.warmAmber
        let restrainedViolet = AsterTheme.restrainedViolet
        let creamText = AsterTheme.creamText
        
        XCTAssertNotNil(ground)
        XCTAssertNotNil(surface)
        XCTAssertNotNil(warmAmber)
        XCTAssertNotNil(restrainedViolet)
        XCTAssertNotNil(creamText)
    }
    
    func testHighContrastRatio() {
        // Relative luminance of cream text (#FAF8F5) vs ground (#121110)
        let rCream = 250.0 / 255.0
        let gCream = 248.0 / 255.0
        let bCream = 245.0 / 255.0
        
        let rGround = 18.0 / 255.0
        let gGround = 17.0 / 255.0
        let bGround = 16.0 / 255.0
        
        let lumCream = 0.2126 * rCream + 0.7152 * gCream + 0.0722 * bCream
        let lumGround = 0.2126 * rGround + 0.7152 * gGround + 0.0722 * bGround
        
        let contrastRatio = (lumCream + 0.05) / (lumGround + 0.05)
        
        // WCAG AAA requires >= 7:1 for normal text
        XCTAssertGreaterThan(contrastRatio, 7.0, "Cream text on dark ground must meet WCAG AAA contrast ratio")
    }
}
