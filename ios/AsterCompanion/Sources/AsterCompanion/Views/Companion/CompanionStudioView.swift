import SwiftUI

/// Companion Studio Customization View conforming strictly to reference screenshot 4.
public struct CompanionStudioView: View {
    @ObservedObject var appState: AppState = AppState.shared
    @State private var companionName: String = ""
    @State private var showingSavedToast: Bool = false
    @State private var showingSettings: Bool = false
    @FocusState private var isNameFocused: Bool
    
    public init() {}
    
    public var body: some View {
        ScrollView(.vertical, showsIndicators: false) {
            VStack(alignment: .leading, spacing: 22) {
                // MARK: - Header
                headerSection
                
                // MARK: - Avatar Preview with Radiant Amber Halo Glow
                avatarPreviewSection
                    .frame(maxWidth: .infinity)
                
                // MARK: - Profile Switcher Pills (Aster vs Nova)
                profileSwitcher
                    .padding(.top, 4)
                
                // MARK: - Name Section
                nameSection
                
                // MARK: - Appearance Section
                appearanceSection
                
                // MARK: - Voice Section
                voiceSection
                
                // MARK: - Save Button
                saveButton
                    .padding(.top, 10)
                
                Spacer(minLength: 40)
            }
            .padding(.horizontal, 20)
            .padding(.top, 16)
        }
        .background(AsterTheme.ground.ignoresSafeArea())
        .onAppear {
            companionName = appState.activeProfile.name
        }
        .onChange(of: appState.activeProfileId) { _ in
            companionName = appState.activeProfile.name
        }
        .overlay(alignment: .top) {
            if showingSavedToast {
                HStack(spacing: 8) {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(AsterTheme.onlineGreen)
                    Text("Companion settings saved")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(AsterTheme.creamText)
                }
                .padding(.horizontal, 18)
                .padding(.vertical, 10)
                .background(AsterTheme.surface)
                .clipShape(Capsule())
                .overlay(Capsule().stroke(AsterTheme.outline, lineWidth: 1))
                .transition(.move(edge: .top).combined(with: .opacity))
                .padding(.top, 16)
            }
        }
        .sheet(isPresented: $showingSettings) {
            SettingsSheetView()
        }
    }
    
    // MARK: - Header
    private var headerSection: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("Your companion")
                    .font(.system(size: 28, weight: .bold))
                    .foregroundColor(AsterTheme.creamText)
                
                Text("Make it yours")
                    .font(.system(size: 15, weight: .regular))
                    .foregroundColor(AsterTheme.mutedText)
            }
            
            Spacer()
            
            Button(action: { showingSettings = true }) {
                Image(systemName: "gearshape")
                    .font(.system(size: 20, weight: .medium))
                    .foregroundColor(AsterTheme.creamText)
                    .padding(8)
            }
        }
    }
    
    // MARK: - Large Avatar Preview with Amber Glow
    private var avatarPreviewSection: some View {
        ZStack {
            // Radiant Warm Amber Halo Glow
            Circle()
                .fill(
                    RadialGradient(
                        gradient: Gradient(colors: [
                            AsterTheme.warmAmber.opacity(0.65),
                            AsterTheme.warmAmber.opacity(0.25),
                            Color.clear
                        ]),
                        center: .center,
                        startRadius: 20,
                        endRadius: 110
                    )
                )
                .frame(width: 220, height: 220)
                .blur(radius: 20)
            
            // Large Avatar Circle
            Image(appState.activeProfile.avatarImageName, bundle: .main)
                .resizable()
                .aspectRatio(contentMode: .fill)
                .frame(width: 160, height: 160)
                .clipShape(Circle())
                .overlay(
                    Circle()
                        .stroke(AsterTheme.outline, lineWidth: 2)
                )
        }
        .frame(height: 200)
    }
    
    // MARK: - Profile Switcher (Aster vs Nova, Max 2 Profiles)
    private var profileSwitcher: some View {
        HStack(spacing: 0) {
            ForEach(appState.profiles) { profile in
                let isSelected = (profile.id == appState.activeProfileId)
                Button(action: {
                    withAnimation(.spring(response: 0.3, dampingFraction: 0.8)) {
                        appState.switchProfile(to: profile.id)
                    }
                }) {
                    Text(profile.name)
                        .font(.system(size: 15, weight: isSelected ? .bold : .medium))
                        .foregroundColor(isSelected ? AsterTheme.warmAmber : AsterTheme.mutedText)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 12)
                        .background(isSelected ? AsterTheme.surface : Color.clear)
                        .clipShape(Capsule())
                        .overlay(
                            Capsule()
                                .stroke(isSelected ? AsterTheme.warmAmber : Color.clear, lineWidth: 1.5)
                        )
                }
            }
        }
        .padding(4)
        .background(AsterTheme.surface)
        .clipShape(Capsule())
        .overlay(
            Capsule()
                .stroke(AsterTheme.outline, lineWidth: 1)
        )
    }
    
    // MARK: - Name Section
    private var nameSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Name")
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(AsterTheme.mutedText)
            
            HStack {
                TextField("Companion Name", text: $companionName)
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(AsterTheme.creamText)
                    .accentColor(AsterTheme.warmAmber)
                    .focused($isNameFocused)
                    .onSubmit {
                        appState.updateActiveProfileName(companionName)
                    }
                
                Button(action: { isNameFocused = true }) {
                    Image(systemName: "pencil")
                        .font(.system(size: 16, weight: .medium))
                        .foregroundColor(AsterTheme.mutedText)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 14)
            .background(AsterTheme.surface)
            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .stroke(AsterTheme.outline, lineWidth: 1)
            )
        }
    }
    
    // MARK: - Appearance Section
    private var appearanceSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Appearance")
                .font(.system(size: 17, weight: .bold))
                .foregroundColor(AsterTheme.creamText)
            
            // Hair Color Swatches
            VStack(alignment: .leading, spacing: 10) {
                Text("Hair")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(AsterTheme.mutedText)
                
                HStack(spacing: 16) {
                    ForEach(HairColor.allCases) { hair in
                        let isSelected = (appState.activeProfile.hairColor == hair)
                        VStack(spacing: 6) {
                            Button(action: {
                                withAnimation { appState.updateActiveProfileHair(hair) }
                            }) {
                                Circle()
                                    .fill(hair.color)
                                    .frame(width: 38, height: 38)
                                    .overlay(
                                        Circle()
                                            .stroke(isSelected ? AsterTheme.warmAmber : AsterTheme.outline, lineWidth: isSelected ? 2.5 : 1)
                                            .padding(isSelected ? -4 : 0)
                                    )
                            }
                            
                            Text(hair.rawValue)
                                .font(.system(size: 12, weight: isSelected ? .bold : .regular))
                                .foregroundColor(isSelected ? AsterTheme.creamText : AsterTheme.mutedText)
                        }
                    }
                }
            }
            
            // Eye Color Swatches
            VStack(alignment: .leading, spacing: 10) {
                Text("Eyes")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(AsterTheme.mutedText)
                
                HStack(spacing: 16) {
                    ForEach(EyeColor.allCases) { eye in
                        let isSelected = (appState.activeProfile.eyeColor == eye)
                        VStack(spacing: 6) {
                            Button(action: {
                                withAnimation { appState.updateActiveProfileEyes(eye) }
                            }) {
                                Circle()
                                    .fill(eye.color)
                                    .frame(width: 38, height: 38)
                                    .overlay(
                                        Circle()
                                            .stroke(isSelected ? AsterTheme.warmAmber : AsterTheme.outline, lineWidth: isSelected ? 2.5 : 1)
                                            .padding(isSelected ? -4 : 0)
                                    )
                            }
                            
                            Text(eye.rawValue)
                                .font(.system(size: 12, weight: isSelected ? .bold : .regular))
                                .foregroundColor(isSelected ? AsterTheme.creamText : AsterTheme.mutedText)
                        }
                    }
                }
            }
            
            // Style Chips
            VStack(alignment: .leading, spacing: 10) {
                Text("Style")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(AsterTheme.mutedText)
                
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 10) {
                        ForEach(CompanionStyle.allCases) { style in
                            let isSelected = (appState.activeProfile.style == style)
                            Button(action: {
                                withAnimation { appState.updateActiveProfileStyle(style) }
                            }) {
                                Text(style.rawValue)
                                    .font(.system(size: 14, weight: isSelected ? .bold : .medium))
                                    .foregroundColor(isSelected ? AsterTheme.warmAmber : AsterTheme.creamText)
                                    .padding(.horizontal, 18)
                                    .padding(.vertical, 10)
                                    .background(AsterTheme.surface)
                                    .clipShape(Capsule())
                                    .overlay(
                                        Capsule()
                                            .stroke(isSelected ? AsterTheme.warmAmber : AsterTheme.outline, lineWidth: 1.5)
                                    )
                            }
                        }
                    }
                }
            }
        }
    }
    
    // MARK: - Voice Section
    private var voiceSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Voice")
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(AsterTheme.mutedText)
            
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 10) {
                    ForEach(VoiceOption.allCases) { voice in
                        let isSelected = (appState.activeProfile.voice == voice)
                        Button(action: {
                            withAnimation { appState.updateActiveProfileVoice(voice) }
                        }) {
                            Text(voice.rawValue)
                                .font(.system(size: 14, weight: isSelected ? .bold : .medium))
                                .foregroundColor(isSelected ? AsterTheme.warmAmber : AsterTheme.creamText)
                                .padding(.horizontal, 18)
                                .padding(.vertical, 10)
                                .background(AsterTheme.surface)
                                .clipShape(Capsule())
                                .overlay(
                                    Capsule()
                                        .stroke(isSelected ? AsterTheme.warmAmber : AsterTheme.outline, lineWidth: 1.5)
                                )
                        }
                    }
                }
            }
        }
    }
    
    // MARK: - Save Button
    private var saveButton: some View {
        Button(action: {
            appState.updateActiveProfileName(companionName)
            appState.saveActiveProfile()
            withAnimation {
                showingSavedToast = true
            }
            DispatchQueue.main.asyncAfter(deadline: .now() + 2.5) {
                withAnimation {
                    showingSavedToast = false
                }
            }
        }) {
            Text("Save companion")
                .font(.system(size: 16, weight: .bold))
                .foregroundColor(AsterTheme.ground)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 16)
                .background(AsterTheme.warmAmber)
                .clipShape(Capsule())
        }
    }
}
