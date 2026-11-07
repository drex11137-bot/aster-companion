import SwiftUI

/// Main Home / Today View conforming strictly to reference screenshot 1.
public struct TodayView: View {
    @ObservedObject var appState: AppState = AppState.shared
    @State private var showingSettings: Bool = false
    @State private var showingAllTasks: Bool = false
    @State private var showingAllMemories: Bool = false
    @State private var selectedMemoryForPreview: MemoryItem? = nil
    
    public init() {}
    
    public var body: some View {
        ScrollView(.vertical, showsIndicators: false) {
            VStack(alignment: .leading, spacing: 20) {
                // MARK: - Header with Greeting and Avatar
                headerSection
                
                // Motto
                Text("A calmer, brighter you — one step at a time.")
                    .font(.system(size: 15, weight: .regular))
                    .foregroundColor(AsterTheme.mutedText)
                    .padding(.top, -6)
                
                // MARK: - Next Reminder Card
                reminderCard
                
                // MARK: - Your Tasks Section
                tasksSection
                
                // MARK: - Recent Memories Carousel
                recentMemoriesSection
                
                Spacer(minLength: 40)
            }
            .padding(.horizontal, 20)
            .padding(.top, 16)
        }
        .background(AsterTheme.ground.ignoresSafeArea())
        .sheet(isPresented: $showingSettings) {
            SettingsSheetView()
        }
        .sheet(item: $selectedMemoryForPreview) { memory in
            MemoryDetailSheet(memory: memory)
        }
    }
    
    // MARK: - Header
    private var headerSection: some View {
        HStack(alignment: .center, spacing: 14) {
            // Circular Avatar with Warm Amber Halo and Green Online Dot
            ZStack(alignment: .bottomTrailing) {
                // Amber Halo Glow
                Circle()
                    .fill(
                        RadialGradient(
                            gradient: Gradient(colors: [
                                AsterTheme.warmAmber.opacity(0.55),
                                AsterTheme.warmAmber.opacity(0.2),
                                Color.clear
                            ]),
                            center: .center,
                            startRadius: 8,
                            endRadius: 36
                        )
                    )
                    .frame(width: 68, height: 68)
                    .blur(radius: 6)
                
                // Avatar Image
                Image(appState.activeProfile.avatarImageName, bundle: .main)
                    .resizable()
                    .aspectRatio(contentMode: .fill)
                    .frame(width: 58, height: 58)
                    .clipShape(Circle())
                    .overlay(
                        Circle()
                            .stroke(AsterTheme.outline, lineWidth: 1.5)
                    )
                
                // Green Online Dot
                Circle()
                    .fill(AsterTheme.onlineGreen)
                    .frame(width: 14, height: 14)
                    .overlay(
                        Circle()
                            .stroke(AsterTheme.ground, lineWidth: 2.5)
                    )
                    .offset(x: 2, y: 2)
            }
            
            // Name & Online Status
            VStack(alignment: .leading, spacing: 3) {
                Text("Good evening, \(appState.userName)")
                    .font(.system(size: 24, weight: .bold))
                    .foregroundColor(AsterTheme.creamText)
                
                HStack(spacing: 6) {
                    Circle()
                        .fill(AsterTheme.onlineGreen)
                        .frame(width: 8, height: 8)
                    
                    Text("\(appState.activeProfile.name) is online")
                        .font(.system(size: 14, weight: .regular))
                        .foregroundColor(AsterTheme.mutedText)
                }
            }
            
            Spacer()
            
            // Settings Gear Button
            Button(action: { showingSettings = true }) {
                Image(systemName: "gearshape")
                    .font(.system(size: 20, weight: .medium))
                    .foregroundColor(AsterTheme.creamText)
                    .padding(8)
            }
        }
    }
    
    // MARK: - Next Reminder Card
    private var reminderCard: some View {
        HStack(alignment: .center, spacing: 16) {
            // Amber Calendar Icon
            Image(systemName: "calendar")
                .font(.system(size: 24, weight: .medium))
                .foregroundColor(AsterTheme.warmAmber)
                .frame(width: 32, height: 32)
            
            // Reminder Details
            VStack(alignment: .leading, spacing: 3) {
                Text("Next reminder")
                    .font(.system(size: 13, weight: .regular))
                    .foregroundColor(AsterTheme.mutedText)
                
                Text(appState.nextReminder.title)
                    .font(.system(size: 17, weight: .semibold))
                    .foregroundColor(AsterTheme.creamText)
                
                Text(appState.nextReminder.dateLabel)
                    .font(.system(size: 13, weight: .regular))
                    .foregroundColor(AsterTheme.mutedText)
            }
            
            Spacer()
            
            // Warm Amber Snooze Capsule Button
            Button(action: {
                withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) {
                    appState.snoozeReminder()
                }
            }) {
                Text(appState.nextReminder.isSnoozed ? "Snoozed" : "Snooze")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(AsterTheme.ground)
                    .padding(.horizontal, 22)
                    .padding(.vertical, 10)
                    .background(AsterTheme.warmAmber)
                    .clipShape(Capsule())
            }
        }
        .padding(18)
        .background(AsterTheme.surface)
        .clipShape(RoundedRectangle(cornerRadius: AsterTheme.radiusCard, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: AsterTheme.radiusCard, style: .continuous)
                .stroke(AsterTheme.outline, lineWidth: 1)
        )
    }
    
    // MARK: - Your Tasks Section
    private var tasksSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header with "See all >" in Violet
            HStack {
                Text("Your tasks")
                    .font(.system(size: 19, weight: .bold))
                    .foregroundColor(AsterTheme.creamText)
                
                Spacer()
                
                Button(action: { appState.selectedTab = .chat }) {
                    HStack(spacing: 4) {
                        Text("See all")
                            .font(.system(size: 14, weight: .medium))
                        Image(systemName: "chevron.right")
                            .font(.system(size: 12, weight: .semibold))
                    }
                    .foregroundColor(AsterTheme.restrainedViolet)
                }
            }
            
            // Container Card
            VStack(spacing: 0) {
                ForEach(Array(appState.tasks.enumerated()), id: \.element.id) { index, task in
                    taskRow(task)
                    
                    if index < appState.tasks.count - 1 {
                        Divider()
                            .background(AsterTheme.outline)
                            .padding(.leading, 48)
                    }
                }
            }
            .background(AsterTheme.surface)
            .clipShape(RoundedRectangle(cornerRadius: AsterTheme.radiusCard, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: AsterTheme.radiusCard, style: .continuous)
                    .stroke(AsterTheme.outline, lineWidth: 1)
            )
        }
    }
    
    private func taskRow(_ task: TaskItem) -> some View {
        HStack(spacing: 14) {
            // Checkbox
            Button(action: {
                withAnimation(.spring(response: 0.25, dampingFraction: 0.7)) {
                    appState.toggleTask(task)
                }
            }) {
                ZStack {
                    RoundedRectangle(cornerRadius: 6)
                        .stroke(task.isCompleted ? AsterTheme.warmAmber : AsterTheme.outlineActive, lineWidth: 1.5)
                        .frame(width: 22, height: 22)
                        .background(task.isCompleted ? AsterTheme.warmAmber : Color.clear)
                        .clipShape(RoundedRectangle(cornerRadius: 6))
                    
                    if task.isCompleted {
                        Image(systemName: "checkmark")
                            .font(.system(size: 12, weight: .bold))
                            .foregroundColor(AsterTheme.ground)
                    }
                }
            }
            
            // Task text
            VStack(alignment: .leading, spacing: 2) {
                Text(task.title)
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(task.isCompleted ? AsterTheme.mutedText : AsterTheme.creamText)
                    .strikethrough(task.isCompleted, color: AsterTheme.mutedText)
                
                Text(task.dueDateLabel)
                    .font(.system(size: 13, weight: .regular))
                    .foregroundColor(AsterTheme.mutedText)
            }
            
            Spacer()
            
            Image(systemName: "chevron.right")
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(AsterTheme.mutedText)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 14)
    }
    
    // MARK: - Recent Memories Section
    private var recentMemoriesSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header with "See all >" in Violet
            HStack {
                Text("Recent memories")
                    .font(.system(size: 19, weight: .bold))
                    .foregroundColor(AsterTheme.creamText)
                
                Spacer()
                
                Button(action: { appState.selectedTab = .memory }) {
                    HStack(spacing: 4) {
                        Text("See all")
                            .font(.system(size: 14, weight: .medium))
                        Image(systemName: "chevron.right")
                            .font(.system(size: 12, weight: .semibold))
                    }
                    .foregroundColor(AsterTheme.restrainedViolet)
                }
            }
            
            // Horizontal Carousel
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 14) {
                    ForEach(appState.memories.filter { $0.imageThumbnailName != nil }) { memory in
                        memoryCard(memory)
                    }
                }
            }
        }
    }
    
    private func memoryCard(_ memory: MemoryItem) -> some View {
        Button(action: { selectedMemoryForPreview = memory }) {
            ZStack(alignment: .bottomLeading) {
                // Background Image
                if let imageName = memory.imageThumbnailName {
                    Image(imageName, bundle: .main)
                        .resizable()
                        .aspectRatio(contentMode: .fill)
                        .frame(width: 172, height: 180)
                        .clipped()
                } else {
                    Rectangle()
                        .fill(AsterTheme.surface)
                        .frame(width: 172, height: 180)
                }
                
                // Dark Gradient Scrim Overlay
                LinearGradient(
                    gradient: Gradient(colors: [
                        Color.clear,
                        AsterTheme.ground.opacity(0.4),
                        AsterTheme.ground.opacity(0.95)
                    ]),
                    startPoint: .top,
                    endPoint: .bottom
                )
                .frame(width: 172, height: 180)
                
                // Text Content
                VStack(alignment: .leading, spacing: 3) {
                    Text(memory.title)
                        .font(.system(size: 15, weight: .semibold))
                        .foregroundColor(AsterTheme.creamText)
                        .lineLimit(2)
                        .multilineTextAlignment(.leading)
                    
                    Text(memory.relativeTime)
                        .font(.system(size: 12, weight: .regular))
                        .foregroundColor(AsterTheme.mutedText)
                }
                .padding(14)
            }
            .frame(width: 172, height: 180)
            .clipShape(RoundedRectangle(cornerRadius: AsterTheme.radiusCard, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: AsterTheme.radiusCard, style: .continuous)
                    .stroke(AsterTheme.outline, lineWidth: 1)
            )
        }
        .buttonStyle(PlainButtonStyle())
    }
}

// MARK: - Detail Sheets

struct MemoryDetailSheet: View {
    let memory: MemoryItem
    @Environment(\.dismiss) var dismiss
    
    var body: some View {
        NavigationStack {
            ZStack {
                AsterTheme.ground.ignoresSafeArea()
                
                VStack(spacing: 20) {
                    if let imageName = memory.imageThumbnailName {
                        Image(imageName, bundle: .main)
                            .resizable()
                            .aspectRatio(contentMode: .fit)
                            .clipShape(RoundedRectangle(cornerRadius: 16))
                            .padding(.horizontal)
                    }
                    
                    VStack(alignment: .leading, spacing: 8) {
                        Text(memory.title)
                            .font(.system(size: 20, weight: .bold))
                            .foregroundColor(AsterTheme.creamText)
                        
                        Text(memory.relativeTime)
                            .font(.system(size: 14))
                            .foregroundColor(AsterTheme.mutedText)
                        
                        HStack(spacing: 6) {
                            Text("Category:")
                                .foregroundColor(AsterTheme.mutedText)
                            Text(memory.category.rawValue)
                                .foregroundColor(AsterTheme.warmAmber)
                                .fontWeight(.semibold)
                        }
                        .font(.system(size: 14))
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal)
                    
                    Spacer()
                }
                .padding(.top)
            }
            .navigationTitle("Memory")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                        .foregroundColor(AsterTheme.warmAmber)
                }
            }
        }
    }
}

struct SettingsSheetView: View {
    @Environment(\.dismiss) var dismiss
    @ObservedObject var appState: AppState = AppState.shared
    
    var body: some View {
        NavigationStack {
            ZStack {
                AsterTheme.ground.ignoresSafeArea()
                
                List {
                    Section("Account & Companion") {
                        HStack {
                            Text("User Name")
                            Spacer()
                            Text(appState.userName)
                                .foregroundColor(AsterTheme.mutedText)
                        }
                        HStack {
                            Text("Active Profile")
                            Spacer()
                            Text(appState.activeProfile.name)
                                .foregroundColor(AsterTheme.warmAmber)
                        }
                        HStack {
                            Text("Profiles Count")
                            Spacer()
                            Text("\(appState.profiles.count) of 2 (Max)")
                                .foregroundColor(AsterTheme.mutedText)
                        }
                    }
                    .listRowBackground(AsterTheme.surface)
                    
                    Section("Awareness & Privacy") {
                        HStack {
                            Text("Continuous Screen")
                            Spacer()
                            Text(appState.telemetry.isScreenPaused ? "Paused" : "Enabled")
                                .foregroundColor(appState.telemetry.isScreenPaused ? AsterTheme.warmAmber : AsterTheme.onlineGreen)
                        }
                        HStack {
                            Text("Audio Awareness")
                            Spacer()
                            Text(appState.telemetry.isAudioMuted ? "Muted" : "Active")
                                .foregroundColor(appState.telemetry.isAudioMuted ? AsterTheme.warmAmber : AsterTheme.onlineGreen)
                        }
                    }
                    .listRowBackground(AsterTheme.surface)
                }
                .scrollContentBackground(.hidden)
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                        .foregroundColor(AsterTheme.warmAmber)
                }
            }
        }
    }
}
