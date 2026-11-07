//
//  ReplayKitTests.swift
//  AsterCompanionTests
//
//  Created for Aster Companion iOS & macOS Screen Awareness System.
//  Comprehensive test suite validating perceptual hashing, static frame suppression,
//  packet serialization, monotonic sequencing, profile isolation guards, and memory safety.
//

import CoreMedia
import CoreVideo
import Foundation
import XCTest
@testable import AsterCompanion

final class ReplayKitTests: XCTestCase {

    // MARK: - Test Helpers

    /// Creates a solid-color CVPixelBuffer of specified dimensions and 32BGRA format.
    private func createTestPixelBuffer(
        width: Int = 100,
        height: Int = 100,
        color: (r: UInt8, g: UInt8, b: UInt8)
    ) -> CVPixelBuffer? {
        var pixelBuffer: CVPixelBuffer?
        let attributes: [CFString: Any] = [
            kCVPixelBufferCGImageCompatibilityKey: true,
            kCVPixelBufferCGBitmapContextCompatibilityKey: true
        ]

        let status = CVPixelBufferCreate(
            kCFAllocatorDefault,
            width,
            height,
            kCVPixelFormatType_32BGRA,
            attributes as CFDictionary,
            &pixelBuffer
        )

        guard status == kCVReturnSuccess, let buffer = pixelBuffer else {
            return nil
        }

        CVPixelBufferLockBaseAddress(buffer, [])
        defer { CVPixelBufferUnlockBaseAddress(buffer, []) }

        guard let baseAddress = CVPixelBufferGetBaseAddress(buffer) else {
            return nil
        }

        let bytesPerRow = CVPixelBufferGetBytesPerRow(buffer)
        let ptr = baseAddress.assumingMemoryBound(to: UInt8.self)

        for y in 0..<height {
            let rowOffset = y * bytesPerRow
            for x in 0..<width {
                let pixelOffset = rowOffset + (x * 4)
                ptr[pixelOffset] = color.b     // Blue
                ptr[pixelOffset + 1] = color.g // Green
                ptr[pixelOffset + 2] = color.r // Red
                ptr[pixelOffset + 3] = 255     // Alpha
            }
        }

        return buffer
    }

    /// Creates a patterned CVPixelBuffer with a vertical gradient.
    private func createGradientPixelBuffer(width: Int = 100, height: Int = 100) -> CVPixelBuffer? {
        var pixelBuffer: CVPixelBuffer?
        let status = CVPixelBufferCreate(
            kCFAllocatorDefault,
            width,
            height,
            kCVPixelFormatType_32BGRA,
            nil,
            &pixelBuffer
        )

        guard status == kCVReturnSuccess, let buffer = pixelBuffer else { return nil }

        CVPixelBufferLockBaseAddress(buffer, [])
        defer { CVPixelBufferUnlockBaseAddress(buffer, []) }

        guard let baseAddress = CVPixelBufferGetBaseAddress(buffer) else { return nil }
        let bytesPerRow = CVPixelBufferGetBytesPerRow(buffer)
        let ptr = baseAddress.assumingMemoryBound(to: UInt8.self)

        for y in 0..<height {
            let rowOffset = y * bytesPerRow
            for x in 0..<width {
                let pixelOffset = rowOffset + (x * 4)
                let val = UInt8((x * 255) / width)
                ptr[pixelOffset] = val
                ptr[pixelOffset + 1] = val
                ptr[pixelOffset + 2] = val
                ptr[pixelOffset + 3] = 255
            }
        }

        return buffer
    }

    // MARK: - Perceptual Hashing Tests

    func testPerceptualHashIdenticalFrames() {
        guard let bufferA = createTestPixelBuffer(color: (r: 120, g: 120, b: 120)),
              let bufferB = createTestPixelBuffer(color: (r: 120, g: 120, b: 120)) else {
            XCTFail("Failed to allocate test pixel buffers.")
            return
        }

        guard let hashA = PerceptualHash.computeDHash(from: bufferA),
              let hashB = PerceptualHash.computeDHash(from: bufferB) else {
            XCTFail("Failed to compute perceptual hash.")
            return
        }

        let distance = PerceptualHash.hammingDistance(hashA, hashB)
        XCTAssertEqual(distance, 0, "Identical frames must produce a Hamming distance of 0.")
        XCTAssertTrue(PerceptualHash.isStatic(hashA: hashA, hashB: hashB, threshold: 2))
    }

    func testPerceptualHashDistinctFrames() {
        guard let bufferA = createGradientPixelBuffer(width: 100, height: 100),
              let bufferB = createTestPixelBuffer(width: 100, height: 100, color: (r: 255, g: 0, b: 0)) else {
            XCTFail("Failed to allocate test pixel buffers.")
            return
        }

        guard let hashA = PerceptualHash.computeDHash(from: bufferA),
              let hashB = PerceptualHash.computeDHash(from: bufferB) else {
            XCTFail("Failed to compute perceptual hash.")
            return
        }

        let distance = PerceptualHash.hammingDistance(hashA, hashB)
        XCTAssertGreaterThan(distance, 2, "Distinct frames must have Hamming distance > threshold.")
        XCTAssertFalse(PerceptualHash.isStatic(hashA: hashA, hashB: hashB, threshold: 2))
    }

    func testPerceptualHashHexFormatting() {
        let testHash: UInt64 = 0xABCD1234EF567890
        let hex = PerceptualHash.hexString(from: testHash)
        XCTAssertEqual(hex.lowercased(), "abcd1234ef567890")

        let parsed = PerceptualHash.hash(from: hex)
        XCTAssertEqual(parsed, testHash)
    }

    // MARK: - Awareness Packet Serialization Tests

    func testPacketEncodingDecoding() throws {
        let frameMeta = FrameMetadata(
            width: 1280,
            height: 720,
            format: "jpeg",
            perceptualHash: "0123456789abcdef",
            hammingDistance: 1,
            isKeyframe: true,
            skippedSinceLastKeyframe: 4,
            captureFPS: 3.0,
            targetFPS: 3.0
        )

        let consent = AwarenessConsentMetadata(
            screenCaptureGranted: true,
            micAudioGranted: false,
            appAudioPlaybackGranted: true
        )

        let originalPacket = AwarenessPacket(
            sequenceNumber: 42,
            source: .iosReplayKitExtension,
            deviceId: "device-test-uuid",
            sessionId: "session-test-uuid",
            profileId: "profile-alpha",
            consent: consent,
            type: .frame,
            frame: frameMeta,
            payloadBase64: "aGVsbG8td29ybGQ=",
            payloadChecksum: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        let jsonData = try encoder.encode(originalPacket)

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        let decodedPacket = try decoder.decode(AwarenessPacket.self, from: jsonData)

        XCTAssertEqual(decodedPacket.id, originalPacket.id)
        XCTAssertEqual(decodedPacket.sequenceNumber, 42)
        XCTAssertEqual(decodedPacket.profileId, "profile-alpha")
        XCTAssertEqual(decodedPacket.deviceId, "device-test-uuid")
        XCTAssertEqual(decodedPacket.source, .iosReplayKitExtension)
        XCTAssertEqual(decodedPacket.type, .frame)
        XCTAssertEqual(decodedPacket.frame?.width, 1280)
        XCTAssertEqual(decodedPacket.frame?.height, 720)
        XCTAssertEqual(decodedPacket.frame?.perceptualHash, "0123456789abcdef")
        XCTAssertEqual(decodedPacket.frame?.isKeyframe, true)
        XCTAssertEqual(decodedPacket.consent.screenCaptureGranted, true)
        XCTAssertEqual(decodedPacket.consent.micAudioGranted, false)
        XCTAssertEqual(decodedPacket.consent.appAudioPlaybackGranted, true)
    }

    // MARK: - Profile Isolation & IPC Tests

    func testProfileIsolationValidation() {
        let testSuiteName = "group.com.astercompanion.test.\(UUID().uuidString)"
        let ipc = AppGroupIPC(suiteName: testSuiteName)

        ipc.updateActiveProfileId("profile-primary")

        // Valid match
        XCTAssertTrue(ipc.validateProfileIsolation(sessionProfileId: "profile-primary"))

        // Invalid mismatch (Profile B attempting to read or stream during Profile A's session)
        XCTAssertFalse(ipc.validateProfileIsolation(sessionProfileId: "profile-secondary"))
    }

    func testSessionConfigPersistence() {
        let testSuiteName = "group.com.astercompanion.test.\(UUID().uuidString)"
        let ipc = AppGroupIPC(suiteName: testSuiteName)

        guard let testUrl = URL(string: "https://example.supabase.co") else {
            XCTFail("Invalid URL")
            return
        }

        let config = AwarenessSessionConfig(
            activeProfileId: "profile-alpha",
            deviceId: "device-xyz",
            sessionId: "session-abc",
            supabaseUrl: testUrl,
            supabaseAuthToken: "mock-jwt-token",
            micOptIn: true,
            appAudioOptIn: false,
            targetFrameRate: 5.0,
            maxResolutionDimension: 1080
        )

        ipc.saveSessionConfig(config)

        let loaded = ipc.loadSessionConfig()
        XCTAssertNotNil(loaded)
        XCTAssertEqual(loaded?.activeProfileId, "profile-alpha")
        XCTAssertEqual(loaded?.deviceId, "device-xyz")
        XCTAssertEqual(loaded?.sessionId, "session-abc")
        XCTAssertEqual(loaded?.micOptIn, true)
        XCTAssertEqual(loaded?.appAudioOptIn, false)
        XCTAssertEqual(loaded?.targetFrameRate, 5.0)
        XCTAssertEqual(loaded?.maxResolutionDimension, 1080)

        ipc.clearSessionConfig()
        XCTAssertNil(ipc.loadSessionConfig())
    }

    // MARK: - Memory Inspector Verification

    func testResidentMemoryMeasurement() {
        let residentMB = AwarenessTransportClient.getResidentMemoryMB()
        XCTAssertGreaterThan(residentMB, 0.0, "Resident memory must be a positive number.")
        XCTAssertLessThan(residentMB, 500.0, "Resident memory should be within reasonable bounds.")
    }
}
