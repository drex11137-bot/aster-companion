import XCTest
@testable import AsterCompanion

final class OfflineSyncTests: XCTestCase {
    
    func testOfflineQueuingAndFlush() async throws {
        let client = SupabaseClient.shared
        
        // Simulate Offline State
        client.isOnline = false
        
        let testMemory = MemoryItem(
            profileId: UUID(),
            title: "Test offline memory",
            relativeTime: "Just now",
            category: .preferences,
            iconType: .sun
        )
        
        try await client.saveMemory(testMemory)
        XCTAssertGreaterThan(client.pendingSyncCount, 0, "Offline writes must queue into outbox")
        
        // Reconnect and Flush
        client.isOnline = true
        await client.flushOutbox()
        XCTAssertEqual(client.pendingSyncCount, 0, "Flushing outbox should drain pending actions")
    }
}
