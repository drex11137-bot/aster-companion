# Aster Companion Research Dossier: Design System, Visual Tokens & Native Mobile UI Architecture

**Domain Key**: `09_design_system_tokens`  
**Generated**: November 2026  
**Total Queries Executed**: 20  

## Executive Findings & Architectural Directives

This document compiles verified engineering research for Design System, Visual Tokens & Native Mobile UI Architecture in the Aster Companion ecosystem. These findings directly inform our Supabase backend, Android Compose client, iOS SwiftUI app, laptop web client, and multimodal AI pipelines.

---

## Query Inventory & Verified Evidence

### Q1: Premium dark mode design graphite black warm amber orange accent color palette tokens

- **[Dark Luxury — Editorial](https://www.skillsui.app/previews/dark-luxury.html)** (Exa)
- **[Themes for shadcn/ui — Vibra UI](https://vibraui.com/themes)** (Exa)
- **[shadcn/ui Themes: install a real design system in one command · CSS Crème](https://csscreme.com/themes)** (Exa)
- **[Pipe design system | Refero Styles](https://styles.refero.design/style/ab201ed7-928f-4080-ba95-c3992311e39d)** (Exa)

### Q2: Restrained violet indigo color accent in dark UI chat bubbles contrast accessibility

- **[Beyond Dark Mode: Comprehensive Color Contrast Strategies for Accessibility | Accessible Web Webinar](https://www.youtube.com/watch?v=34MjM67qOPM)** (Tavily)
  > "### Transcript [0:04] So, color contrast is one of the most fundamental  parts of accessibility because it directly affects   how clearly users can perceive text and interface  elements. Strong contrast especially supports   [0:13] people with low vision. When text blends into the  background, it be"
- **[Color Contrast Accessibility: Complete WCAG 2025 Guide + Free Checker Tool - AllAccessible Blog | AllAccessible](https://www.allaccessible.org/blog/color-contrast-accessibility-wcag-guide-2025)** (Tavily)
  > "/ 7.0:1 - Focus / / Backgrounds for white text / --bg-primary: #0052A3; / 4.9:1 / --bg-secondary: #404040; / 10.7:1 / / Status colors / --success-text: #155724; / 7.0:1 / --success-bg: #218838; / 4.0:1 white text / --error-text: #B71C1C; / 7.2:1 / --error-bg: #D32F2F; / 4.5:1 white text / --warning-"
- **[WebAIM: Contrast and Color Accessibility - Understanding WCAG 2 Contrast and Color Requirements](https://webaim.org/articles/contrast)** (Tavily)
  > "> The visual presentation of the following have a contrast ratio of at least 3:1 against adjacent color(s): > >  User Interface Components: Visual information required to identify user interface components and states, except for inactive components or where the appearance of the component is determi"

### Q3: Jetpack Compose Material 3 DarkColorScheme custom typography shapes spacing tokens

- **[Material Design 3 in Compose  |  Jetpack Compose  |  Android Developers](https://developer.android.com/develop/ui/compose/designsystems/material3)** (Exa)
- **[Custom design systems in Compose  |  Jetpack Compose  |  Android Developers](https://developer.android.com/develop/ui/compose/designsystems/custom)** (Exa)
- **[MaterialTheme  |  API reference  |  Android Developers](https://developer.android.com/reference/kotlin/androidx/compose/material3/MaterialTheme.composable)** (Exa)
- **[Migrate XML themes to Material 3 in Compose  |  Jetpack Compose  |  Android Developers](https://developer.android.com/develop/ui/compose/designsystems/migrate-xml-theme-to-compose)** (Exa)

### Q4: SwiftUI design system Color assets custom typography view modifiers dark theme

- **[Defining dynamic colors in Swift | Swift by Sundell](https://www.swiftbysundell.com/articles/defining-dynamic-colors-in-swift)** (Tavily)
  > "However, while the above technique certainly works, things can quickly get quite messy and repetitive if we need to perform the same kind of observation within many different views. One way to address that when using SwiftUI would be to instead create a reusable view modifier that lets us specify se"
- **[15 dark mode color website schemes: examples that stand out](https://www.ladybugz.com/dark-color-website-schemes-examples)** (Tavily)
  > "Website Design Highlights: The customized dark web theme uses deep tones along with animated platform visuals and human-centered storytelling that bring the science to life. The  contrast between the dark background and vivid animated sequences and bright yellow accents creates a sophisticated, scie"
- **[Dark Website Design - Professional Dark Theme & Dark Mode Website Design Services](https://mycleverai.com/dark-website-design)** (Tavily)
  > "Dark websites should create sophisticated experiences through careful contrast management, elegant typography, and strategic accent colors that enhance readability and visual appeal.  Color contrast ratios, text readability, and accessibility standards ensure dark themes remain usable and inclusive"

### Q5: Tailwind CSS custom theme configuration dark surface colors warm glowing borders

- **[Theme variables - Core concepts](https://tailwindcss.com/docs/theme)** (Exa)
- **[Tailwind v4 Theming for Wensity Components | Wensity UI](https://ui.wensity.com/docs/theming)** (Exa)
- **[Glow design system | Agentic Boilerplate](https://agenticboilerplate.com/designs/glow)** (Exa)
- **[Theming — Aura UI Docs](https://aura-ui.com/docs/theming)** (Exa)

### Q6: Mobile bottom navigation bar design 4 tabs pill indicator active state smooth transition

- **[Build a Bottom Navigation Bar with AI - Mobile Nav | RationalGo](https://rationalgo.ai/resources/app-builder/build-bottom-navigation-bar-with-ai-mobile)** (Tavily)
  > "1. Prompt RationalGo to create a bottom navigation bar with 5 tabs 2. Add icons for each tab: Home, Search, Plus (create), Bell, User 3. Implement animated active indicator (sliding pill or underline) 4. Add a larger center Create button with raised circular style 5. Include notification badge on th"
- **[30+ CSS Tab Bars: Responsive Bottom Navigation Snippets](https://freefrontend.com/css-tab-bars)** (Tavily)
  > "Symmetric horizontal spacing and segmented boundaries are mapped natively using CSS Grid and Flexbox configurations.  Active tracking highlights and indicators leverage the native View Transitions API, automatically morphing coordinates on GPU layers.  To preserve critical INP (Interaction to Next P"
- **[Bottom navigation](https://m2.material.io/components/bottom-navigation)** (Tavily)
  > "[](https://m2.material.io/components/bottom-navigation#main_content). [Use Material 3](https://m3.material.io/). *   [Components](https://m2.material.io/components). *   [App bars: bottom](https://m2.material.io/components/app-bars-bottom "App bars: bottom"). *   [App bars: top](https://m2.material."

### Q7: Modern AI companion chat UI design streaming message bubbles timeline schedule cards

- **[AI chat · UI Catalogue](https://ui.tailor.tech/patterns/ai-chat)** (Exa)
- **[Elements — assistant-ui](https://www.assistant-ui.com/elements)** (Exa)
- **[Chat — Echo AI | Pepper UI](https://design.mobupps.com/patterns/chat/)** (Exa)
- **[AgentChat - Neon UI](https://ui.neon.com/agent/agent-chat)** (Exa)

### Q8: Memory management list view category filter chips search bar edit delete actions UI

- **[Chips – Material Design 3](https://m3.material.io/components/chips/guidelines)** (Tavily)
  > "More on expanded breakpoints , filter chips may contain a trailing icon to directly remove the chip or open a menu of options.  In   compact windows  Window widths smaller than 600dp, such as a phone in portrait orientation.  More on compact breakpoints , the trailing icon's target area is too small"
- **[Chip Component – Anatomy, States, and Usage](https://designsystems.surf/blueprints/chip)** (Tavily)
  > "### Action  Chips are designed not only for filtering, multi-select, or tagging, but they can also initiate actions, dynamically offering users quick choices of related actions in the right context.  Chip component UI Design ysage example Action [...] Consider a project management app, where Chips c"
- **[Chip UI design and how chips differ from tags and badges | Setproduct Blog](https://www.setproduct.com/blog/chip-ui-design)** (Tavily)
  > "Solution: Include a clear and accessible close button or an ❌ icon next to each Chip (on hover state), allowing users to easily remove unwanted selections. Consider providing additional confirmation if permanent removal is required to prevent accidental deletions.  ### Use Micro-interactions  UX Pro"

### Q9: Companion studio profile switcher avatar preview color swatches style selector design

- **[Companion Picker · UI Library · Levenium UI](https://ui.levenium.com/ui/companion-picker)** (Exa)
- **[apps/desktop/src/app/chat/sidebar/profile-switcher.tsx](https://github.com/NousResearch/hermes-agent/blob/ee472a7f/apps/desktop/src/app/chat/sidebar/profile-switcher.tsx)** (Exa)
- **[Avatar Studio · Tobs](https://tobs.app/en/avatar)** (Exa)
- **[desktop/src/features/profile/ui/ProfileAvatarEditor.tsx](https://github.com/block/buzz/blob/7e34bee6/desktop/src/features/profile/ui/ProfileAvatarEditor.tsx)** (Exa)

### Q10: Micro-interactions haptic feedback polished animations Compose AnimatedVisibility

- **[Creating Micro-Interactions in Android Apps Using Compose: The Art of Delightful Motion](https://medium.com/@androidlab/creating-micro-interactions-in-android-apps-using-compose-the-art-of-delightful-motion-854886405b68)** (Tavily)
  > "[](  Listen  Share  Transform your Android UX with subtle animations, haptic feedback, and polished interactions that make users smile without overwhelming your codebase.  Press enter or click to view image in full size  Image 3: 3D Android device displaying animated micro-interactions with floating"
- **[Jetpack Compose Animation Tutorials for Beginners: Build Smooth UI Motion from Scratch](https://www.news.climate.columbia.edu/jetpack-compose-4d6478)** (Tavily)
  > "Beyond efficiency, Compose animations enhance user engagement by making interactions feel responsive and intentional. Micro-interactions—like a button’s ripple effect or a list item’s smooth scroll—subtly guide users through an app. For developers, this translates to higher retention and satisfactio"
- **[AnimatedVisibility API Reference in animation](https://composables.com/jetpack-compose/androidx.compose.animation/animation/composable-functions/AnimatedVisibility/api)** (Tavily)
  > "This extension function creates an AnimatedVisibility composable as a child Transition of the given Transition. This means: 1) the enter/exit transition is now triggered by the provided `Transition`'s `targetState` change. When the targetState changes, the visibility will be derived using the `visib"

### Q11: Dynamic font scaling accessibility Dynamic Type iOS scalable fonts Android sp

- **[Text scaling - Android Accessibility Help](https://support.google.com/accessibility/android/answer/12159181?hl=en)** (Exa)
- **[Scaling fonts automatically | Apple Developer Documentation](https://developer.apple.com/documentation/uikit/scaling-fonts-automatically)** (Exa)
- **[Get started with Dynamic Type - WWDC24 - Videos - Apple Developer](https://developer.apple.com/videos/play/wwdc2024/10074/)** (Exa)
- **[Content resizing - Accessibility for Products - BBC](https://www.bbc.co.uk/accessibility/forproducts/guides/mobile/content-resizing)** (Exa)

### Q12: High contrast mode and dark light theme switching design tokens WCAG 2.1 AA

- **[Dark Mode Accessibility: WCAG Contrast Requirements 2026](https://www.adaguard.io/dark-mode-accessibility-wcag-contrast)** (Tavily)
  > "WCAG 2.1 Level AA sets two minimum contrast ratios that apply to every color combination on your site — in every theme:  1.4.3 Contrast (Minimum): At least 4.5:1 for normal text (under 18pt regular or 14pt bold). At least 3:1 for large text (18pt+ regular or 14pt+ bold). This ratio applies to text a"
- **[Dark Mode Accessibility - Is It Better, and What WCAG Says](https://www.webyes.com/blogs/dark-mode-accessibility)** (Tavily)
  > "For swapping an asset outright, the element takes a media query, so it can carry both files:  ```   Acme  ```  ## Is dark mode the same as high contrast mode?  No. Windows Contrast Themes and `prefers-contrast` are separate settings, and a dark theme does not satisfy either. Two media features cover"
- **[Design an Accessible Color System: Contrast, States, Dark Mode and CSS Tokens · Web2Generators](https://www.web2generators.com/blog/design-an-accessible-color-system-contrast-states-dark-mode-and-css-tokens)** (Tavily)
  > "## Test focus and Windows high contrast modes  Keyboard navigation needs a visible indication of focus. Test Tab and Shift+Tab from the page header through dialogs and forms. A `:focus-visible` ring should remain recognizable on links, filled buttons and focusable cards in both themes. Check that st"

### Q13: Schedule timeline card UI component with milestone icons and connector lines

- **[Schedule Timeline — Card Component (HTML, CSS, JS / React)](https://builder.atheros.ai/components/schedule-timeline)** (Exa)
- **[ABUI | Components, blocks, and utilities by Antonio Brandao.](https://www.abui.io/components/timeline-steps)** (Exa)
- **[Milestone Timeline Cards - Free Component | ADYSRE](https://www.adysre.com/components/timeline-milestones-cards)** (Exa)
- **[Timeline: React + Tailwind component | Ballmac UI](https://ui.ballmac.com/components/timeline)** (Exa)

### Q14: Citation chip pill component displaying memory sources used in AI response

- **[GPT-5.5 Instant Memory Now Shows Which Saved Memory It Used — And 4 Other Hidden UI Changes | MindStudio](https://www.mindstudio.ai/blog/gpt-55-instant-memory-source-citations-hidden-ui-changes)** (Tavily)
  > "Here’s what the update actually looks like in practice, plus four other interface and behavioral changes that shipped alongside it.  ## What You Actually Get From the Memory Citation Update  When you ask GPT-5.5 Instant something that touches on your saved memories — say, “tell me about myself” or a"
- **[Data on AI chip components | Epoch AI](https://epoch.ai/data/ai-chip-components)** (Tavily)
  > "### Citation  Epoch AI, 'Data on AI chip components'. Published online at epoch.ai. Retrieved from ' [online resource]. Accessed 11 Oct 2026.  ### BibTeX Citation  @misc{EpochAIChipComponents2026, title = {{Data on AI chip components}}, author = {{Epoch AI}}, year = {2026}, month = {7}, url = { note"
- **[Memory Systems for AI: Part 5 - Rambus](https://www.rambus.com/blogs/memory-systems-for-ai-part-5)** (Tavily)
  > "The slide above illustrates the most common types of memory used in high-performance AI applications: on-chip memory, high bandwidth memory (HBM) and Graphics DDR SDRAM (GDDR SDRAM). On-chip memory, in the form of SRAM, is by far the highest bandwidth and most power-efficient solution available toda"

### Q15: Quick action suggestion chips above chat input composer Material 3 AssistChip

- **[Create a chip to represent complex entities  |  Jetpack Compose  |  Android Developers](https://developer.android.com/develop/ui/compose/quick-guides/content/create-chip)** (Exa)
- **[Chip  |  Jetpack Compose  |  Android Developers](https://developer.android.com/develop/ui/compose/components/chip)** (Exa)
- **[AssistChip  |  API reference  |  Android Developers](https://developer.android.com/reference/kotlin/androidx/compose/material3/AssistChip.composable)** (Exa)
- **[SuggestionChip  |  API reference  |  Android Developers](https://developer.android.com/reference/kotlin/androidx/compose/material3/SuggestionChip.composable)** (Exa)

### Q16: Full screen voice call UI with ambient animated waveform gradient visualizer

- **[Audio Waveform Visualizer Effect In OBS FREE!](https://www.youtube.com/watch?v=-wDZf-weTEs)** (Tavily)
  > "[0:52] There is a Linux install, a Mac O S install, and two different versions of the Windows install. [0:59] We are going to select the setup exe and click on that to download it. [1:03] Then all we need to do is browse to where that file is saved and double click it. It'll bring up this Window is"
- **[Audio visualizer | LiveKit Documentation](https://docs.livekit.io/frontends/agents-ui/audio-visualizer/prebuilt)** (Tavily)
  > "## Overview  Audio visualizer components give your voice agent a visual presence in your application. They render animated visualizations driven by two inputs: the audio track's volume levels and the agent's current state (listening, thinking, speaking). This combination means the visualizer respond"
- **[WaveForm: the Background Sound Visualizer](https://www.instructables.com/WaveForm-the-Background-Sound-Visualizer)** (Tavily)
  > "const int MIC_PIN = 28; // GP28 (your working mic pin)  const int FRAME_MS = 16; // ~60 FPS  const int OVERSAMP = 128; // samples per frame      // Horizontal spacing between points: 1 = packed, 2 = more spread, 3 = even more  const int X_STEP = 2;  const int NUM_POINTS = WIDTH / X_STEP; // how many"

### Q17: Awareness floating pill status indicator with pulse animation and status dot

- **[floating-status-pill — shadcn block · Motion Menu | registry.directory](https://registry.directory/motion-menu/floating-status-pill)** (Exa)
- **[Pill](https://www.shadcn.io/components/pill)** (Exa)
- **[frontend/src/components/FloatingPill.jsx](https://github.com/debpalash/OmniVoice-Studio/blob/766e2f72/frontend/src/components/FloatingPill.jsx)** (Exa)
- **[Status — nauvalazhar/ai](https://ai.nauv.al/status)** (Exa)

### Q18: Empty states loading skeletons error states with retry buttons mobile UX best practice

- **[Lesson 19 : Designing Empty, Loading & Error States | UI/UX Design Best Practices](https://www.youtube.com/watch?v=Y913fPwY7Sg)** (Tavily)
  > "Learn how to design effective empty states, loading states, and error states for modern web applications with this practical UI/UX design tutorial. Discover UI design principles, user experience best practices, skeleton screens, loading indicators, error messages, empty state illustrations, and user"
- **[Empty States in UX: Types, Examples & Best Practices for SaaS (2026)](https://kompassify.com/blog/empty-states-guide)** (Tavily)
  > "An empty state means there is legitimately nothing to display: no data yet, no results for this query, or everything completed. An error state means content exists (or should) but couldn't be shown because something failed: a network problem, a server error, a timeout. They need different messages:"
- **[Empty State UX Examples & Best Practices - Pencil & Paper](https://www.pencilandpaper.io/articles/empty-states)** (Tavily)
  > "📖 Information-focused – these empty states are serving to inform the user that the container is empty, rather than letting them assume the system is broken. You can even take this to the extreme, and pack your empty containers with onboarding content and other learning opportunities.  👟 Action-focus"

### Q19: Settings screen layout categorized sections toggle switches chevron navigations

- **[Android settings design guidelines  |  Android OS core topics  |  Android Open Source Project](https://source.android.com/docs/core/settings/settings-guidelines)** (Exa)
- **[Settings - Patterns - Material Design](https://m1.material.io/patterns/settings.html)** (Exa)
- **[Settings Layout · VegaStack Design](https://design.vegastack.com/docs/components/settings-layout)** (Exa)
- **[Settings Page Examples: 667 Real Product Screens | Screenrove](https://screenrove.com/patterns/settings-pages)** (Exa)

### Q20: Responsive layout adaptation mobile portrait tablet dual-pane desktop window

- **[Responsive Design for Mobile Apps: Principles and Best Practices](https://www.saasfactor.co/blogs/responsive-design-for-mobile-app)** (Tavily)
  > "The redesign introduced three key shifts. The portfolio dashboard moved from a dense table to a mobile-first card layout, with a two-column expanded view on tablet. Navigation shifted from a compressed sidebar to a bottom tab bar on mobile and a persistent sidebar on tablet. The onboarding flow was"
- **[Responsive/adaptive design with views  |  Views  |  Android Developers](https://developer.android.com/develop/ui/views/layout/responsive-adaptive-design-with-views)** (Tavily)
  > "## Adaptive design  Your app's layout should always be responsive to different display sizes. However, even a responsive layout can't provide the best user experience on every device or multi‑window mode display. For example, the UI you designed for a phone, probably doesn't provide an optimal user"
- **[Responsive design techniques - Windows apps | Microsoft Learn](https://learn.microsoft.com/en-us/windows/apps/design/layout/responsive-design)** (Tavily)
  > "# Responsive design techniques  Responsive design uses just one layout where the content is fluid and can adapt to changing window sizes. Responsive design lets you build a feature one time and expect it to work across all screen sizes. Adaptive design is similar, but replaces one layout with anothe"

