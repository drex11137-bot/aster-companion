import SwiftUI

/// Custom Tab Bar component strictly replicating the pill indicator design in reference screenshots.
public struct AsterTabBar: View {
    @Binding var selectedTab: AsterTab
    
    public init(selectedTab: Binding<AsterTab>) {
        self._selectedTab = selectedTab
    }
    
    public var body: some View {
        HStack(alignment: .center) {
            ForEach(AsterTab.allCases) { tab in
                let isSelected = (selectedTab == tab)
                
                Button(action: {
                    withAnimation(.spring(response: 0.28, dampingFraction: 0.75)) {
                        selectedTab = tab
                    }
                }) {
                    VStack(spacing: 4) {
                        ZStack {
                            if isSelected {
                                Capsule()
                                    .fill(AsterTheme.warmAmber)
                                    .frame(width: 64, height: 32)
                                    .transition(.scale.combined(with: .opacity))
                            } else {
                                Color.clear
                                    .frame(width: 64, height: 32)
                            }
                            
                            Image(systemName: tab.iconName)
                                .font(.system(size: 18, weight: .semibold))
                                .foregroundColor(isSelected ? AsterTheme.ground : AsterTheme.mutedText)
                        }
                        
                        Text(tab.rawValue)
                            .font(.system(size: 11, weight: isSelected ? .bold : .medium))
                            .foregroundColor(isSelected ? AsterTheme.warmAmber : AsterTheme.mutedText)
                    }
                    .frame(maxWidth: .infinity)
                }
                .buttonStyle(PlainButtonStyle())
            }
        }
        .padding(.top, 8)
        .padding(.bottom, 12)
        .background(
            AsterTheme.ground
                .overlay(
                    Rectangle()
                        .fill(AsterTheme.outline)
                        .frame(height: 1),
                    alignment: .top
                )
                .ignoresSafeArea(edges: .bottom)
        )
    }
}

/// Root Application Entry Point for Aster Companion.
@main
public struct AsterCompanionApp: App {
    @StateObject private var appState = AppState.shared
    
    public init() {}
    
    public var body: some Scene {
        WindowGroup {
            ZStack(alignment: .bottom) {
                // Background
                AsterTheme.ground.ignoresSafeArea()
                
                // Active Screen View
                Group {
                    switch appState.selectedTab {
                    case .today:
                        TodayView()
                    case .chat:
                        ChatView()
                    case .memory:
                        MemoryView()
                    case .companion:
                        CompanionStudioView()
                    }
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .padding(.bottom, 64) // Reserve space for custom tab bar
                
                // Pixel-perfect Bottom Tab Bar
                AsterTabBar(selectedTab: $appState.selectedTab)
            }
            .preferredColorScheme(.dark)
            .environmentObject(appState)
        }
    }
}
