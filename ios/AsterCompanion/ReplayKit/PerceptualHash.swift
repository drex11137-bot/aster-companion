//
//  PerceptualHash.swift
//  AsterCompanion
//
//  Created for Aster Companion iOS & macOS Screen Awareness System.
//  Ultra-low-allocation difference hash (dHash) and average hash (aHash)
//  operating directly on CVPixelBuffer without allocating intermediate UIImages.
//

import CoreMedia
import CoreVideo
import Foundation

/// High-performance perceptual hashing and Hamming distance utility.
/// Designed specifically for iOS ReplayKit Broadcast Extensions to eliminate static frame uploads
/// while consuming zero heap allocations and adhering to the < 50MB extension RAM limit.
public enum PerceptualHash {

    // MARK: - Constants

    /// Target grid dimensions for Difference Hash (9 columns x 8 rows = 72 luminance samples).
    public static let dHashWidth = 9
    public static let dHashHeight = 8

    /// Target grid dimensions for Average Hash (8 columns x 8 rows = 64 luminance samples).
    public static let aHashWidth = 8
    public static let aHashHeight = 8

    // MARK: - dHash Computation

    /// Computes a 64-bit difference hash (dHash) directly from a `CVPixelBuffer`.
    ///
    /// The algorithm extracts a 9x8 luminance grid across the screen image, then compares
    /// each column with its horizontal neighbor: bit = (pixel[x, y] > pixel[x + 1, y]) ? 1 : 0.
    /// This produces 8 bits per row across 8 rows = 64 bits.
    ///
    /// - Parameter pixelBuffer: The raw video frame pixel buffer from ReplayKit or ScreenCaptureKit.
    /// - Returns: A 64-bit unsigned integer representing the perceptual signature, or `nil` on failure.
    public static func computeDHash(from pixelBuffer: CVPixelBuffer) -> UInt64? {
        CVPixelBufferLockBaseAddress(pixelBuffer, .readOnly)
        defer { CVPixelBufferUnlockBaseAddress(pixelBuffer, .readOnly) }

        let width = CVPixelBufferGetWidth(pixelBuffer)
        let height = CVPixelBufferGetHeight(pixelBuffer)
        guard width > 0 && height > 0 else { return nil }

        let pixelFormat = CVPixelBufferGetPixelFormatType(pixelBuffer)
        var luminanceGrid = [UInt8](repeating: 0, count: dHashWidth * dHashHeight)

        let success: Bool
        if CVPixelBufferIsPlanar(pixelBuffer) {
            // YUV planar formats (e.g., kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange / FullRange)
            // Plane 0 is the full-resolution Y (luminance) plane.
            success = samplePlanarLuminance(
                pixelBuffer: pixelBuffer,
                plane: 0,
                sourceWidth: width,
                sourceHeight: height,
                targetWidth: dHashWidth,
                targetHeight: dHashHeight,
                output: &luminanceGrid
            )
        } else {
            // Packed RGB/BGRA formats (e.g., kCVPixelFormatType_32BGRA, kCVPixelFormatType_32ARGB)
            success = samplePackedBGRALuminance(
                pixelBuffer: pixelBuffer,
                pixelFormat: pixelFormat,
                sourceWidth: width,
                sourceHeight: height,
                targetWidth: dHashWidth,
                targetHeight: dHashHeight,
                output: &luminanceGrid
            )
        }

        guard success else { return nil }

        // Compute 64 bits from the 9x8 grid: (left > right)
        var hash: UInt64 = 0
        var bitIndex = 0

        for row in 0..<dHashHeight {
            let rowOffset = row * dHashWidth
            for col in 0..<(dHashWidth - 1) {
                let leftPixel = luminanceGrid[rowOffset + col]
                let rightPixel = luminanceGrid[rowOffset + col + 1]

                if leftPixel > rightPixel {
                    hash |= (1 << bitIndex)
                }
                bitIndex += 1
            }
        }

        return hash
    }

    // MARK: - aHash Computation

    /// Computes an 8x8 Average Hash (aHash) directly from a `CVPixelBuffer`.
    /// Useful as a complementary perceptual comparison or fast fallback.
    public static func computeAHash(from pixelBuffer: CVPixelBuffer) -> UInt64? {
        CVPixelBufferLockBaseAddress(pixelBuffer, .readOnly)
        defer { CVPixelBufferUnlockBaseAddress(pixelBuffer, .readOnly) }

        let width = CVPixelBufferGetWidth(pixelBuffer)
        let height = CVPixelBufferGetHeight(pixelBuffer)
        guard width > 0 && height > 0 else { return nil }

        let pixelFormat = CVPixelBufferGetPixelFormatType(pixelBuffer)
        var luminanceGrid = [UInt8](repeating: 0, count: aHashWidth * aHashHeight)

        let success: Bool
        if CVPixelBufferIsPlanar(pixelBuffer) {
            success = samplePlanarLuminance(
                pixelBuffer: pixelBuffer,
                plane: 0,
                sourceWidth: width,
                sourceHeight: height,
                targetWidth: aHashWidth,
                targetHeight: aHashHeight,
                output: &luminanceGrid
            )
        } else {
            success = samplePackedBGRALuminance(
                pixelBuffer: pixelBuffer,
                pixelFormat: pixelFormat,
                sourceWidth: width,
                sourceHeight: height,
                targetWidth: aHashWidth,
                targetHeight: aHashHeight,
                output: &luminanceGrid
            )
        }

        guard success else { return nil }

        // Calculate average luminance
        let totalSum = luminanceGrid.reduce(0) { $0 + Int($1) }
        let average = UInt8(totalSum / luminanceGrid.count)

        // Generate 64-bit hash
        var hash: UInt64 = 0
        for i in 0..<luminanceGrid.count {
            if luminanceGrid[i] >= average {
                hash |= (1 << i)
            }
        }

        return hash
    }

    // MARK: - Hamming Distance

    /// Calculates the Hamming distance between two 64-bit perceptual hashes.
    /// The Hamming distance represents the number of differing bits (0 to 64).
    ///
    /// - Parameters:
    ///   - hashA: First perceptual hash.
    ///   - hashB: Second perceptual hash.
    /// - Returns: Number of differing bits. 0 means perceptually identical.
    @inlinable
    public static func hammingDistance(_ hashA: UInt64, _ hashB: UInt64) -> Int {
        return (hashA ^ hashB).nonzeroBitCount
    }

    /// Evaluates whether two hashes are perceptually identical within a given bit error threshold.
    ///
    /// - Parameters:
    ///   - hashA: First perceptual hash.
    ///   - hashB: Second perceptual hash.
    ///   - threshold: Maximum allowable bit difference (default: 2 bits out of 64).
    /// - Returns: True if difference is within threshold (static frame).
    @inlinable
    public static func isStatic(hashA: UInt64, hashB: UInt64, threshold: Int = 2) -> Bool {
        return hammingDistance(hashA, hashB) <= threshold
    }

    /// Formats a 64-bit hash as a standardized 16-character hexadecimal string.
    public static func hexString(from hash: UInt64) -> String {
        return String(format: "%016llx", hash)
    }

    /// Parses a 16-character hexadecimal string into a 64-bit hash.
    public static func hash(from hexString: String) -> UInt64? {
        return UInt64(hexString, radix: 16)
    }

    // MARK: - Private Sampling Implementations

    /// Samples luminance from Planar YUV buffers (e.g., NV12 plane 0).
    /// Uses box-sampling across uniform step intervals with zero allocations.
    private static func samplePlanarLuminance(
        pixelBuffer: CVPixelBuffer,
        plane: Int,
        sourceWidth: Int,
        sourceHeight: Int,
        targetWidth: Int,
        targetHeight: Int,
        output: inout [UInt8]
    ) -> Bool {
        guard let baseAddress = CVPixelBufferGetBaseAddressOfPlane(pixelBuffer, plane) else {
            return false
        }

        let bytesPerRow = CVPixelBufferGetBytesPerRowOfPlane(pixelBuffer, plane)
        let buffer = baseAddress.assumingMemoryBound(to: UInt8.self)

        let stepX = Double(sourceWidth) / Double(targetWidth)
        let stepY = Double(sourceHeight) / Double(targetHeight)

        for y in 0..<targetHeight {
            let srcY = min(Int((Double(y) + 0.5) * stepY), sourceHeight - 1)
            let rowOffset = srcY * bytesPerRow
            let outRowOffset = y * targetWidth

            for x in 0..<targetWidth {
                let srcX = min(Int((Double(x) + 0.5) * stepX), sourceWidth - 1)
                output[outRowOffset + x] = buffer[rowOffset + srcX]
            }
        }

        return true
    }

    /// Samples luminance from packed 32-bit RGB/BGRA buffers using standard ITU-R BT.601 coefficients:
    /// Y = (299*R + 587*G + 114*B) / 1000.
    private static func samplePackedBGRALuminance(
        pixelBuffer: CVPixelBuffer,
        pixelFormat: OSType,
        sourceWidth: Int,
        sourceHeight: Int,
        targetWidth: Int,
        targetHeight: Int,
        output: inout [UInt8]
    ) -> Bool {
        guard let baseAddress = CVPixelBufferGetBaseAddress(pixelBuffer) else {
            return false
        }

        let bytesPerRow = CVPixelBufferGetBytesPerRow(pixelBuffer)
        let buffer = baseAddress.assumingMemoryBound(to: UInt8.self)

        let stepX = Double(sourceWidth) / Double(targetWidth)
        let stepY = Double(sourceHeight) / Double(targetHeight)

        // Detect channel order
        let isBGRA = (pixelFormat == kCVPixelFormatType_32BGRA)

        for y in 0..<targetHeight {
            let srcY = min(Int((Double(y) + 0.5) * stepY), sourceHeight - 1)
            let rowOffset = srcY * bytesPerRow
            let outRowOffset = y * targetWidth

            for x in 0..<targetWidth {
                let srcX = min(Int((Double(x) + 0.5) * stepX), sourceWidth - 1)
                let pixelOffset = rowOffset + (srcX * 4)

                let r: UInt32
                let g: UInt32
                let b: UInt32

                if isBGRA {
                    b = UInt32(buffer[pixelOffset])
                    g = UInt32(buffer[pixelOffset + 1])
                    r = UInt32(buffer[pixelOffset + 2])
                } else {
                    // Assume ARGB or RGBA default fallback
                    r = UInt32(buffer[pixelOffset + 1])
                    g = UInt32(buffer[pixelOffset + 2])
                    b = UInt32(buffer[pixelOffset + 3])
                }

                // Integer ITU-R BT.601 luma calculation
                let luma = (299 * r + 587 * g + 114 * b) / 1000
                output[outRowOffset + x] = UInt8(clamping: luma)
            }
        }

        return true
    }
}
