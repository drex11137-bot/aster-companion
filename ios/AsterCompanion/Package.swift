// swift-tools-version: 6.0
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "AsterCompanion",
    platforms: [
        .iOS(.v17),
        .macOS(.v14)
    ],
    products: [
        .library(
            name: "AsterCompanion",
            targets: ["AsterCompanion"]
        ),
        .library(
            name: "ReplayKitBroadcastExtension",
            targets: ["ReplayKitBroadcastExtension"]
        )
    ],
    dependencies: [],
    targets: [
        .target(
            name: "AsterCompanion",
            dependencies: [],
            path: "Sources/AsterCompanion",
            resources: [
                .process("Resources")
            ]
        ),
        .target(
            name: "ReplayKitBroadcastExtension",
            dependencies: [],
            path: "Sources/ReplayKitBroadcastExtension"
        ),
        .testTarget(
            name: "AsterCompanionTests",
            dependencies: ["AsterCompanion"],
            path: "Tests/AsterCompanionTests"
        )
    ],
    swiftLanguageModes: [.v6]
)
