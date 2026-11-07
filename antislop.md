

## RESEARCH SNAPSHOT — HIGH-SIGNAL FINDINGS

| Finding | Evidence | Caveat |
|---|---|---|
| The current anti-slop discourse repeatedly identifies purple/indigo gradients, Inter/system fonts, centered heroes, three-card grids, uniform rounding, glass and diffuse shadows | Multiple independent 2026 taxonomies and practitioner guides | These patterns are not uniquely AI-generated |
| Current anti-slop catalogs have expanded beyond the original “purple gradient” stereotype into bento, editorial/cream aesthetics, fake trust chrome, generic motion, AI iconography and state incompleteness | 2026 public taxonomies/repos | Catalogs are community-maintained, not standards bodies |
| Human-designed pages can legitimately contain individual tells; community discussion explicitly warns against treating one tell as proof | Reddit r/UI_Design and r/webdesign discussions | Qualitative evidence |
| LLMs can produce manipulative interaction patterns under prompting | DarkBench, ICLR 2025 | DarkBench focuses on LLM interactions/dark patterns rather than visual style similarity |
| Tool-based UI generation is still an active research area with benchmarks such as CANVAS | CANVAS (2025) | Benchmark performance does not directly measure “slop” |
| WCAG 2.2 explicitly addresses contrast, focus, target size, hover/focus content and animation | W3C | Accessibility is separate from aesthetic authorship |
| 2026 practitioner studies suggest AI-era design tells are becoming more prevalent while ordinary basic implementation defects may decline | Precious Studio “Slop Patterns” note | Self-reported observational study; not peer-reviewed |
# AI SLOP IN DIGITAL PRODUCT DESIGN
## A Forensic UI/UX Taxonomy, Anti-Pattern Catalog, Detection Framework, and Negative Prompt Specification

**Version:** 1.0  
**Research date:** 3 October 2026  
**Primary use:** Negative prompt / system instruction / design-review specification for AI agents that generate websites, apps, dashboards, landing pages, SaaS products, mobile interfaces, and UI components.

> **Core proposition:** “AI slop” is not a single color, framework, component, font, or trend. It is a *bundle* of statistically safe, over-repeated, weakly justified design decisions that make an interface visually interchangeable, semantically thin, theatrically polished, and insufficiently adapted to the actual product, user, content, brand, or task.

> **Important:** This document intentionally does **not** claim that a single “slop” tell proves AI authorship. Most of the patterns catalogued here were created by human designers before generative AI existed. The relevant signal is *density, repetition, defaulting, context mismatch, and absence of intent*. A well-designed human interface can use a gradient, rounded card, Inter, glass, a bento grid, or a centered hero without becoming “AI slop.”

---

# TABLE OF CONTENTS

1. Research basis and evidence model
2. What “AI slop” means in UI/UX
3. The four-layer model of slop
4. The central distinction: a design system is not slop
5. The AI-slop visual grammar at a glance
6. Master anti-pattern taxonomy
   - 6.1 Art direction and visual authorship
   - 6.2 Color and color behavior
   - 6.3 Typography and type hierarchy
   - 6.4 Layout and composition
   - 6.5 Spacing and rhythm
   - 6.6 Cards, surfaces, borders, radii and elevation
   - 6.7 Navigation and headers
   - 6.8 Hero sections
   - 6.9 Feature sections
   - 6.10 Bento and grid patterns
   - 6.11 Testimonials, logos and trust chrome
   - 6.12 Pricing and monetization surfaces
   - 6.13 Forms, inputs and controls
   - 6.14 Dashboards and data interfaces
   - 6.15 Tables, lists and information density
   - 6.16 Icons and iconography
   - 6.17 Illustration, imagery and 3D decoration
   - 6.18 Motion, animation and transitions
   - 6.19 Microinteractions and state design
   - 6.20 Responsive/mobile behavior
   - 6.21 Accessibility failures that travel with slop
   - 6.22 Copy, labels, microcopy and content structure
   - 6.23 AI self-reference and “AI theater”
   - 6.24 Fake product/UI imagery
   - 6.25 Empty, loading, error and edge states
   - 6.26 Dark patterns and conversion theater
   - 6.27 Code-level and implementation fingerprints
   - 6.28 “Template residue” and generator fingerprints
7. AI-slop archetypes
8. How slop evolves when old tells become unfashionable
9. False positives: when a “sloppy-looking” tell is actually good design
10. Anti-slop generation rules
11. Anti-slop review protocol
12. Before/after examples
13. Negative prompt: full copy-paste specification
14. Compact negative prompt
15. Automated detection heuristics and lint ideas
16. Evaluation matrix
17. Research notes and limitations
18. Sources and further reading

---

# 1. RESEARCH BASIS AND EVIDENCE MODEL

This document is a synthesis rather than a claim that “AI slop” is a formal academic taxonomy. The phrase is comparatively recent, community-defined, and unstable. Current discussions combine several older ideas: template-driven design, visual homogenization, design-system defaults, cargo-culted trends, low-effort content, generated imagery, vibe coding, and manipulative optimization.

The research sweep for this version deliberately mixed:

| Source class | What it contributes | How it is treated |
|---|---|---|
| AI/UI anti-slop repositories and taxonomies | Concrete named visual tells, implementation-level examples, negative rules | High value for operational detection; not treated as peer-reviewed evidence |
| Practitioner articles | Why patterns occur, examples, proposed remedies | Useful for synthesis; claims checked for methodological caveats |
| Reddit | Firsthand reactions, edge cases, disagreement, community vocabulary | Qualitative evidence; not population estimates |
| X / Twitter-indexed material | Current discourse and trend language | Used cautiously; direct UI-specific indexing is sparse, so no invented quotes |
| HCI / research papers | Formal evidence about UI generation, design tools, usability and dark patterns | Highest weight for empirical claims |
| W3C / NN/G | Accessibility and usability constraints | Normative/authoritative guidance for quality gates |
| Code-level repositories | Concrete Tailwind/shadcn/icon/animation fingerprints | Useful for static detection, not authorship attribution |

### 1.1 What the recent practitioner taxonomies agree on

Several independent 2026 anti-slop efforts converge on nearly the same cluster: indigo/violet gradients, Inter/system fonts, centered heroes, triptych feature cards, uniform rounding, diffuse shadows, glassmorphism, sparkle/AI iconography, generic SaaS copy, fake or hollow social proof, repeated micro-animations, and an absence of visual decisions that are specific to the product.

The strongest conceptual convergence is this:

**The problem is not “modern design.” The problem is unchosen modern design.**

A pattern becomes suspicious when the generator uses it because it is the most probable answer to an underspecified prompt rather than because it solves an identified design problem.

### 1.2 A notable 2026 observational study

Precious Studio reports that its “Slop Patterns” library had 235 named patterns as of 23 September 2026. It also describes a hand-audited analysis of 4,725 Show HN launch pages archived from 2016–2026; in its sample, 199 of 425 launch pages from 2026 had at least one of six “AI-era design tells,” while 2 of 310 did in 2016. The authors explicitly state that this dataset describes population-level drift and does not identify who created any individual page. Treat these values as a studio-reported observational analysis, not as an independent peer-reviewed measurement.

### 1.3 Why the word “slop” needs an intent layer

A useful detector must not simply ban:

- gradients,
- rounded corners,
- cards,
- Inter,
- Lucide,
- bento grids,
- dark themes,
- animation,
- glass,
- or centered composition.

Those are legitimate tools. A detector that bans tools rather than context will produce an anti-pattern of its own: **anti-slop slop** — a new template whose only identity is “I am not purple and rounded.”

The robust detector therefore asks:

> **What does this choice communicate, what does it enable, why is it here, and would it still be here if the generator had not seen the canonical template?**

---

# 2. WHAT “AI SLOP” MEANS IN UI/UX

## 2.1 Working definition

For this document:

> **AI slop in UI/UX = an interface whose visible and interaction-level decisions are disproportionately drawn from high-frequency contemporary defaults, are weakly tied to the product’s actual identity or task, and accumulate into an interchangeable or manufactured-looking experience.**

This definition contains five components:

1. **Default concentration** — too many high-frequency defaults are selected together.
2. **Low specificity** — visual and interaction choices could be transplanted to another product with little modification.
3. **Context mismatch** — the visual language does not grow from the domain, content, audience, or task.
4. **Decorative compensation** — gradients, glows, floating cards and animation substitute for content, hierarchy, evidence, or interaction design.
5. **Insufficient refinement** — generated output is treated as the finished design instead of as a first implementation pass.

## 2.2 The strongest high-level signal: interchangeability

Imagine a sequence of unrelated products:

- a pathology lab portal,
- an AI note-taking app,
- a restaurant reservation service,
- a legal case tracker,
- a personal finance dashboard,
- an architectural studio,
- and a school attendance application.

If they all receive:

- the same centered hero,
- the same headline scale,
- the same neutral sans,
- the same violet gradient,
- the same three cards,
- the same glass nav,
- the same rounded buttons,
- the same sparkle icons,
- the same “Powerful / Seamless / Intelligent” copy,
- the same floating product mockup,
- the same testimonial wall,
- the same 3-tier pricing cards,

then the interface language is no longer carrying domain information. It has become a **generic wrapper**.

## 2.3 “Looks expensive” is not the same as designed

A common AI-generation instruction is effectively:

> “Make it premium, modern, sleek, futuristic, professional, and visually stunning.”

These are low-information adjectives. They do not specify:

- what visual tradition is appropriate,
- which content matters most,
- what the brand believes,
- how dense the interface should be,
- what the user is trying to accomplish,
- what should be surprising,
- what should remain boring,
- or what interaction should be memorable.

A model responds by retrieving a statistically safe interpretation of “premium.” That frequently means sparse layouts, neutral grotesques, soft shadows, rounded rectangles, a dark near-black base, an accent gradient, a hero metric, glass surfaces, and polished micro-animation.

The result can be technically competent and aesthetically generic at the same time.

---

# 3. THE FOUR-LAYER MODEL OF SLOP

The most useful way to detect AI slop is to separate the phenomenon into four layers.

## Layer A — Token slop

The page uses familiar tokens without specific justification.

Typical examples:

- Inter because “modern.”
- #7c3aed because “AI.”
- rounded-2xl because “friendly.”
- shadow-lg because “depth.”
- blur-xl because “premium.”

## Layer B — Component slop

The page assembles familiar components in familiar ways.

Examples:

- icon-in-rounded-square + heading + two lines of copy,
- card-in-card,
- hero + two buttons,
- 3-card feature row,
- logo wall,
- 3-tier pricing table,
- testimonial carousel,
- FAQ accordion,
- four-column footer.

## Layer C — Page-template slop

The entire page becomes the canonical sequence:

**Navbar → eyebrow pill → centered hero → CTA pair → logo wall → three-card feature grid → product screenshot/bento → testimonials → stats → pricing → FAQ → CTA → footer.**

Each section can be technically good. The whole still reads as one generic page archetype.

## Layer D — Product-behavior slop

The visual layer may be attractive, but the actual UX remains shallow.

Examples:

- only the happy path exists,
- no empty state,
- no error recovery,
- forms rely on placeholder text,
- destructive actions lack confirmation or undo,
- controls are not keyboard-accessible,
- loading is a decorative spinner rather than informative progress,
- AI features are bolted onto the interface as chat panels,
- generated output is always “Insert / Apply,”
- conversion is optimized through pressure rather than clarity.

**The deeper lesson:** a visually distinctive page can still be slop if it lacks product thinking; a visually conventional page can still be excellent if it is deeply contextual, usable, credible and intentional.

---

# 4. A DESIGN SYSTEM IS NOT SLOP

This is critical.

A coherent design system intentionally repeats rules. Consistency helps users form expectations and transfer knowledge. Nielsen Norman Group explicitly distinguishes internal consistency from external consistency and warns that breaking established conventions without a task-based reason increases cognitive load.

Therefore:

### Good repetition

- the same focus treatment on all form controls,
- the same button semantics everywhere,
- the same spacing tokens within a component family,
- the same color meaning for success/error/warning,
- the same navigation behavior,
- a consistent icon weight,
- a predictable modal system.

### Sloppy repetition

- the same decorative gradient added to every section,
- the same 16px radius on every possible object regardless of size,
- the same card used for content that has different semantic roles,
- the same fade-up animation for every node in the DOM,
- the same “AI” sparkle used for unrelated functionality,
- the same 3-column grid despite content differences,
- the same marketing copy pattern across unrelated products.

**Systematize semantics; vary expression where semantics change.**

---

# 5. THE AI-SLOP VISUAL GRAMMAR AT A GLANCE

| Dimension | Common AI-slop default | Why it becomes a tell | Anti-slop direction |
|---|---|---|---|
| Type | Inter/Roboto/system; one family | Extremely common training-data default | Brand/domain-specific pairing and deliberate type scale |
| Accent | Violet/indigo | High-frequency “modern/AI” cue | Own hue, restrained palette, semantic color system |
| Gradient | Blue → violet / violet → pink | Instant “AI landing page” recognition | Solid surfaces or gradients with communicative purpose |
| Hero | Centered stack | Lowest-risk composition | Content-driven grid, asymmetry, editorial framing where appropriate |
| Feature layout | Exactly 3 equal cards | Canonical SaaS scaffold | Unequal emphasis, sequence, tabs, narrative blocks |
| Radius | rounded-2xl everywhere | Flattens hierarchy | Radius hierarchy or sharp geometry where appropriate |
| Shadow | diffuse soft shadow everywhere | One-click depth cue | Hairlines/layering/tight elevation |
| Glass | blur/transparency on many surfaces | Decorative “premium” without functional reason | Use only when layering requires it |
| Icons | Lucide/emoji/sparkles | Frequently paired with generated feature cards | Function-true icons or custom visual language |
| Copy | “Powerful / seamless / elevate / future” | Semantically empty but grammatically safe | Specific claims, concrete verbs, real evidence |
| Social proof | generic testimonials/logo cloud | Often fabricated or contextless | One real case > six placeholders |
| Motion | fade-up everything | Tutorial residue | Few meaningful transitions; respect reduced motion |
| Background | grid/noise/glow | Decorative filler | Material, brand, image, or structural background |
| Product mockup | fake browser window | Generic hero filler | Real product state, real data, real workflow |
| Pricing | 3 tiers, middle “Most popular” | Template recurrence | Pricing architecture based on actual offer |
| Footer | 4 columns + social circles | Standard SaaS shell | Information architecture based on real navigation |
| Mobile | desktop stack-down | Generated rather than designed | Recompose around touch and priority |
| States | happy path only | static training examples | Explicit loading/empty/error/offline/permission states |
| Accessibility | focus/reduced-motion/semantics forgotten | Visual generation optimizes appearance | Treat accessibility as a first-class design layer |

---

# 6. MASTER ANTI-PATTERN TAXONOMY

The following catalog is intentionally over-complete. A single occurrence is not a verdict. A cluster is the signal.

## 6.1 ART DIRECTION AND VISUAL AUTHORSHIP

### A01 — “The Median Brief”
**Pattern:** The project receives only adjectives (“modern,” “premium,” “clean,” “futuristic”) and the resulting visual language is unconstrained.

**Symptoms:** the page could have been generated for almost any startup.

**Negative rule:** Never infer the complete art direction from generic adjectives alone. Translate the brief into explicit decisions about typography, color, geometry, density, imagery, composition, interaction tone and content hierarchy.

### A02 — “Default Before Domain”
**Pattern:** UI is generated before the domain and user task are translated into visual language.

**Avoid:** designing a restaurant, laboratory, legal workspace and music app with the same visual vocabulary.

### A03 — “Trend Stack”
**Pattern:** multiple current trends are layered simply because they are fashionable: bento + glass + mesh gradient + 3D blob + floating badges + animated counters.

**Why harmful:** every individual trend is asked to signal “modern,” so none carries information.

### A04 — “Decoration Before Meaning”
**Pattern:** decorative styling is added before deciding what each section needs to communicate.

### A05 — “No Negative Space Intent”
**Pattern:** whitespace is uniformly distributed rather than used to create pacing or emphasis.

### A06 — “Design By Component Inventory”
**Pattern:** the agent begins by listing cards, badges, tabs, charts and modals rather than identifying user goals and information hierarchy.

### A07 — “Reference Without Abstraction”
**Pattern:** a reference product is copied literally instead of extracting its underlying principles.

### A08 — “Copy the Competitor, Change the Color”
**Pattern:** layout, interaction and content architecture remain nearly identical while palette and logo are changed.

### A09 — “One Visual Thesis Never Stated”
**Pattern:** no concise statement explains what the interface is trying to feel like or communicate.

### A10 — “Polish as Substitution”
**Pattern:** shadows, gradients, blur and motion make a weak information architecture appear more finished.

---

## 6.2 COLOR AND COLOR BEHAVIOR

### C01 — “House Indigo”
A violet/indigo primary used because AI products “should” be purple.

**Do not ban purple globally.** Ban unexplained purple.

### C02 — “AI Purple → Blue Gradient”
A two- or three-stop gradient moving blue → indigo → violet/pink, especially behind a centered hero.

### C03 — “Gradient Text on AI Words”
Gradient-filled text applied to “AI,” “future,” “intelligence,” “next,” or “workflow.”

### C04 — “Gradient Everywhere”
The same gradient appears in hero background, headline, buttons, borders and chart highlights.

### C05 — “Neon-on-Near-Black AI Theme”
Near-black background + one neon accent + glow + glass cards, without domain justification.

### C06 — “Cream Migration Slop”
After purple becomes overused, the generator shifts to cream/tan background + dark serif headline + terracotta accent while preserving the same generic skeleton.

**Important:** changing the palette is not escaping slop if structure remains the same.

### C07 — “Skittles Status”
Every dashboard status becomes a different saturated pill color.

### C08 — “Everything Is Accent”
Links, headings, borders, icons, badges and charts all compete for accent attention.

### C09 — “Mud Palette”
A visually fashionable palette is chosen from an aesthetically pleasing screenshot but semantic color roles are not assigned.

### C10 — “No Semantic Tokens”
Raw hex/Tailwind utility colors are scattered throughout components without semantic meanings.

### C11 — “Contrast Sacrifice for Mood”
Secondary text is made too faint to preserve a “soft” aesthetic.

### C12 — “Glow as Hierarchy”
Glow intensity becomes the primary method for ranking controls instead of size, placement, label clarity and semantics.

### C13 — “Gradient CTA Glow”
Primary button has gradient fill, blur behind it, bright border and hover glow simultaneously.

### C14 — “Background Blob Filler”
A blurred colorful blob exists only to make an otherwise empty hero look “designed.”

### C15 — “Grid Background Reflex”
Faint dot/grid lines are inserted into hero or dashboard background regardless of product meaning.

### C16 — “Noise Texture Reflex”
Film/noise is added as a generic sophistication filter.

### C17 — “Dark = Black”
Dark mode collapses into #000/#0a0a0a with no material hierarchy.

### C18 — “Light = White”
Light mode is pure #fff with neutral gray and no relationship to brand materials, unless the product genuinely calls for it.

---

## 6.3 TYPOGRAPHY AND TYPE HIERARCHY

### T01 — “Inter Everywhere”
Inter used for display, body, navigation, labels and buttons without a reason.

### T02 — “Roboto/Arial/System Substitute”
A generic system stack is treated as finished art direction rather than a deliberate performance/accessibility choice.

### T03 — “One Typeface, One Personality”
No contrast between display and body text even where the brand calls for it.

### T04 — “Two Weights Only”
Regular + semibold are used for every hierarchy decision.

### T05 — “Everything Bold”
Headlines, cards, labels and buttons all use strong weights; nothing feels truly primary.

### T06 — “Default Tracking”
Display typography uses browser/font-default tracking despite large sizes that benefit from optical tuning.

### T07 — “Micro-Type Everywhere”
Labels, metadata, tags and helper text are shrunk to 9–11px to create density.

### T08 — “One Line Height Fits All”
The same line-height ratio is used for display, body, captions, labels and UI controls.

### T09 — “80–100 Character Measure”
Long reading text spans excessively wide lines because the page is optimized for filling space rather than reading.

### T10 — “Heading Stack Template”
Tiny uppercase eyebrow → huge centered H1 → 18px gray subhead → buttons.

### T11 — “Italics As Fake Personality”
One word in the hero suddenly becomes italic serif purely to create visual novelty.

### T12 — “Random Serif Accent”
A single serif word is inserted into an otherwise neutral interface without a typographic system.

### T13 — “CAPS Eyebrow Inflation”
Every section heading gets a tiny uppercase label with wide tracking.

### T14 — “01 / 02 / 03 Decoration”
Numerical section markers appear even where the content is not sequential.

### T15 — “Semantic Flatness Through Type”
Headings, labels, card names and metadata all have nearly identical visual weight.

### T16 — “Placeholder Copy Drives Type”
Generic filler forces headings to be awkwardly long or artificially balanced.

---

## 6.4 LAYOUT AND COMPOSITION

### L01 — “Dead Center”
Hero, headings, body copy, buttons, cards and metrics all centered.

### L02 — “Triptych by Reflex”
Exactly three equal cards regardless of the content.

### L03 — “Two-Column SaaS Hero”
Text left + fake product card right, repeated across unrelated products.

### L04 — “Split-Screen Premium Template”
Left text / right image, often with a floating badge pinned to the visual.

### L05 — “Everything Same Width”
All content blocks share identical width instead of adapting to reading, interaction, and media needs.

### L06 — “Everything Same Alignment”
No deliberate alignment shifts; all components sit on one obvious vertical axis.

### L07 — “Symmetry Without Information”
Perfectly mirrored compositions whose only function is visual neatness.

### L08 — “Bento Because Bento”
Bento layout is used even when content does not have heterogeneous importance or media types.

### L09 — “Bento Tile Inflation”
Every tile has rounded corners, gradient border, tiny icon, tiny title, tiny paragraph, and a decorative graphic.

### L10 — “Card Soup”
Everything becomes a card: settings, paragraphs, FAQs, charts, alerts, navigation, features, pricing and simple text blocks.

### L11 — “Nested Box Syndrome”
Card inside card inside card to represent hierarchy that should have been expressed through spacing and separators.

### L12 — “Floating UI Soup”
Multiple disconnected panels hover over the background without actual overlap semantics.

### L13 — “Hero Above the Fold, Nothing Else”
The hero consumes enormous vertical space while real product evidence begins far below.

### L14 — “Scroll Length Padding”
Pages are made long by repeating large headings and oversized empty sections.

### L15 — “Section = Template Instance”
Every section has the same title structure, same max-width, same top padding and same component pattern.

### L16 — “Perfectly Even Columns”
Unequal information is forced into equal-width cards.

### L17 — “No Dominant Moment”
Every component is visually medium-weight; the page has no clear focal point.

### L18 — “Everything Is Hero”
Multiple components compete with oversized headings, glows and big metrics.

### L19 — “One-Screenshot Thinking”
Composition looks attractive as a screenshot but breaks under real data, long labels, localization, and dynamic states.

### L20 — “Container Prison”
The same max-width container is applied to all content types, including data tables, images, long text, and edge-to-edge visual sections.

---

## 6.5 SPACING AND RHYTHM

### S01 — “24px Everywhere”
The same padding is used inside cards, sections, dialogs and toolbars.

### S02 — “Metronome Sections”
Every section has identical top/bottom spacing.

### S03 — “Gap-4 Monoculture”
Utility classes are repeated everywhere even when relationships differ.

### S04 — “Airy = Premium”
Generous whitespace is inserted mechanically instead of according to hierarchy.

### S05 — “Compressed Importance”
Critical information gets the same spacing as metadata.

### S06 — “No Compression”
Dense task interfaces are artificially spaced like marketing pages.

### S07 — “No Rhythm Change”
The page never accelerates or slows down visually.

### S08 — “Padding Instead of Design”
A component feels empty, so padding is increased instead of improving content hierarchy.

### S09 — “Uniform Mobile Collapse”
Desktop gaps are simply reduced proportionally rather than rethinking content order.

---

## 6.6 CARDS, SURFACES, BORDERS, RADII AND ELEVATION

### R01 — “Rounded-2xl Everything”
Buttons, cards, inputs, avatars, images, dialogs and page shells all use the same large radius.

### R02 — “One Radius to Rule Them All”
No relationship between object size, semantic role and corner geometry.

### R03 — “Shadow-lg, Shipped”
Generic diffuse shadows are assigned to every card.

### R04 — “Ghost Card”
Hairline border + diffuse shadow + low-opacity fill all compete on one surface.

### R05 — “Frosted Everything”
Backdrop blur appears on nav, cards, modals, tooltips and random feature surfaces.

### R06 — “Glass Without Layering”
Glass effect exists even when there is no background visual that benefits from depth or translucency.

### R07 — “Gradient Border Card”
Card border becomes a multicolor gradient because a normal border feels too plain.

### R08 — “Glow Border on Hover”
Any card hover causes border color + shadow + glow + vertical lift.

### R09 — “Card-In-Card Chrome”
One framed panel contains another framed panel for no semantic reason.

### R10 — “Colored Left Stripe”
Decorative 3–4px accent stripe appears on ordinary cards without semantic meaning.

### R11 — “Pill Inflation”
Status, category, user role, AI capability, and navigation all become pills.

### R12 — “Everything Has a Border”
Visual hierarchy is expressed through repeated 1px outlines rather than grouping and spacing.

### R13 — “Everything Has a Shadow”
Depth loses meaning because all elements float equally.

### R14 — “Inset Shadow Reflex”
Inputs or cards receive inner shadow solely to look “premium.”

### R15 — “Surface Inversion Pattern”
Alternating sections are created only by swapping card/surface tones, not by content purpose.

---

## 6.7 NAVIGATION AND HEADERS

### N01 — “Glass Navbar”
Sticky translucent nav with blur, low-opacity border, centered logo, pill CTA.

### N02 — “Pill Nav”
Primary navigation items are enclosed in pills even when they are ordinary links.

### N03 — “Floating Nav Shell”
Nav looks detached from page content without providing a meaningful reason.

### N04 — “Logo + Center Links + Right CTA”
The same three-zone navigation structure is used regardless of information architecture.

### N05 — “Tiny Header + Oversized Hero”
Header receives minimal design thought while hero receives all visual complexity.

### N06 — “Hamburger Everywhere”
Desktop navigation is unnecessarily hidden behind a mobile-style menu because it is visually convenient.

### N07 — “Social Icon Orbit”
Header or footer contains circular social icons simply because “every site should.”

### N08 — “Header CTA Doppelgänger”
The primary CTA appears in nav, hero, every section, footer and sticky mobile bar with no context-specific reason.

---

## 6.8 HERO SECTIONS

### H01 — “Eyebrow → Giant H1 → Gray Subhead → CTA Pair”
The canonical startup hero skeleton.

### H02 — “Now in Beta Pill”
A pill with pulsing dot is inserted above the headline even when no beta stage exists.

### H03 — “Gradient AI Headline”
One or more hero words are gradient-colored.

### H04 — “Hero Orb”
An iridescent 3D blob floats behind the copy.

### H05 — “Blurred Blob”
Background contains one or more huge blurred accent circles.

### H06 — “Fake Dashboard Hero”
CSS-drawn fake UI is used as a product illustration instead of showing a real workflow.

### H07 — “Mac Window Prop”
Traffic-light dots + rounded dark window + fake dashboard appear in a product hero.

### H08 — “Code Window Prop”
Terminal/code mockup appears even when product is not developer-facing.

### H09 — “Floating Badge Cluster”
Three or more tiny labels float around hero visual to fill negative space.

### H10 — “Hero Metric Theatre”
Huge metrics appear before users understand what the metric represents.

### H11 — “Two CTA Reflex”
Primary + ghost secondary button are generated without evidence that both actions matter.

### H12 — “Arrow-Right CTA”
A trailing arrow icon is added to generic button copy by reflex.

---

## 6.9 FEATURE SECTIONS

### F01 — “Three Identical Features”
The canonical triptych.

### F02 — “Icon in Colored Tile”
Every feature begins with a rounded square containing an icon.

### F03 — “Feature Card Paragraph Length = 2 Sentences”
Every card uses nearly identical copy length.

### F04 — “Feature Icon Semantic Mismatch”
Shield = security, sparkles = AI, Zap = speed, chart = analytics, regardless of brand or nuanced meaning.

### F05 — “Six Cards Because Features Section”
Two rows of three are created simply because “six features” feels complete.

### F06 — “Feature Redundancy”
Different cards restate the same broad benefit with different verbs.

### F07 — “Feature Section Without Evidence”
The interface claims capability but shows no actual interaction, result, data, constraint or user outcome.

---

## 6.10 BENTO AND GRID PATTERNS

### B01 — “Bento as Default Novelty”
Bento appears because three-card grids are known tells, creating a new tell.

### B02 — “Every Tile Is a Mini Hero”
Huge headings, gradient borders, decorative media and badges compete inside every cell.

### B03 — “Equal Information in Unequal Tiles”
Bento geometry contradicts the actual content hierarchy.

### B04 — “Bento with No Real Media”
Cells contain tiny abstract icons instead of meaningful content.

### B05 — “Pseudo-Asymmetry”
The layout looks asymmetric mathematically but remains visually predictable: one large card + four identical small cards.

### B06 — “Bento + Glow + Glass Triple Stack”
A common over-finished combination with little semantic meaning.

---

## 6.11 TESTIMONIALS, LOGOS AND TRUST CHROME

### P01 — “Fake Testimonial Wall”
Three or six generic one-sentence testimonials with broad praise and no specific outcome.

### P02 — “Generated Name + Avatar”
A plausible first/last name plus generic portrait is used as evidence.

### P03 — “Fake Company”
Testimonials use company names that cannot be substantiated.

### P04 — “Logo Cloud”
A row of grayscale logos appears under “Trusted by” without clear customer relationship.

### P05 — “Logo Marquee”
The logo wall scrolls continuously to imply abundance.

### P06 — “Logo Ipsum”
Placeholder geometric marks are presented as social proof.

### P07 — “Five-Star Reflex”
Stars appear beside generic quotes even where no review platform exists.

### P08 — “Invented Statistics”
“10K+ users,” “99.9% uptime,” “50M workflows,” etc. appear without verified basis.

### P09 — “Fake Compliance Badges”
SOC2, HIPAA, ISO, GDPR or partner badges appear without actual evidence.

### P10 — “Trust Without Verification Path”
Claims cannot be clicked, explained or contextualized.

### P11 — “Case Study Without Case”
A quote names a company but provides no method, baseline, result or evidence.

### P12 — “Social Proof Before Product Proof”
The page spends more space on reputation than on explaining what the product actually does.

---

## 6.12 PRICING AND MONETIZATION SURFACES

### PR01 — “Three-Tier Law”
Free / Pro / Enterprise with middle plan highlighted whether or not it matches business reality.

### PR02 — “Most Popular Gradient Pill”
The center tier receives a glowing gradient border and “MOST POPULAR” badge.

### PR03 — “Monthly / Annual Toggle Reflex”
Billing toggle is inserted without explaining annual savings or billing terms.

### PR04 — “Enterprise = Contact Us”
Enterprise tier is generic because no actual enterprise packaging has been designed.

### PR05 — “Feature Checklist Soup”
Every plan is a long list of nearly identical checks.

### PR06 — “Fake Savings”
Price comparison uses invented anchors, fake original prices or unclear discounts.

### PR07 — “Pricing Decoration Over Clarity”
Glow, scale and color make the selected plan look important but obscure actual cost differences.

### PR08 — “CTA at Every Tier”
Every card uses the same “Get started” button even where the correct next action differs.

---

## 6.13 FORMS, INPUTS AND CONTROLS

### FO01 — “Placeholder as Label”
Input labels exist only as placeholder text.

### FO02 — “One Rounded Field Style”
All controls share identical radius, fill, border, and height regardless of semantic role.

### FO03 — “No Focus Design”
Focus outline is removed and no accessible replacement exists.

### FO04 — “No Error State Design”
The model designs only pristine form states.

### FO05 — “Validation After Submission Only”
Users receive no useful inline feedback for clearly invalid fields.

### FO06 — “Generic Selects”
Custom dropdowns are built for stylistic consistency when native controls would be more robust.

### FO07 — “Icon-Only Ambiguity”
Controls use unlabeled icons for destructive or consequential actions.

### FO08 — “Ghost Controls”
Interactive boundaries are too subtle to distinguish from static content.

### FO09 — “Loading Without Preservation”
Submitting a form removes context instead of showing progress in place.

### FO10 — “Success Theater”
A green checkmark animation appears without explaining what changed or what the user should do next.

---

## 6.14 DASHBOARDS AND DATA INTERFACES

### D01 — “Dashboard Card Grid”
Every metric, chart, and action lives in a floating card.

### D02 — “Four KPI Cards First”
Revenue / users / growth / uptime appear above task-relevant information by template.

### D03 — “Decorative Sparklines”
Tiny charts exist to make a card feel analytical but do not support a decision.

### D04 — “Chart Soup”
Multiple chart types are included simply to show richness.

### D05 — “Donut Chart Reflex”
A donut/pie chart is used when a table, bar or single number would communicate faster.

### D06 — “Animated Counter Reflex”
Numbers count upward whenever they enter the viewport.

### D07 — “Color-Coded Everything”
Every category receives a saturated unique color.

### D08 — “Filters as Decoration”
Date/status/segment filters exist but do not measurably affect visible content.

### D09 — “Data Without Units”
Numbers are shown without currency, time range, denominator or context.

### D10 — “No Density Adaptation”
A dense operational dashboard is spaced like a marketing landing page.

### D11 — “Fake Live Data”
Interface shows simulated activity, “online” counts or live graphs that are not actually live.

### D12 — “Dashboard Screenshot Theatre”
Marketing page embeds fake dashboard images instead of real product states.

---

## 6.15 TABLES, LISTS AND INFORMATION DENSITY

### TB01 — “Cardified Table”
A table is transformed into dozens of cards because the generator prefers cards.

### TB02 — “Pill Status Every Row”
Status becomes a colorful badge in every row even when plain text would be clearer.

### TB03 — “Icon Before Every Label”
Icons are added to every list item, creating visual noise.

### TB04 — “No Column Prioritization”
All data receives equal width and emphasis.

### TB05 — “No Empty Table State”
An empty dataset shows a blank panel or generic “No data” text.

### TB06 — “Infinite Scroll Reflex”
Pagination is replaced with endless loading without a content-scale reason.

### TB07 — “Fake Activity Feed”
Recent activity is inserted to make the dashboard look alive.

---

## 6.16 ICONS AND ICONOGRAPHY

### I01 — “Lucide Five”
Sparkles, Zap, Shield, Check, ArrowRight are repeatedly selected across unrelated products.

### I02 — “Sparkle Tax”
Every AI feature gets Sparkles/Wand/Bot/Brain/Cpu imagery.

### I03 — “Emoji Reflex”
Emoji are used as feature icons in professional interfaces without domain justification.

### I04 — “Icon in Rounded Square”
Icon sits inside a colored rounded tile because the template expects a visual anchor.

### I05 — “Icon Mismatch”
The visual metaphor is only vaguely related to the action.

### I06 — “Icon Weight Drift”
Mixed icon libraries or stroke weights create an unrefined system.

### I07 — “Arrow Everywhere”
Every CTA ends with an arrow despite no directional meaning.

### I08 — “Circular Icon Button Soup”
Many controls become circles simply because the generator knows how to style an icon button.

### I09 — “Decorative Icons in Headings”
Icons are appended to headings where they add no information.

---

## 6.17 ILLUSTRATION, IMAGERY AND 3D DECORATION

### IM01 — “Iridescent Blob”
3D soft-body object with rainbow reflections in hero.

### IM02 — “Spline/Abstract 3D Prop”
A floating generic 3D object is used without connection to product mechanics.

### IM03 — “Corporate Memphis Echo”
Flat pastel characters performing generic “collaboration” or “productivity” actions.

### IM04 — “Generic Diverse Team Photo”
Stock image of people around a laptop in a bright office.

### IM05 — “Laptop Dashboard Stock Photo”
Stock photograph includes a screen displaying generic analytics UI.

### IM06 — “Generated Founder Portrait”
Photorealistic but contextless headshot used as testimonial evidence.

### IM07 — “Plastic Product Render”
Everything is smooth, reflective and physically perfect regardless of product category.

### IM08 — “3D Everywhere”
3D hero art, 3D icons, 3D illustrations, 3D product mockups and 3D badges coexist without a visual system.

### IM09 — “AI Image Placeholder”
Generated imagery is used to fill space rather than convey product information.

### IM10 — “Fake Screenshot”
A beautiful product screenshot is actually a static mockup that does not match the real product.

---

## 6.18 MOTION, ANIMATION AND TRANSITIONS

### M01 — “Fade-Up Everything”
Every section enters with opacity + upward movement.

### M02 — “100ms Stagger Ritual”
Every child receives a uniform stagger.

### M03 — “Hover Lift Everything”
All cards translate up on hover.

### M04 — “Shadow Bloom Hover”
Card rises + shadow grows + border brightens + accent glow appears.

### M05 — “Constant Marquee”
Logos or testimonials move forever without informational need.

### M06 — “Parallax for Prestige”
Background moves at a different speed purely to signal sophistication.

### M07 — “Scroll-Jacked Storytelling”
Scrolling is overridden so the user is forced through an animation sequence.

### M08 — “Elastic Everything”
Springs/bounces are applied to ordinary controls.

### M09 — “Animation Without Hierarchy”
A button, footer, hero text and secondary card all have similar animation intensity.

### M10 — “Invisible Content Trap”
Important content is hidden until an entrance animation triggers.

### M11 — “Animation Without Reduced Motion”
Non-essential animation ignores `prefers-reduced-motion`.

### M12 — “Janky Layout Animation”
Width/height/top/left changes cause visible layout movement or poor performance.

### M13 — “Loading Shimmer for Everything”
Shimmer animation is applied even when skeleton loading is not useful.

### M14 — “Shimmer as Decoration”
Shimmer appears on static content or as a “new/AI” effect unrelated to loading.

### M15 — “Cursor Theatre”
Custom cursor effects, magnetic buttons and cursor trails exist without improving interaction.

---

## 6.19 MICROINTERACTIONS AND STATE DESIGN

A mature interface has designed states. A shallow generated interface usually has designed screenshots.

### State set to require for interactive elements

At minimum, consider:

1. default
2. hover
3. focus-visible
4. active/pressed
5. disabled
6. loading
7. success
8. error
9. empty/not-available where applicable
10. permission/restricted where applicable
11. offline/syncing where applicable

### MS01 — “Screenshot State Only”
Only default state has been designed.

### MS02 — “Hover Does Everything”
The UI uses hover to compensate for missing hierarchy.

### MS03 — “No Pressed State”
Button appears decorative because click feedback is absent.

### MS04 — “No Disabled Semantics”
Disabled controls visually resemble active controls or simply vanish.

### MS05 — “Generic Green Success”
Any successful operation ends in a decorative check animation without useful confirmation.

### MS06 — “Generic Red Error”
An error is represented only by red text or an icon, with no recovery action.

### MS07 — “Toast as Trash Bin”
Important information is dumped into temporary toasts.

### MS08 — “Modal for Everything”
A modal is used for tasks that could be completed inline.

### MS09 — “Drawer for Everything”
Every secondary task becomes a slide-over panel.

### MS10 — “Preview → Insert Ceremony”
AI-generated content appears in a preview card and requires an “Insert/Apply” step even when direct application + undo would be more coherent.

---

## 6.20 RESPONSIVE / MOBILE BEHAVIOR

### MOB01 — “Desktop Stack-Down”
Desktop layout is simply stacked vertically.

### MOB02 — “Hero Still Huge”
The desktop hero remains oversized on small screens, pushing task content below the fold.

### MOB03 — “Horizontal Overflow”
Cards, tabs, tables or buttons overflow because the generator did not test realistic widths.

### MOB04 — “Tiny Touch Targets”
Icon buttons shrink to visual ornament size.

### MOB05 — “Desktop Navigation Collapse”
The header becomes a hamburger without reconsidering navigation priority.

### MOB06 — “Button Row Wrap”
Primary/secondary actions wrap awkwardly instead of becoming a clear vertical hierarchy.

### MOB07 — “Bento Collapse to Card Soup”
Interesting desktop composition becomes a long list of identical cards on mobile.

### MOB08 — “Text Before Task”
Marketing copy remains above the actual mobile task even when task-first ordering is more appropriate.

### MOB09 — “Sticky Bottom CTA Reflex”
A persistent bottom bar appears solely to keep a CTA visible, sometimes occluding content.

### MOB10 — “No Thumb Reach Consideration”
Important actions are placed in hard-to-reach or visually inconvenient regions on mobile.

---

## 6.21 ACCESSIBILITY FAILURES THAT TRAVEL WITH SLOP

These are not definitions of AI slop, but they are common co-failures and must be prevented.

### AX01 — “focus:outline-none” Without Replacement
Keyboard focus is removed for aesthetics.

### AX02 — Low Contrast Secondary Text
Soft gray on light gray is used to make interfaces feel calm.

### AX03 — Color-Only Status
Green/red/amber communicate state without a textual or shape cue.

### AX04 — Missing Reduced Motion
Decorative animation is not suppressed for users who prefer reduced motion.

### AX05 — Tiny Targets
Important pointer targets are smaller than practical touch sizes or fail WCAG requirements.

### AX06 — Hover-Only Information
Information or controls appear only on hover with no equivalent keyboard/touch path.

### AX07 — Missing Labels
Forms rely on placeholder text.

### AX08 — Heading Level Skips
Heading hierarchy is chosen by size rather than semantic structure.

### AX09 — Div Soup
Semantics are discarded for styling convenience.

### AX10 — Custom Control Without Keyboard Path
A visually polished custom dropdown, slider, combobox or tab system is functionally incomplete.

### AX11 — Focus Obscured by Sticky UI
Sticky headers/bottom bars cover the element receiving focus.

### AX12 — Animation Triggers Motion Discomfort
Non-essential parallax, zoom, movement or scroll effects are mandatory.

W3C WCAG 2.2 includes requirements around contrast, focus visibility, focus not being obscured, target size, and animation triggered by interaction. Treat accessibility as a design constraint, not a post-processing step.

---

## 6.22 COPY, LABELS, MICROCOPY AND CONTENT STRUCTURE

### K01 — “Build the Future of X”
A broad aspirational headline that could belong to any startup.

### K02 — “Powerful / Seamless / Intelligent”
Adjectives stand in for product evidence.

### K03 — “Elevate Your Workflow”
Verb + abstract business noun construction.

### K04 — “Unlock / Transform / Empower”
Generic verbs that provide little product information.

### K05 — “AI-Powered” as Content
The interface describes itself as AI-powered instead of describing its user outcome.

### K06 — “Revolutionize”
Grandiose language without a concrete claim.

### K07 — “All-in-One”
Feature breadth is asserted without explaining how workflows connect.

### K08 — “Seamless”
The experience is called seamless instead of showing the actual interaction.

### K09 — “Trusted by Leading Teams”
Anonymous trust language that avoids evidence.

### K10 — “Quietly Trusted By”
Hedged prestige language designed to make an empty logo row sound credible.

### K11 — “Join Thousands”
Unverifiable social proof.

### K12 — “99.9% Uptime”
A highly specific number with no source or operational context.

### K13 — “Get Started” Everywhere
The same CTA appears regardless of the next action.

### K14 — “Learn More” Everywhere
A generic CTA provides no clue what content follows.

### K15 — “See How It Works” Without a Demonstration
CTA promises explanation but leads to another marketing section.

### K16 — “Punctuation Template”
Repeated em-dash prose, title case, short polished paragraphs and slogan-like section titles create formulaic rhythm.

### K17 — “Poetic Section Labels”
“Built for momentum,” “Designed for clarity,” “Made for what’s next” appear as interchangeable headings.

### K18 — “Copy Length Matching”
Each card has nearly identical word count despite different content.

### K19 — “Marketing Copy in Product UI”
A dashboard button says “Unlock your productivity potential” instead of “Export CSV.”

### K20 — “No Domain Vocabulary”
A medical system, compiler, warehouse system, and design tool all speak the same generic SaaS language.

---

## 6.23 AI SELF-REFERENCE AND “AI THEATER”

### AI01 — Sparkles Everywhere
Any AI-adjacent capability receives a sparkle.

### AI02 — “Powered by GPT” as Primary Label
The model/vendor becomes the feature identity.

### AI03 — AI Badge Inflation
“AI,” “AI-powered,” “Smart,” “Magic,” “Copilot,” “Assistant” tags are attached to ordinary automation.

### AI04 — Chatbot Bolted Onto a Task UI
Instead of designing direct controls, the product adds a chat panel for everything.

### AI05 — Generate → Preview → Insert
A generic two-step or three-step AI action appears regardless of task.

### AI06 — Prompt Box as Universal Interface
The user is forced to express a structured task through natural-language prompting when direct controls would be faster.

### AI07 — Model Name as UX
GPT-4, Claude, Gemini or vendor branding is shown where the user actually needs to understand the function.

### AI08 — “Thinking” Theater
Long animated AI states imply intelligence without providing meaningful progress information.

### AI09 — Fake Agent Activity
Spinners, cursor movement, terminal text and simulated status messages suggest complex work that is not actually happening.

### AI10 — AI Suggestion Flood
Every screen offers suggestions, prompts, generated chips and “magic” actions.

### AI11 — AI Capability as Visual Decoration
Sparkles, gradients and glows communicate “AI” more strongly than the actual feature behavior.

---

## 6.24 FAKE PRODUCT/UI IMAGERY

### FI01 — CSS Screenshot of a Product That Does Not Exist
A marketing page renders a fake dashboard in HTML solely for visual effect.

### FI02 — Browser Chrome Prop
Fake URL bar, traffic lights and window controls create “real software” theater.

### FI03 — Fake Terminal
Terminal appears because developer aesthetics look technical.

### FI04 — Fake Chart
Marketing chart numbers do not correspond to actual product functionality.

### FI05 — Fake User Data
Avatars, names, messages, notifications and metrics are invented but presented as if they were real product evidence.

### FI06 — Screenshot Mismatch
Marketing screenshot uses a visual language or feature set not present in the shipped product.

### FI07 — Placeholder That Ships
Logoipsum, DiceBear, lorem ipsum, generic avatars or “John Doe” remain in production.

---

## 6.25 EMPTY, LOADING, ERROR AND EDGE STATES

A strong anti-slop specification should explicitly force agents to design the “boring” states that a screenshot-driven generator overlooks.

### E01 — Blank Empty State
No guidance, explanation or next action.

### E02 — Generic Empty Copy
“No data yet.”

### E03 — Empty State Illustration Without Action
Large decorative illustration but no clear recovery or creation path.

### E04 — Spinner-Only Loading
No content structure or progress information.

### E05 — Skeleton Overuse
Entire application is gray blocks even where immediate content could simply be displayed.

### E06 — Error as Toast
Critical failure is communicated only by a transient toast.

### E07 — Error Without Recovery
“Something went wrong” with no retry, correction, fallback or support path.

### E08 — Offline Ignored
Application behaves as if network access is guaranteed.

### E09 — Permission State Ignored
Users encounter blank panels rather than a clear explanation of access requirements.

### E10 — Long Content Ignored
No behavior for overflow, truncation, wrapping or unusually large user input.

### E11 — Long Names Break Layout
Cards assume short Western names and fixed-length labels.

### E12 — Localization Blindness
UI depends on fixed-width English strings, pun-based headings, or visual word length.

### E13 — Data Extremes Ignored
Very high/low values break charts, badges or progress bars.

### E14 — Zero / One / Many Not Considered
An interface assumes every collection has multiple items.

---

## 6.26 DARK PATTERNS AND CONVERSION THEATER

AI slop can be aesthetically beautiful and still be poor UX because generated systems may reproduce persuasive patterns without understanding their ethical or task implications.

### DP01 — Fake Scarcity
“Only 2 spots left” without factual basis.

### DP02 — Countdown Without Real Deadline
Timer creates pressure but does not represent an actual cutoff.

### DP03 — Preselected Add-On
Optional purchase is selected by default.

### DP04 — Hidden Cost
Important fees appear only late in the flow.

### DP05 — Confirm-Shaming
The “no” option is emotionally framed.

### DP06 — Asymmetric Buttons
The desired commercial action is visually dominant while the alternative is minimized beyond normal hierarchy.

### DP07 — Forced Signup
The interface blocks access to useful content without a genuine product reason.

### DP08 — Infinite Cancellation
User must fight through irrelevant questions or repeated confirmations to cancel.

### DP09 — Misleading Language
Button wording does not accurately describe the result.

### DP10 — Sneaking
Important terms are visually buried in low-contrast text or secondary panels.

### DP11 — Brand Bias
The system favors its own service in comparative or choice interfaces without task justification.

### DP12 — Manipulative AI Assistant
The conversational assistant nudges users beyond their stated task rather than supporting informed choice.

Research such as DarkBench shows that LLMs can reproduce manipulative design behaviors under adversarial prompting. The anti-slop prompt must therefore explicitly reject dark patterns instead of assuming visual polish implies ethical design.

---

## 6.27 CODE-LEVEL AND IMPLEMENTATION FINGERPRINTS

These are useful to an automated detector, but they are not proof of authorship.

### CODE01 — Verbatim Gradient Utility Stacks
Examples such as blue→purple Tailwind gradients.

### CODE02 — `rounded-2xl shadow-lg p-6` Everywhere
A frequently observed generated combination.

### CODE03 — Raw Utility Color Scatter
No semantic tokens; colors are embedded directly in utility classes.

### CODE04 — `dark:` Prefix Explosion
Every element has separate dark-mode overrides rather than shared tokens.

### CODE05 — Uniform `gap-4` / `p-6`
Spacing is mechanically repeated rather than semantically varied.

### CODE06 — Framer Motion Entrance Boilerplate
Every component receives the same opacity/y transform animation.

### CODE07 — Inline Animation
Animation is embedded in one-off inline styles, making consistency and reduced-motion support harder.

### CODE08 — Shadcn Defaults Untouched
The library itself is not the problem; unmodified defaults across the entire interface are the signal.

### CODE09 — Icon Library + Semantic Repetition
Same library and same handful of icons used across unrelated features.

### CODE10 — Generated Placeholder Components
Components contain static sample data rather than real state/data binding.

### CODE11 — Accessibility Omissions
Missing labels, alt text, focus states, keyboard support and semantics are common co-signals.

### CODE12 — Happy-Path Event Handlers
Handlers only account for successful API response.

### CODE13 — Excessive `!important`
Late-stage AI patching creates CSS specificity battles instead of coherent tokens.

### CODE14 — Z-Index Escalation
Arbitrary z-index values appear because the layering model was not designed.

### CODE15 — Magic-Number Accumulation
One-off pixel values proliferate instead of using a coherent spacing/typography system.

### CODE16 — Duplicate Styling Systems
Tailwind utilities + component CSS + inline styles all define the same visual property.

---

## 6.28 TEMPLATE RESIDUE AND GENERATOR FINGERPRINTS

### TR01 — Generator Attribution Left in UI
“Built with Lovable,” “Built with v0,” etc. remains in shipped interface.

### TR02 — Default Favicon
Starter favicon remains.

### TR03 — Default Metadata / Open Graph
Title/description still describes template rather than actual product.

### TR04 — Demo Navigation
Links point to sections that no longer exist.

### TR05 — Fake Settings
UI exposes controls that do not affect the application.

### TR06 — Dead Buttons
Buttons look active but perform no meaningful action.

### TR07 — Placeholder Link Targets
Every link points to `/`, `#`, or an unimplemented route.

### TR08 — Template Footer Copy
Generic “we are a team of passionate developers building the future” paragraph.

### TR09 — Repeated CTA in Every Section
The generator inserts an identical CTA after each section.

### TR10 — FAQ Written to Fill Space
Questions are generic and answers repeat the marketing copy.

### TR11 — Section Exists Because the Template Has One
A section remains despite having no useful content.

### TR12 — Design Token Drift
A last-minute AI edit introduces a slightly different radius, shadow, font size, or accent color without updating the system.

---

# 7. AI-SLOP ARCHETYPES

These archetypes describe whole-system combinations. They are more useful than single-tell bans.

## Archetype 1 — “Violet SaaS Default”

**Formula:**

`Inter + violet/indigo + centered hero + gradient + 3 cards + glass + rounded-2xl + shadow-lg + Sparkles + “Get Started”`

**Strongest detection signal:** the bundle, not any single element.

## Archetype 2 — “Dark AI Lab”

**Formula:**

`#0a0a0a + neon accent + glow + glass panels + grid background + terminal text + 3D blob + animated metrics`

**Typical mismatch:** used for products with no technical/experimental visual identity.

## Archetype 3 — “Cream Anti-Slop Clone”

**Formula:**

`warm cream + editorial serif + terracotta/olive + asymmetric hero + thin lines + tiny uppercase labels + huge italic word`

**Failure:** the generator has learned a newer anti-slop aesthetic and reproduces it mechanically.

## Archetype 4 — “Bento Maximalist”

**Formula:**

`dark background + 6–10 rounded tiles + gradient borders + small icons + little stats + one large central tile + every tile animated`

## Archetype 5 — “Fake Editorial”

**Formula:**

`serif hero + dramatic crop + 01/02/03 labels + giant quotes + tiny captions + thin rules + asymmetry`

**Failure:** the typography and composition are decorative but the product/content does not actually behave like editorial material.

## Archetype 6 — “Dashboard Wallpaper”

**Formula:**

`KPI cards + chart cards + colored badges + tiny sparkline charts + animated counters + sidebar + topbar + fake live activity`

## Archetype 7 — “Portfolio Theater”

**Formula:**

`giant name + oversized claim + skill cards + gradient + project cards + fake client logos + animated cursor + contact CTA`

**Better:** real work, case studies, constraints, process and outcomes.

## Archetype 8 — “AI Assistant Everything”

**Formula:**

`chat panel + sparkle icon + prompt chips + “Generate” + preview card + Insert + model badge`

**Failure:** a direct manipulation interface has been converted into a chat because chat is easy for a language model to generate.

---

# 8. HOW SLOP EVOLVES WHEN OLD TELLS BECOME UNFASHIONABLE

AI-generated aesthetics are adaptive. Once the population notices a tell, prompts and tools stop using it as aggressively. A useful negative prompt therefore must target **mechanisms**, not a frozen snapshot.

## 8.1 First-generation tell

Purple gradient + Inter + three cards.

## 8.2 Second-generation tell

Cream background + serif headline + asymmetry + editorial labels.

## 8.3 Third-generation tell

Bento + monospace metadata + custom variable font + “intentional” hairlines.

## 8.4 Fourth-generation tell

The model now obeys anti-slop rules superficially while still making generic decisions underneath.

Example:

> “Do not use purple. Use burnt orange.”

Then:

- same centered hero,
- same 3 cards,
- same testimonial wall,
- same pricing structure,
- same generic copy,
- same animation,
- same fake dashboard.

This is **palette laundering**. It removes one visible tell while preserving the generator’s underlying template.

## 8.5 The durable principle

Do not instruct the model merely:

> “avoid purple.”

Instruct:

> “Do not choose any visual treatment merely because it is a current AI-design convention. Every major visual dimension must be tied to domain, audience, content, or task. Document the reason before implementation.”

---

# 9. FALSE POSITIVES: WHEN A “SLOPPY-LOOKING” TELL IS ACTUALLY GOOD DESIGN

This section is mandatory for any serious detector.

## 9.1 Rounded corners

Rounded corners may improve perceived softness, touch affordance, and brand fit. The slop signal is indiscriminate reuse, not roundedness.

## 9.2 Inter

Inter is highly legible and widely supported. It may be an excellent deliberate choice for data-heavy products. The tell is choosing it without considering brand voice and then using one scale/weight everywhere.

## 9.3 Purple

A company may genuinely own purple as its brand color. Ban unexplained purple, not purple itself.

## 9.4 Bento

Bento is appropriate when content is naturally heterogeneous and some items deserve larger visual territory.

## 9.5 Glass

Glass can solve layering over imagery or communicate depth in a purposeful visual system. Decorative glass on every card is the problem.

## 9.6 Centered hero

Centered composition is appropriate for short focal messages, campaigns, announcements and some consumer experiences.

## 9.7 Three cards

Three is a useful number. The question is whether the content actually comes in three coherent units.

## 9.8 Animation

Animation can communicate causality, continuity and state. The anti-slop rule is meaningful motion, not “zero motion.”

## 9.9 Design-system consistency

Consistency is good. A detector should never penalize semantic reuse simply because something repeats.

## 9.10 Minimalism

A sparse page is not automatically slop. Minimalism becomes slop when “empty” is used to simulate premium quality while failing to provide useful content or hierarchy.

## 9.11 Brutalism / neobrutalism

A deliberately raw aesthetic may be highly authored. Do not mark it as slop merely because it uses heavy borders or unusual composition.

## 9.12 Dark mode

Dark UI is entirely valid. The problem is when “dark + neon glow + glass + grid” is selected as a shortcut for “AI/technology.”

---

# 10. ANTI-SLOP GENERATION RULES

The negative prompt is only half of the solution. Models need positive constraints that force a different behavior.

## Rule 1 — Start with user goals, not components

Before designing, explicitly identify:

- primary user,
- primary task,
- highest-value information,
- most common flow,
- highest-risk failure,
- expected content density,
- domain conventions,
- accessibility needs,
- mobile constraints.

## Rule 2 — Produce a design thesis

Before implementation, state in 1–3 sentences:

- the visual tradition,
- the emotional tone,
- the compositional principle,
- the type strategy,
- the color strategy,
- what the interface intentionally refuses to do.

## Rule 3 — Define tokens before components

Specify semantic tokens for:

- background,
- surface,
- elevated surface,
- text-primary,
- text-secondary,
- border,
- accent,
- action,
- success,
- warning,
- danger,
- focus,
- typography scale,
- radius scale,
- spacing scale,
- motion durations/easing.

## Rule 4 — Design hierarchy, not decoration

For every major section, identify:

1. what the user should notice first,
2. what they should understand second,
3. what action comes third.

## Rule 5 — Let content shape layout

Do not force information into a 3-column grid merely because there are three columns available.

## Rule 6 — Vary geometry deliberately

Use radius, spacing, scale and alignment differences only where hierarchy or brand requires them.

## Rule 7 — Use gradients only when they communicate something

A gradient may represent:

- material,
- lighting,
- data range,
- progress,
- brand transition,
- spatial depth,
- atmospheric context.

It should not exist simply because the hero looked empty.

## Rule 8 — Use animation only when it has a user-facing reason

Every animation should have an explicit purpose:

- continuity,
- feedback,
- spatial orientation,
- state change,
- storytelling,
- attention management.

## Rule 9 — Write real copy before final styling

Copy is part of layout. Never finalize type scale around placeholder slogans.

## Rule 10 — Use evidence instead of manufactured trust

No fake customer logos, metrics, testimonial names, compliance claims or fabricated activity.

## Rule 11 — Design the negative states

For each meaningful feature, explicitly account for:

- loading,
- empty,
- error,
- success,
- disabled,
- permission,
- offline/sync,
- long content,
- mobile.

## Rule 12 — Preserve platform conventions where they help

Originality is not the goal of every interaction. Familiar patterns reduce cognitive load. Be distinctive in visual language and product expression without making common operations unnecessarily unfamiliar.

## Rule 13 — Accessibility is part of art direction

Focus, reduced motion, contrast, target sizes, keyboard behavior and semantics must survive the visual direction.

## Rule 14 — Design for real content

Use:

- long names,
- empty values,
- multiline text,
- localization-like expansion,
- edge-case numbers,
- missing images,
- slow connections.

## Rule 15 — Refuse template continuation

When a familiar template starts to emerge, stop and reconsider the information architecture rather than changing only the colors.

---

# 11. ANTI-SLOP REVIEW PROTOCOL

## Pass A — Five-second recognition test

Squint at the interface.

Ask:

- Does it immediately read as “generic AI SaaS”?
- Would swapping the logo and product name produce the same page for another company?
- Is the strongest visual signal actually the product, or generic visual decoration?

## Pass B — Remove color test

Imagine the interface in grayscale.

Does hierarchy still work?

If not, the system may be relying on accent color instead of structure.

## Pass C — Remove decoration test

Temporarily remove:

- gradients,
- shadows,
- blur,
- glow,
- animation,
- icons.

If the interface collapses, the underlying information architecture may be weak.

## Pass D — Copy replacement test

Replace all marketing copy with labels such as:

- Heading,
- Feature A,
- Feature B,
- CTA.

Does the composition still feel coherent? If not, visual treatment may be compensating for weak content.

## Pass E — Product swap test

Change the product category mentally:

“project management” → “hospital scheduling.”

If the visual system remains equally plausible with no change, it may lack domain specificity.

## Pass F — Component permutation test

Move sections around.

If the page remains structurally identical regardless of content order, the generator may be following a template rather than a narrative.

## Pass G — State completeness test

Inspect default, hover, focus, active, disabled, loading, error and empty states.

## Pass H — Mobile reality test

Use narrow widths and realistic long strings. Do not merely inspect a static “responsive” screenshot.

## Pass I — Credibility test

Every claim should answer:

> How would a skeptical user verify this?

## Pass J — Authorship test

Ask:

> Which three decisions would a human designer recognize as uniquely specific to this product?

If the answer is “the accent color, logo and wording,” the visual authorship is probably too weak.

---

# 12. BEFORE/AFTER EXAMPLES

## Example 1 — Generic AI SaaS hero

### Slop

> Badge: “NOW IN BETA” with pulsing dot  
> H1: “Build the Future of Work” with gradient on “Future”  
> Subhead: “A powerful AI platform that helps teams unlock seamless productivity.”  
> Buttons: “Get Started” + “See How It Works →”  
> Hero background: blue-violet gradient + blurred orb  
> Right side: fake browser window with dashboard cards

### Anti-slop

> H1: “The morning handoff should not take forty minutes.”  
> Subhead: “Auto-generate the shift summary from completed notes, unresolved tasks and incidents.”  
> Primary action: “Create this morning’s handoff”  
> Supporting visual: a real handoff document with one live/realistic task state  
> Composition: text aligned to a strong editorial grid; visual occupies enough space to prove the workflow rather than decorate it.

**Why it is different:** the product promise is concrete, the CTA describes the next operation, and the visual demonstrates the workflow.

---

## Example 2 — Three cards vs task sequence

### Slop

Three identical cards:

1. **Fast** — Lightning icon — “Move faster.”
2. **Secure** — Shield icon — “Stay protected.”
3. **Smart** — Sparkles icon — “Work smarter.”

### Anti-slop

A vertical sequence:

**01. Import the case**  
Show actual accepted inputs.

**02. Detect conflicts**  
Show a conflict highlight with a real example.

**03. Produce the review packet**  
Show what the user gets and what remains for human review.

The visual structure follows the actual workflow, not the number three.

---

## Example 3 — Dashboard card soup

### Slop

Four KPI cards at top, each with rounded corners and a sparkline. Below them: three chart cards. Below that: activity card. All surfaces have the same radius and shadow.

### Anti-slop

The primary task is an operations queue, so:

1. the queue dominates the viewport,
2. filters and search remain immediately accessible,
3. a narrow secondary column surfaces exceptions,
4. KPIs are compact context rather than giant ornaments,
5. charts appear only where they support a decision.

---

## Example 4 — Fake trust section

### Slop

“Trusted by leading teams” + six grayscale logos + endless marquee.

### Anti-slop

“One deployment, one measurable result.”

> “We cut reconciliation from 6 hours a week to 40 minutes.”  
> Dana Cho · Head of Finance, Lattice

Then provide a case-study link and methodology.

**Rule:** one true, inspectable claim beats a wall of generic logos.

---

## Example 5 — Purple gradient replacement

### Slop

Blue → purple → pink gradient behind hero copy.

### Weak anti-slop

Same page, orange → red → yellow gradient.

### Strong anti-slop

The gradient is removed. The product instead uses a single warm accent for interaction, a near-paper background, black ink, a structural grid and one photographic image whose lighting carries the atmosphere.

**Lesson:** “different color” is not enough.

---

## Example 6 — AI feature button

### Slop

Sparkles icon + “AI Magic” + gradient button.

### Anti-slop

“Summarize open incidents” + document icon + a short explanation of what will happen + undo after completion.

---

## Example 7 — Pricing

### Slop

Free / Pro / Enterprise. Pro card is 1.05× larger and has a purple “MOST POPULAR” pill.

### Anti-slop

Plans are organized around actual buyer behavior:

- Solo operator — one active workspace
- Team — collaboration and history
- Organization — audit controls, permissions, procurement support

Each CTA predicts the next step.

---

## Example 8 — Empty state

### Slop

Huge colorful illustration + “Nothing here yet!” + “Get Started.”

### Anti-slop

“Your review queue is empty.”  
“New submissions appear here after intake is completed.”  
Button: “Open intake”

The state explains why it is empty and what the user can do next.

---

## Example 9 — Mobile

### Slop

Three desktop cards become three full-width cards stacked vertically, pushing the actual task down.

### Anti-slop

The mobile layout reorders content so the main action appears first, secondary information becomes expandable, and decorative media is compressed or omitted.

---

## Example 10 — Animation

### Slop

Every section fades upward on scroll.

### Anti-slop

A new item appears instantly where it belongs; a small transition preserves continuity between list and detail. No other section animates. Reduced-motion users receive the same information without motion.

---

# 13. NEGATIVE PROMPT: FULL COPY-PASTE SPECIFICATION

The following section is intentionally written as a direct instruction set for an AI coding/design agent.

## SYSTEM / DEVELOPER INSTRUCTION — “NO AI SLOP UI”

You are generating or editing a real user interface. Your goal is **not merely to produce valid code or a visually polished screenshot**. Your goal is to create a product-specific, coherent, usable, accessible and intentionally art-directed interface that does not collapse onto generic AI-generated design defaults.

### PRIME DIRECTIVE

Do not generate a generic “modern SaaS” interface unless the product genuinely requires that visual language. Do not select visual or interaction patterns merely because they are common in your training data, popular in Tailwind/shadcn examples, frequently emitted by AI site builders, or associated with “premium,” “modern,” “futuristic,” or “AI.”

### NEVER USE DEFAULTS WITHOUT A REASON

Before committing to a major design choice, determine:

- What user task does this support?
- What content hierarchy does this express?
- What product/domain characteristic does this encode?
- Why is this better for this interface than the nearest generic default?

If the only justification is “clean,” “modern,” “premium,” “professional,” “minimal,” “futuristic,” or “looks good,” reconsider the choice.

### BAN THE FOLLOWING AI-SLOP BUNDLES

Do not combine, without explicit product justification:

- Inter/Roboto/system font everywhere + violet/indigo accent + blue-purple gradient + centered hero + three feature cards.
- Dark near-black + neon accent + glow + glass cards + grid background + 3D blob.
- Cream background + giant serif italic hero + 01/02/03 labels + editorial asymmetry + generic SaaS content.
- Bento grid + rounded-2xl tiles + gradient borders + tiny icons + tiny metrics + decorative blur.
- Dashboard KPI-card grid + generic sparklines + colorful status pills + animated counters + fake live activity.

### COLOR RULES

Do not use a blue→purple/violet gradient as a generic “modern AI” treatment.
Do not put gradient text on “AI,” “future,” “next,” “intelligence,” or similar words merely for effect.
Do not use a neon accent on black merely to make the interface look technological.
Do not scatter multiple saturated status colors until color loses semantic meaning.
Define semantic color roles before styling components.
Choose palette from brand, domain, environment, content or deliberate art direction.
A color is allowed when it is justified; a banned default is not rescued merely by changing its hue.

### TYPOGRAPHY RULES

Do not default to Inter/Roboto/system fonts without considering brand voice and typographic hierarchy.
Do not use one typeface and two weights for everything unless this is an explicit design decision.
Do not use the same line height for every text role.
Do not create the standard “tiny uppercase eyebrow + giant centered H1 + gray subhead” on autopilot.
Do not shrink useful labels into 9–11px micro-type just to make the page look sophisticated.
Write real content before finalizing type hierarchy.

### LAYOUT RULES

Do not default to centered composition for the entire page.
Do not force exactly three feature cards.
Do not make every section identical in width, shape and rhythm.
Do not use bento merely because bento is fashionable.
Do not turn every content block into a card.
Do not nest bordered/rounded cards unless containment is semantically meaningful.
Let content quantity, priority and interaction determine layout.
Use asymmetry only when it improves hierarchy, rhythm or brand expression; do not perform fake asymmetry.

### SURFACE RULES

Do not use rounded-2xl on every element.
Do not use one radius token for the entire interface unless it is deliberately part of the system.
Do not give every card the same diffuse shadow.
Do not add glassmorphism to surfaces that do not need translucency or depth.
Do not add gradient borders/glows because a plain border feels “boring.”
Use elevation as a semantic system, not a decoration system.

### HERO RULES

Do not automatically include:

- beta pill,
- pulsing dot,
- giant centered headline,
- gradient word,
- two generic CTA buttons,
- abstract blob,
- fake product browser window.

A hero must explain the product or create a meaningful first interaction. Prefer concrete product evidence over decorative atmosphere.

### FEATURE RULES

Do not generate six generic feature cards merely because a landing page “needs a Features section.”
Do not pair every feature with Sparkles, Zap, Shield, Check or BarChart icons.
Use the structure that matches how users understand the product: sequence, comparison, workflow, demonstration, narrative, evidence, or direct interaction.

### TRUST RULES

Never fabricate testimonials, people, company logos, statistics, customer counts, uptime percentages, compliance badges, awards, certifications, partner marks or usage numbers.
Never use placeholder names as if they were real users.
Never use Logo Ipsum as social proof.
Never create a continuously scrolling logo marquee unless there is a real, meaningful reason and real content.
Prefer specific, inspectable evidence.

### PRICING RULES

Do not automatically generate Free / Pro / Enterprise.
Do not automatically highlight the middle plan.
Do not use “MOST POPULAR” gradient pills unless the actual business model and evidence justify the recommendation.
Do not hide costs or invent discounts.
Every price, qualifier and CTA must match the actual product offer.

### ICON RULES

Do not automatically use Sparkles for AI, Zap for speed, Shield for security and ArrowRight for every CTA.
Use function-true icons.
Use one coherent icon family when icons are appropriate.
Do not use emoji as professional feature iconography unless the domain and tone explicitly call for it.

### AI-UI RULES

Do not make chat the universal interface.
Do not add an AI panel where direct manipulation is faster.
Do not label normal automation “AI-powered” merely to make the product look advanced.
Do not expose model/vendor names as the primary user-facing feature label unless relevant.
Do not use sparkle/glow effects to announce AI.
Do not automatically use Generate → Preview → Insert.
Where possible, integrate AI into the user’s real workflow and provide undo/recovery.

### MOTION RULES

Do not fade or slide every element on scroll.
Do not use identical stagger timings everywhere.
Do not make every card lift on hover.
Do not use marquess, parallax, cursor effects, glows or spring animation as decoration by default.
Every meaningful motion must have a user-facing purpose.
Honor `prefers-reduced-motion`.
Do not hide important content behind animation.

### RESPONSIVE RULES

Do not simply stack desktop columns on mobile.
Do not preserve desktop hero proportions when they damage mobile task visibility.
Do not allow horizontal overflow or tiny touch targets.
Reorder information around mobile priorities.
Hide decorative content before critical task information.
Design touch behavior explicitly.

### ACCESSIBILITY RULES

Never remove focus indication without replacing it with an accessible equivalent.
Maintain appropriate text and non-text contrast.
Do not rely on color alone to communicate state.
Support keyboard interaction.
Ensure semantic headings and controls.
Respect reduced motion preferences.
Ensure targets are usable at pointer/touch sizes.
Prevent sticky UI from obscuring focus.
Do not use hover-only information where keyboard/touch users cannot access it.

### STATE RULES

For every meaningful interactive feature, consider:

- default,
- hover,
- focus,
- active,
- disabled,
- loading,
- success,
- error,
- empty,
- permission/restricted,
- offline/sync where applicable,
- long-content behavior,
- mobile behavior.

A page that only works in the happy path is not finished.

### COPY RULES

Avoid generic AI marketing phrases such as:

- “Build the future of …”
- “Unlock your potential”
- “Elevate your workflow”
- “Transform the way you …”
- “Empower your team”
- “Seamless experience”
- “Powerful platform”
- “All-in-one solution”
- “The future of work”
- “Next-generation AI”

Unless one of these phrases is intentionally part of the actual brand voice, replace it with a specific, verifiable claim.

Do not use generic CTAs such as “Get Started” or “Learn More” when a more specific CTA can describe the next action.

### IMPLEMENTATION RULES

Do not scatter raw hex values throughout the code without semantic meaning.
Do not solve every visual conflict with another CSS override.
Do not accumulate arbitrary z-index values.
Do not rely on placeholder sample data.
Do not leave starter metadata, favicons or generator attribution in production.
Do not claim a feature works if it is only visually simulated.
Do not create fake “live” activity.
Do not omit error handling merely because the screenshot works.

### FINAL ART-DIRECTION CHECK

Before delivering, inspect the rendered interface and ask:

1. Could I swap the product name and reuse this exact design for five unrelated products?
2. If I remove the gradients/glows/shadows, does the hierarchy still work?
3. Is the layout shaped by content or by a landing-page template?
4. Are any trust signals fabricated or unverifiable?
5. Is AI being communicated through actual functionality or through sparkles/glows/labels?
6. Does the interface contain a distinctive visual thesis?
7. Are repeated components repeated because of semantics or because they were easy to generate?
8. Does mobile have its own composition?
9. Are empty/error/loading states designed?
10. Can every major visual decision be justified in one sentence?

If the answers reveal genericity, refactor the design rather than merely recoloring it.

### DO NOT “ANTI-SLOP” BY BECOMING RANDOM

Do not replace generic design with random asymmetry, arbitrary color, illegible typography, unnecessary brutalism, excessive whitespace, bizarre interactions, or intentionally ugly elements.
The objective is **intentionality + usability + specificity**, not novelty for novelty’s sake.

---

# 14. COMPACT NEGATIVE PROMPT

**Never produce generic AI-slop UI. Do not default to Inter/Roboto/system + violet/indigo gradient + centered hero + eyebrow pill + two generic CTAs + three identical feature cards + rounded-2xl everything + shadow-lg everything + glassmorphism + Sparkles/Zap/Shield icons + gradient text + fake dashboard/browser mockups + bento grids used without content justification + generic logo walls + fake testimonials + invented metrics + 3-tier pricing with a glowing “Most Popular” middle tier + fade-up-on-scroll everywhere + hover-lift on every card + generic “Build the future / Elevate your workflow / Seamless / Powerful / AI-powered” copy + “Get Started/Learn More” everywhere + AI chat panels for direct-manipulation tasks + preview/Insert AI ceremonies + decorative grid/noise/glow backgrounds + black/neon “AI lab” aesthetic + cream/editorial anti-slop clones used mechanically.**

**Make decisions from product, domain, audience, content, task, brand and accessibility. Use distinctive typography, semantic tokens, purposeful composition, deliberate spacing/radius/elevation hierarchy, real content, real states, meaningful motion, credible evidence, specific copy, and responsive behavior. Do not merely swap purple for another color; escape the underlying template. Use familiar platform conventions for common interactions, but make the visual language product-specific. Never fabricate data, trust signals, customer logos, testimonials, certifications or functional behavior. Honor WCAG and reduced-motion requirements. Inspect the rendered result and refactor any interface that remains visually interchangeable.**

---

# 15. AUTOMATED DETECTION HEURISTICS AND LINT IDEAS

A useful scanner should treat slop as a **bundle score**, not a single-regex ban.

## 15.1 Example rule families

### Color detector
Flag when:

- hero uses blue→purple or indigo→violet gradient,
- gradient text appears in prominent marketing headline,
- same gradient is reused in CTA + hero + border,
- accent color is used without semantic tokens.

### Typography detector
Flag when:

- Inter/Roboto/system is the only family,
- fewer than 3 meaningful display/body scales exist,
- all headings use one weight,
- body measure becomes excessively wide,
- labels drop below practical legibility.

### Surface detector
Flag when:

- same radius appears on buttons, cards, modals, inputs and page shells,
- same shadow appears on most surfaces,
- backdrop-blur is applied to multiple unrelated elements,
- card-in-card frequency exceeds semantic need.

### Layout detector
Flag when:

- main hero content is centered,
- immediate feature section is exactly three equal cards,
- page sections share identical vertical padding,
- all content aligns to the same center line,
- identical card shapes occur across multiple semantic categories.

### Copy detector
Flag generic phrase families:

- build the future,
- unlock,
- elevate,
- transform,
- empower,
- seamless,
- next-generation,
- all-in-one,
- AI-powered,
- get started,
- learn more,
- trusted by leading teams.

Do **not** ban phrases individually. Use frequency + context.

### Trust detector
Flag:

- generic fake names,
- logoipsum-like asset paths,
- DiceBear/default avatar placeholders,
- checkmark-only testimonials,
- unsupported statistics,
- compliance badges without source.

### Motion detector
Flag:

- identical `opacity:0 → 1` + translateY patterns repeated across sections,
- uniform stagger intervals,
- marquee loops,
- pointer hover transform on every card,
- animations missing reduced-motion handling.

### State detector
Flag components that define only default rendering while lacking:

- loading,
- error,
- empty,
- disabled,
- focus-visible,
- recovery paths.

## 15.2 A useful conceptual formula

A heuristic score can be modeled as:

```text
SLOP_RISK =
    DEFAULT_TOKEN_DENSITY
  + TEMPLATE_DENSITY
  + DECORATION_TO_INFORMATION_RATIO
  + GENERIC_COPY_DENSITY
  + FAKE_TRUST_RISK
  + STATE_INCOMPLETENESS
  + ACCESSIBILITY_DEFICITS
  + PRODUCT_SPECIFICITY_DEFICIT
  - INTENT_EVIDENCE
  - DOMAIN_SPECIFICITY
  - REAL_CONTENT_DENSITY
  - SEMANTIC_COHERENCE
```

Do not present this as scientific psychometrics. It is a tooling heuristic.

## 15.3 Bundle logic is essential

Example:

```text
Inter alone → 0 / negligible
rounded card alone → 0 / negligible
purple alone → 0 / negligible

Inter + purple gradient + centered hero + three-card grid → high suspicion

Inter + purple + centered hero + three cards + fake testimonials
+ generic CTA + glass navbar + gradient text + fade-up-everything
→ very strong generic-AI signature
```

This approach reduces false positives while catching the actual phenomenon: **convergence**.

---

# 16. EVALUATION MATRIX

| Dimension | Questions | Failure example | Desired behavior |
|---|---|---|---|
| Product specificity | Could this UI belong to another product? | Generic SaaS skeleton | Product-specific structure |
| Visual authorship | Are there recognizably intentional choices? | Defaults only | Clear design thesis |
| Content hierarchy | Does layout follow importance? | Equal cards everywhere | Deliberate emphasis |
| Typography | Does type carry brand and hierarchy? | One family/2 weights | Coherent scale + character |
| Color semantics | Does color mean something? | Many bright pills | Semantic palette |
| Geometry | Do radii/borders convey hierarchy? | Same radius everywhere | System with hierarchy |
| Surface treatment | Is depth purposeful? | Shadow/glass everywhere | Selective elevation |
| Layout variety | Does each section suit its content? | Every section same grid | Content-shaped composition |
| Motion | Does movement communicate? | Fade-up everything | Few purposeful transitions |
| Trust | Are claims real? | Fake logos/stats | Evidence-based proof |
| UX states | Are edge states designed? | Happy path only | Complete state model |
| Accessibility | Can all users operate it? | Focus removed | Accessible by construction |
| Mobile | Does layout recompose? | Stack-down | Mobile-first priorities |
| AI integration | Does AI serve the workflow? | Chat bolted on | Native task integration |
| Copy | Does language describe the product? | “Empower your team” | Concrete claims |
| Implementation | Is the system maintainable? | Magic numbers/overrides | Tokenized system |

---

# 17. RESEARCH NOTES AND LIMITATIONS

## 17.1 The term is not a formal scientific diagnosis

“AI slop” is an emerging community label. The catalog in this document is operational: it is meant to help a design agent avoid recognizable failure modes, not to establish a formal academic category.

## 17.2 Human designers invented most “AI tells”

Rounded cards, gradients, glass, bento grids, editorial typography, dark themes and animation all predate generative UI. Their presence is therefore not evidence of machine authorship.

## 17.3 Detection must evolve

As soon as a visual tell becomes publicly known, models can learn to avoid it. The durable anti-slop principle is therefore:

> **Require explicit design reasoning and product specificity, not simply a forbidden list of colors and components.**

## 17.4 Reddit is excellent for vocabulary, weak for prevalence

Community posts reveal what designers/users notice, complain about and debate. They do not establish population frequencies.

Recent Reddit discussions in 2026 show both strong recognition of the aesthetic bundle and a counterargument: calling individual elements “AI slop” can become too broad because the same patterns were common in human design before generative AI. The strongest community formulation is therefore close to “generic, thoughtless, interchangeable combination,” not “contains rounded corners.”

## 17.5 X-specific evidence is harder to audit

The search sweep found broad X discourse around AI slop, but directly indexed X material specifically about web/UI slop was substantially sparser than Reddit and GitHub. This document therefore avoids fabricating X quotations or attributing specific UI claims to individual X users without a directly inspectable source.

## 17.6 The “anti-slop aesthetic” can itself become slop

Once generators learn that AI slop means:

- purple,
- Inter,
- rounded cards,
- centered layout,

they may simply produce:

- cream,
- serif,
- square cards,
- asymmetric layout.

The page will look less like first-generation AI output while remaining equally generic.

## 17.7 The detector must protect usability

Nielsen Norman Group’s guidance on consistency and standards matters here. An interface should not sacrifice familiar conventions simply to look original. Distinctive styling should sit *above* a usable interaction model, not replace one.

---

# 18. SOURCES AND FURTHER READING

## 18.1 Primary / research-oriented sources

1. **Kran, Esben et al. — DarkBench: Benchmarking Dark Patterns in Large Language Models (ICLR 2025).**  
   https://arxiv.org/html/2503.10728v1  
   https://proceedings.iclr.cc/paper_files/paper/2025/file/6f6421fbc2351067ef9c75e4bcd12af5-Paper-Conference.pdf

2. **CANVAS: A Benchmark for Vision-Language Models on Tool-Based User Interface Design (2025).**  
   https://arxiv.org/abs/2511.20737

3. **W3C — Web Content Accessibility Guidelines (WCAG) 2.2.**  
   https://www.w3.org/TR/WCAG22/Overview.html

## 18.2 Usability / UX standards

4. **Nielsen Norman Group — Maintain Consistency and Adhere to Standards.**  
   https://www.nngroup.com/articles/consistency-and-standards/

5. **Nielsen Norman Group — 5 Principles of Visual Design in UX.**  
   https://www.nngroup.com/articles/principles-visual-design/

6. **W3C WAI — Understanding Animation from Interactions.**  
   https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html

## 18.3 Current anti-slop taxonomies / practitioner sources

7. **Artificial Human Design — The Slop Taxonomy.**  
   https://github.com/Ad-Astra-Computing/ahd/blob/main/docs/SLOP_TAXONOMY.md

8. **Precious Studio — Slop Patterns: a public library of AI design tells (23 Sep 2026).**  
   https://precious.studio/journal/launching-slop-patterns

9. **funboy322 — avoid-ai-design.**  
   https://github.com/funboy322/avoid-ai-design

10. **hankimis — ai-design-tells.**  
    https://github.com/hankimis/ai-design-tells

11. **hankimis — AI-DESIGN-TELLS.md.**  
    https://github.com/hankimis/ai-design-tells/blob/main/harness/AI-DESIGN-TELLS.md

12. **febbhav — signs-of-ai-design.**  
    https://github.com/febbhav/signs-of-ai-design

13. **925 Studios — AI Slop Web Design: Complete Guide to Spotting and Fixing Generic Websites (2026).**  
    https://www.925studios.co/blog/ai-slop-web-design-guide

14. **Can Dedeoglu — Escaping AI Slop: A Practical System for Design Taste (2026).**  
    https://www.candede.com/articles/escaping-ai-slop-in-web-design/

15. **NxtFruit — AI Slop Design: Why Every AI Landing Page Looks the Same (2026).**  
    https://nxtfruit.com/2026/08/08/ai-slop-design/

16. **Beaver Builder — How to Avoid AI Slop in Web Design (2026).**  
    https://www.wpbeaverbuilder.com/avoid-ai-slop-in-web-design/

17. **UX Skill — Everything built with shadcn/ui looks the same and how to break out (2026).**  
    https://uxskill.laithjunaidy.com/blog/shadcn-ui-looks-generic.html

## 18.4 Community evidence

18. **Reddit — Preventing the AI slop look (r/webdesign, June 2026).**  
    https://www.reddit.com/r/webdesign/comments/1uhuovu/preventing_the_ai_slop_look/

19. **Reddit — Any advice to escape the AI slop web design look? (r/vibecoding, June 2026).**  
    https://www.reddit.com/r/vibecoding/comments/1ubewk8/any_advice_to_escape_the_ai_slop_web_design_look/

20. **Reddit — Websites looking like “AI slop” (r/UI_Design, Sep 2026).**  
    https://www.reddit.com/r/UI_Design/comments/1w70kqb/question_about_websites_looking_like_ai_slop/

21. **Reddit — Web design is depressing (r/webdesign, Apr 2026).**  
    https://www.reddit.com/r/webdesign/comments/1slhc5f/web_design_is_depressing/

22. **Reddit — I hate AI generated web design (Aug 2026).**  
    https://www.reddit.com/r/hatethissmug/comments/1vcj2r4/i_hate_ai_generated_web_design/

23. **Reddit — Clients want slop (Sep 2026).**  
    https://www.reddit.com/r/webdev/comments/1wnognr/clients_want_slop/

24. **Reddit — So many websites look like this now (June 2026).**  
    https://www.reddit.com/r/webdesign/comments/1u1579w/so_many_websites_look_like_this_now/

25. **Reddit — I finally figured out why every AI-coded site looks the same and how to actually fix it (Aug 2026).**  
    https://www.reddit.com/r/ClaudeCode/comments/1vvzqvj/i_finally_figured_out_why_every_aicoded_site/

## 18.5 Additional practitioner material referenced during synthesis

26. **Rottoways — Why your AI generated website looks like every other AI generated website (2026).**  
    https://rottoways.com/blog/ai-generated-website-looks-generic

27. **Joshua Snoddy — Why Do AI-Generated Websites All Look the Same? (2026).**  
    https://www.joshuasnoddy.com/blog/why-ai-websites-look-the-same/

28. **Social Animal — Brutalist & Editorial Web Design.**  
    https://socialanimal.dev/solutions/brutalist-editorial-web-design/

---

# APPENDIX A — THE “ONE SENTENCE OF INTENT” DEVICE

For each major visual dimension, require a one-sentence justification:

| Dimension | Example acceptable intent |
|---|---|
| Typography | “The display serif echoes the product’s archival/research positioning, while the grotesk remains readable for dense metadata.” |
| Color | “The warm clay accent comes from the brand identity and is reserved for actions and selected states.” |
| Radius | “Controls are compact and lightly rounded; cards use larger radii only where they represent independent objects.” |
| Layout | “The primary workflow gets 65% of the viewport because it is the user’s main task; secondary analytics are visually quieter.” |
| Motion | “The detail panel slides from the list to preserve spatial continuity; decorative sections remain static.” |
| Iconography | “Icons are function-specific and use one optical stroke weight.” |
| Copy | “CTA labels describe the next system action instead of using generic marketing language.” |

If the agent cannot write a plausible intent sentence, it should reconsider the design choice.

---

# APPENDIX B — MINIMUM EVIDENCE A SERIOUS GENERATOR SHOULD RETURN INTERNALLY

Before implementation, a high-quality agent should be able to resolve:

```text
PRODUCT:
PRIMARY USER:
PRIMARY TASK:
SECONDARY TASKS:
DOMAIN CONVENTIONS:
BRAND CHARACTER:
CONTENT DENSITY:
VISUAL THESIS:
TYPE DIRECTION:
COLOR DIRECTION:
LAYOUT PRINCIPLE:
SURFACE/ELEVATION PRINCIPLE:
ICONOGRAPHY PRINCIPLE:
MOTION PRINCIPLE:
MOBILE PRINCIPLE:
ACCESSIBILITY CONSTRAINTS:
STATES TO DESIGN:
TRUST / EVIDENCE RULES:
FORBIDDEN DEFAULTS:
REASON THESE DEFAULTS ARE EXCLUDED:
```

This is much stronger than asking the model to “make it not AI-looking.”

---

# APPENDIX C — THE ULTIMATE META-RULE

> **Do not optimize the interface to escape the appearance of AI. Optimize it to become genuinely specific to the product.**

A model can learn every banned class string in this document and still produce slop if it does not understand what users are trying to accomplish.

The target state is not:

**“Looks human.”**

The target state is:

**“Looks like the result of a coherent product decision.”**

That distinction should be the foundation of every negative prompt, design review, linter, visual evaluator and autonomous coding agent that uses this document.

---

## END OF DOCUMENT
