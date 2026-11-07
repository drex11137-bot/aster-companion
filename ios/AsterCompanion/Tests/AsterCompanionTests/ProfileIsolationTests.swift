import XCTest
@testable import AsterCompanion

final class ProfileIsolationTests: XCTestCase {
    
    @MainActor
    func testMaxTwoProfilesConstraint() {
        let appState = AppState.shared
        
        // Assert exactly 2 profiles are initialized
        XCTAssertEqual(appState.profiles.count, 2, "PRD DEC-021 requires exactly maximum 2 profiles per account.")
        
        // Profiles must have distinct identities
        let profile1 = appState.profiles[0]
        let profile2 = appState.profiles[1]
        
        XCTAssertNotEqual(profile1.id, profile2.id)
        XCTAssertEqual(profile1.name, "Aster")
        XCTAssertEqual(profile2.name, "Nova")
    }
    
    @MainActor
    func testProfileSwitchingIsolatesContext() {
        let appState = AppState.shared
        let profile1 = appState.profiles[0]
        let profile2 = appState.profiles[1]
        
        // Activate Profile 1
        appState.switchProfile(to: profile1.id)
        XCTAssertEqual(appState.activeProfileId, profile1.id)
        
        // Switch to Profile 2
        appState.switchProfile(to: profile2.id)
        XCTAssertEqual(appState.activeProfileId, profile2.id)
        XCTAssertEqual(appState.activeProfile.name, "Nova")
    }
    
    func testExplicitSharingAuditTrail() async throws {
        let profile1Id = UUID()
        let profile2Id = UUID()
        let memoryId = UUID()
        let userId = "test_user_maya"
        
        let client = SupabaseClient.shared
        client.currentUserId = userId
        
        let sharedMemory = try await client.shareMemoryExplicitly(
            memoryId: memoryId,
            fromProfile: profile1Id,
            toProfile: profile2Id
        )
        
        XCTAssertTrue(sharedMemory.isExplicitlyShared)
        XCTAssertNotNil(sharedMemory.shareAudit)
        XCTAssertEqual(sharedMemory.shareAudit?.sourceProfileId, profile1Id)
        XCTAssertEqual(sharedMemory.shareAudit?.destinationProfileId, profile2Id)
        XCTAssertEqual(sharedMemory.shareAudit?.confirmedByUserId, userId)
    }
}
