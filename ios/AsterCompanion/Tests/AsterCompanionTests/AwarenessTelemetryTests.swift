import XCTest
@testable import AsterCompanion

final class AwarenessTelemetryTests: XCTestCase {
    
    func testHonestFPSDistinction() {
        let telemetry = AwarenessTelemetry(
            status: .active,
            captureFPS: 120.0,
            uploadFPS: 30.0,
            ingestFPS: 30.0,
            analysisFPS: 5.0,
            latencyMs: 140.0,
            continuityRatio: 1.0,
            gapsDetected: 0
        )
        
        // Assert PRD Section 5.3: Capture FPS must never be conflated with Analysis FPS
        XCTAssertNotEqual(
            telemetry.captureFPS,
            telemetry.analysisFPS,
            "Capture FPS must be distinguished from multimodal inference analysis FPS"
        )
        XCTAssertEqual(telemetry.captureFPS, 120.0)
        XCTAssertEqual(telemetry.analysisFPS, 5.0)
        XCTAssertEqual(telemetry.continuityRatio, 1.0)
        XCTAssertEqual(telemetry.gapsDetected, 0)
    }
}
