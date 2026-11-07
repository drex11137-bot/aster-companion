import SwiftUI

/// Memory Management View conforming strictly to reference screenshot 2.
public struct MemoryView: View {
    @ObservedObject var appState: AppState = AppState.shared
    @State private var searchText: String = ""
    @State private var selectedCategory: MemoryCategory = .all
    @State private var memoryToEdit: MemoryItem? = nil
    @State private var memoryToDelete: MemoryItem? = nil
    @State private var memoryToShare: MemoryItem? = nil
    @State private var showingAddMemorySheet: Bool = false
    
    public init() {}
    
    // Filtered memories based on active search and category
    private var filteredMemories: [MemoryItem] {
        appState.memories.filter { item in
            let matchesCategory = (selectedCategory == .all) || (item.category == selectedCategory)
            let matchesSearch = searchText.isEmpty || item.title.localizedCaseInsensitiveContains(searchText)
            return matchesCategory && matchesSearch
        }
    }
    
    public var body: some View {
        ScrollView(.vertical, showsIndicators: false) {
            VStack(alignment: .leading, spacing: 20) {
                // Header
                headerSection
                
                // Search Field
                searchBar
                
                // Category Filter Chips
                filterChipsRow
                
                // Memory Cards List
                cardsList
                
                Spacer(minLength: 40)
            }
            .padding(.horizontal, 20)
            .padding(.top, 16)
        }
        .background(AsterTheme.ground.ignoresSafeArea())
        .sheet(item: $memoryToEdit) { memory in
            EditMemorySheet(memory: memory)
        }
        .sheet(item: $memoryToShare) { memory in
            ExplicitSharingModal(memory: memory)
        }
        .sheet(isPresented: $showingAddMemorySheet) {
            AddMemorySheet()
        }
        .alert("Delete Memory", isPresented: Binding(
            get: { memoryToDelete != nil },
            set: { if !$0 { memoryToDelete = nil } }
        )) {
            Button("Cancel", role: .cancel) { memoryToDelete = nil }
            Button("Delete", role: .destructive) {
                if let item = memoryToDelete {
                    appState.deleteMemory(id: item.id)
                    memoryToDelete = nil
                }
            }
        } message: {
            Text("Are you sure you want to delete this memory? This action cannot be undone.")
        }
    }
    
    // MARK: - Header
    private var headerSection: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("Memories")
                    .font(.system(size: 32, weight: .bold))
                    .foregroundColor(AsterTheme.creamText)
                
                Text("The little things that matter.")
                    .font(.system(size: 15, weight: .regular))
                    .foregroundColor(AsterTheme.mutedText)
            }
            
            Spacer()
            
            // Add Memory Button
            Button(action: { showingAddMemorySheet = true }) {
                ZStack {
                    Circle()
                        .fill(AsterTheme.surface)
                        .frame(width: 40, height: 40)
                        .overlay(Circle().stroke(AsterTheme.outline, lineWidth: 1))
                    
                    Image(systemName: "plus")
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundColor(AsterTheme.warmAmber)
                }
            }
        }
    }
    
    // MARK: - Search Bar
    private var searchBar: some View {
        HStack(spacing: 12) {
            Image(systemName: "magnifyingglass")
                .font(.system(size: 17, weight: .medium))
                .foregroundColor(AsterTheme.mutedText)
            
            TextField("Search memories", text: $searchText)
                .font(.system(size: 16, weight: .regular))
                .foregroundColor(AsterTheme.creamText)
                .accentColor(AsterTheme.warmAmber)
            
            if !searchText.isEmpty {
                Button(action: { searchText = "" }) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(AsterTheme.mutedText)
                }
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(AsterTheme.surface)
        .clipShape(Capsule())
        .overlay(Capsule().stroke(AsterTheme.outline, lineWidth: 1))
    }
    
    // MARK: - Filter Chips Row
    private var filterChipsRow: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 10) {
                ForEach(MemoryCategory.allCases) { category in
                    let isSelected = (selectedCategory == category)
                    Button(action: {
                        withAnimation(.spring(response: 0.25, dampingFraction: 0.8)) {
                            selectedCategory = category
                        }
                    }) {
                        Text(category.rawValue)
                            .font(.system(size: 14, weight: isSelected ? .bold : .medium))
                            .foregroundColor(isSelected ? AsterTheme.ground : AsterTheme.creamText)
                            .padding(.horizontal, 22)
                            .padding(.vertical, 9)
                            .background(isSelected ? AsterTheme.warmAmber : AsterTheme.surface)
                            .clipShape(Capsule())
                            .overlay(
                                Capsule()
                                    .stroke(isSelected ? Color.clear : AsterTheme.outline, lineWidth: 1)
                            )
                    }
                }
            }
        }
    }
    
    // MARK: - Cards List
    private var cardsList: some View {
        VStack(spacing: 12) {
            ForEach(filteredMemories) { memory in
                memoryCard(memory)
            }
        }
    }
    
    private func memoryCard(_ memory: MemoryItem) -> some View {
        HStack(alignment: .center, spacing: 16) {
            // Circle Badge with Amber Icon
            ZStack {
                Circle()
                    .fill(AsterTheme.elevatedSurface)
                    .frame(width: 44, height: 44)
                    .overlay(Circle().stroke(AsterTheme.outline, lineWidth: 1))
                
                Image(systemName: memory.iconType.systemName)
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(AsterTheme.warmAmber)
            }
            
            // Text Content
            VStack(alignment: .leading, spacing: 4) {
                Text(memory.title)
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(AsterTheme.creamText)
                    .lineLimit(2)
                    .multilineTextAlignment(.leading)
                
                Text(memory.relativeTime)
                    .font(.system(size: 13, weight: .regular))
                    .foregroundColor(AsterTheme.mutedText)
            }
            
            Spacer()
            
            // Actions: Share, Edit, Delete
            HStack(spacing: 16) {
                // Explicit Share Action
                Button(action: { memoryToShare = memory }) {
                    Image(systemName: "square.and.arrow.up")
                        .font(.system(size: 15, weight: .medium))
                        .foregroundColor(AsterTheme.mutedText)
                }
                
                // Edit (Pencil)
                Button(action: { memoryToEdit = memory }) {
                    Image(systemName: "pencil")
                        .font(.system(size: 16, weight: .medium))
                        .foregroundColor(AsterTheme.mutedText)
                }
                
                // Delete (Trash)
                Button(action: { memoryToDelete = memory }) {
                    Image(systemName: "trash")
                        .font(.system(size: 16, weight: .medium))
                        .foregroundColor(AsterTheme.mutedText)
                }
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 14)
        .background(AsterTheme.surface)
        .clipShape(RoundedRectangle(cornerRadius: AsterTheme.radiusCard, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: AsterTheme.radiusCard, style: .continuous)
                .stroke(AsterTheme.outline, lineWidth: 1)
        )
    }
}

// MARK: - Edit Memory Sheet
struct EditMemorySheet: View {
    @State var memory: MemoryItem
    @Environment(\.dismiss) var dismiss
    @ObservedObject var appState: AppState = AppState.shared
    
    var body: some View {
        NavigationStack {
            ZStack {
                AsterTheme.ground.ignoresSafeArea()
                
                Form {
                    Section("Memory Content") {
                        TextField("Memory title", text: $memory.title, axis: .vertical)
                            .foregroundColor(AsterTheme.creamText)
                    }
                    .listRowBackground(AsterTheme.surface)
                    
                    Section("Category") {
                        Picker("Category", selection: $memory.category) {
                            ForEach(MemoryCategory.allCases.filter { $0 != .all }) { cat in
                                Text(cat.rawValue).tag(cat)
                            }
                        }
                    }
                    .listRowBackground(AsterTheme.surface)
                }
                .scrollContentBackground(.hidden)
            }
            .navigationTitle("Edit Memory")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                        .foregroundColor(AsterTheme.mutedText)
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        appState.updateMemory(memory)
                        dismiss()
                    }
                    .foregroundColor(AsterTheme.warmAmber)
                    .fontWeight(.bold)
                }
            }
        }
    }
}

// MARK: - Add Memory Sheet
struct AddMemorySheet: View {
    @Environment(\.dismiss) var dismiss
    @ObservedObject var appState: AppState = AppState.shared
    @State private var title: String = ""
    @State private var category: MemoryCategory = .preferences
    @State private var iconType: MemoryIconType = .sun
    
    var body: some View {
        NavigationStack {
            ZStack {
                AsterTheme.ground.ignoresSafeArea()
                
                Form {
                    Section("New Memory") {
                        TextField("What would you like Aster to remember?", text: $title, axis: .vertical)
                            .foregroundColor(AsterTheme.creamText)
                    }
                    .listRowBackground(AsterTheme.surface)
                    
                    Section("Category") {
                        Picker("Category", selection: $category) {
                            ForEach(MemoryCategory.allCases.filter { $0 != .all }) { cat in
                                Text(cat.rawValue).tag(cat)
                            }
                        }
                    }
                    .listRowBackground(AsterTheme.surface)
                }
                .scrollContentBackground(.hidden)
            }
            .navigationTitle("Add Memory")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                        .foregroundColor(AsterTheme.mutedText)
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Add") {
                        appState.addMemory(title: title, category: category, iconType: iconType)
                        dismiss()
                    }
                    .disabled(title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    .foregroundColor(AsterTheme.warmAmber)
                    .fontWeight(.bold)
                }
            }
        }
    }
}

// MARK: - Explicit Sharing Modal (PRD Section 9.4)
struct ExplicitSharingModal: View {
    let memory: MemoryItem
    @Environment(\.dismiss) var dismiss
    @ObservedObject var appState: AppState = AppState.shared
    @State private var confirmed: Bool = false
    
    private var targetProfile: CompanionProfile? {
        appState.profiles.first(where: { $0.id != appState.activeProfileId })
    }
    
    var body: some View {
        NavigationStack {
            ZStack {
                AsterTheme.ground.ignoresSafeArea()
                
                VStack(spacing: 24) {
                    Image(systemName: "lock.shield.fill")
                        .font(.system(size: 48))
                        .foregroundColor(AsterTheme.warmAmber)
                        .padding(.top, 20)
                    
                    VStack(spacing: 8) {
                        Text("Explicit Profile Sharing")
                            .font(.system(size: 22, weight: .bold))
                            .foregroundColor(AsterTheme.creamText)
                        
                        Text("By default, companion profiles are strictly isolated. Confirming this action will create a signed audit entry and grant explicit access.")
                            .font(.system(size: 14))
                            .foregroundColor(AsterTheme.mutedText)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal)
                    }
                    
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Memory to share:")
                            .font(.system(size: 13))
                            .foregroundColor(AsterTheme.mutedText)
                        
                        HStack {
                            Image(systemName: memory.iconType.systemName)
                                .foregroundColor(AsterTheme.warmAmber)
                            Text(memory.title)
                                .font(.system(size: 15, weight: .semibold))
                                .foregroundColor(AsterTheme.creamText)
                        }
                        .padding()
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(AsterTheme.surface)
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                        
                        if let target = targetProfile {
                            HStack {
                                Text("Destination:")
                                    .font(.system(size: 13))
                                    .foregroundColor(AsterTheme.mutedText)
                                Spacer()
                                Text(target.name)
                                    .font(.system(size: 14, weight: .bold))
                                    .foregroundColor(AsterTheme.warmAmber)
                            }
                        }
                    }
                    .padding(.horizontal)
                    
                    Spacer()
                    
                    // Confirmation Button
                    Button(action: {
                        appState.explicitlyShareMemory(memory: memory)
                        confirmed = true
                        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                            dismiss()
                        }
                    }) {
                        Text(confirmed ? "Shared Successfully" : "Authorize & Share")
                            .font(.system(size: 16, weight: .bold))
                            .foregroundColor(AsterTheme.ground)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 16)
                            .background(confirmed ? AsterTheme.onlineGreen : AsterTheme.warmAmber)
                            .clipShape(Capsule())
                    }
                    .padding(.horizontal)
                    .padding(.bottom, 20)
                }
            }
            .navigationTitle("Share Memory")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                        .foregroundColor(AsterTheme.mutedText)
                }
            }
        }
    }
}
