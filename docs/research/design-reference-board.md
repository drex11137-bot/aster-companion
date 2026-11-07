# GAUGE: Design Reference Board & Visual Language Specification
## Benchmarks, Anti-Slop Discipline, Banned Colors Audit, and Accessibility Architecture

This design reference document defines the visual direction, design tokens, color palette, typography hierarchy, and accessibility rules for **GAUGE: System Monitor**, grounded in the Anti-Slop UI Doctrine (`GEMINI.md`, `stopslop.md`, and `antislop.md`).

---

## 1. Visual Thesis & Design Identity

> **Visual Thesis:** GAUGE looks and operates like a high-precision laboratory instrument—calm, observant, authoritative, and humane. It replaces the dark-neon generic "AI dashboard" with a disciplined, high-contrast technical aesthetic inspired by physical oscilloscopes, multimeter dials, and precision aerospace telemetry.

### What GAUGE Refuses to Do (Negative Constraints)
1. **No Purple / Indigo Gradients:** Zero blue-to-purple diagonal gradients across buttons, cards, headers, or backgrounds.
2. **No Generic Rounded-2xl Card Soup:** No repetitive `rounded-2xl` cards stacked inside cards with identical padding and diffuse box-shadows. Surfaces are separated by subtle lightness steps and clean 1px structural rules.
3. **No Decorative Placeholders:** Zero fake window chrome (traffic light dots), zero fake code snippets, zero pulsing "Active" dots carrying no real state, and zero sparkles.
4. **No Uninformative Charts:** Charts must always have labeled axes, units, time ranges, and readable numbers. No decorative sparklines without scales.

---

## 2. Banned Colors Audit & Verification

As mandated by project specifications, the following 8 hex colors are **strictly prohibited** from all stylesheets, themes, drawables, SVGs, and vector assets:

| Banned Color Hex | Status in GAUGE | Replacement Token & Rationale |
| :---: | :---: | :--- |
| `#0b0d11` | **PROHIBITED** | Replaced by `GaugeGroundDark` (`#111318` - Warm Slate Obsidian) |
| `#14171d` | **PROHIBITED** | Replaced by `GaugeSurfaceDark` (`#1A1C23` - Laboratory Technical Surface) |
| `#1c2029` | **PROHIBITED** | Replaced by `GaugeSurfaceElevated` (`#232630` - Focused Component Surface) |
| `#222733` | **PROHIBITED** | Replaced by `GaugeSurfaceHighlight` (`#2C303D` - Interactive Surface Active) |
| `#2a303e` | **PROHIBITED** | Replaced by `GaugeOutlineDark` (`#383D4E` - High-Contrast Structural Rule) |
| `#343b4d` | **PROHIBITED** | Replaced by `GaugeOutlineActive` (`#474D63` - Focused Control Border) |
| `#252a36` | **PROHIBITED** | Replaced by `GaugeSurfaceContainer` (`#20222B` - Grouping Container) |
| `#12151b` | **PROHIBITED** | Replaced by `GaugeSurfaceHeader` (`#15171F` - Header & App Bar Ground) |

*Verification:* Automated repo scan confirms 0 occurrences of these 8 hex strings across all code and assets.

---

## 3. Approved Semantic Color Tokens (WCAG 2.2 AA / AAA Compliant)

All colors are defined as semantic tokens in `ui/theme/Color.kt` and `ui/theme/Theme.kt`.

### Dark Theme (Default Telemetry Mode)
- **Ground (Base Background):** `#111318` (Deep Matte Obsidian Slate)
- **Surface (Card & Container):** `#1A1C23` (Laboratory Surface, +5% lightness shift)
- **Surface Elevated (Dialogs & Menus):** `#232630` (Elevated Surface)
- **Surface Highlight (Active / Pressed):** `#2C303D` (Subtle selection)
- **Outline / Border (Structural Rule):** `#383D4E` (1px clean separation)
- **Ink Primary (Headings & Values):** `#F3F4F6` (Contrast ratio 14.8:1 against Ground — AAA)
- **Ink Secondary (Labels & Metadata):** `#9CA3AF` (Contrast ratio 6.2:1 against Ground — AA)
- **Accent Primary (Active Action / Selected):** `#06B6D4` (Electric Laboratory Cyan)
- **Signal Normal / Healthy:** `#10B981` (Telemetry Emerald)
- **Signal Warning / Elevated:** `#F59E0B` (Instrument Amber)
- **Signal Critical / Alert:** `#EF4444` (Precision Alert Red)
- **Signal Charging / Power:** `#3B82F6` (Ion Blue)

### Light Theme (Paper Telemetry Mode)
- **Ground (Base Background):** `#F8F9FA` (Clean Off-White Technical Paper)
- **Surface (Card & Container):** `#FFFFFF` (Pure Crisp White)
- **Surface Elevated:** `#F1F3F5` (Subtle Card Surface)
- **Outline / Border:** `#E5E7EB` (Clean 1px Technical Rule)
- **Ink Primary:** `#111827` (Deep Asphalt Charcoal — 15.2:1 AAA)
- **Ink Secondary:** `#4B5563` (Muted Technical Ink — 7.1:1 AAA)
- **Accent Primary:** `#0891B2` (Deep Instrument Cyan)
- **Signal Normal:** `#059669` (Deep Emerald)
- **Signal Warning:** `#D97706` (Deep Amber)
- **Signal Critical:** `#DC2626` (Deep Red)

---

## 4. Typography Hierarchy & Number Formatting

- **Display & Section Titles:** Clean Grotesque / Sans (`FontFamily.SansSerif`), weights `Medium` (500) and `SemiBold` (600).
- **Telemetry Numbers & Data Values:** Monospace tabular numbers (`FontFamily.Monospace`, `FontWeight.Bold`), ensuring numbers line up vertically without layout jitter when streaming live ticks.
- **Micro-Copy & Units:** Explicit uppercase tracking (`0.05em`), 11–12sp, with high-contrast secondary ink. Units are always displayed adjacent to numbers (`MB`, `GB`, `mA`, `mV`, `°C`, `Hz`, `ms`).

---

## 5. Dual-Encoding Accessibility (WCAG 2.2 Criterion 1.4.1)

Color is **never the sole indicator** of state:
- **Normal Status:** Emerald Green + Checkmark / Dot icon + Text label (`Optimal` / `Normal`)
- **Elevated Status:** Amber + Warning Triangle icon + Text label (`Elevated` / `Throttled`)
- **Critical Status:** Red Alert + Hexagon / Octagon icon + Text label (`Critical` / `Low Memory`)
- **Touch Targets:** All interactive icons, chips, and buttons maintain a minimum touch target size of **48 x 48 dp**.
- **Screen Reader Support:** All live updating values specify `accessibilityLiveRegion = "polite"` with explicit content descriptions (e.g., `contentDescription = "Available memory: 3.2 gigabytes out of 8.0 gigabytes"`).

---

## 6. Original Mascot Specification: "Gaugey"

- **Character Identity:** A compact, expressive dial-gauge character consisting of a circular meter housing, an expressive needle pointer, two calm inquisitive eyes, and subtle indicator tick marks.
- **Roles in the Product:**
  1. **Onboarding Guide:** Introduces app capabilities and explains why permissions matter without marketing fluff.
  2. **Calm State (Normal):** Needle centered at 45°, relaxed observant eyes.
  3. **Busy State (High CPU / Heavy Work):** Needle actively pulsing, focused forward glance.
  4. **Throttled State (Thermal / Low Memory):** Needle resting at upper warning arc with attentive expression.
  5. **Charging State (Plugged In):** Small lightning spark accent atop dial.
- **Reduced Motion Support:** Respects system `prefers-reduced-motion` / "Remove animations" by rendering static vector illustrations without looping springs.
- **Asset Technology:** Clean vector SVG rendered directly via Compose `Canvas` and vector paths, with zero third-party heavy binary dependencies.
