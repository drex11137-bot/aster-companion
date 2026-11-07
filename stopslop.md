# The Anti-Slop UI Doctrine: Negative Prompt Dossier on AI-Generated UI/UX

Oct 2, 2026 · @TheAmazingDivine

## Part 0: How to use this document

**AI slop in UI is any visible decision that nobody made.** The purple gradient, the Inter headline, the three identical icon cards, the pulsing 'Active' badge on something that is never inactive: none of these is wrong on its own. Each is wrong because no one chose it. It is the statistical median of the training data, surfacing wherever the brief was silent.

This dossier is built from the research below (design blogs, Hacker News and Reddit-style community threads, X posts, GitHub anti-slop skills, Anthropic's own frontend guidance, and academic papers on design homogenization). It is written to be read by an AI model as a negative prompt and review spec, and by a human as a reference.

### 0.1 The one test

For every element on screen ask: **does it convey real information, or serve this specific context?**

- If yes, it is craft. Keep it. A chevron that signals 'expandable', a status pill that maps to a real distinct state, a relative timestamp in an activity log, a dark-mode toggle.
- If it is there because it 'looks like a dashboard', 'looks technical', 'looks premium' or 'looks modern', it is slop. Cut it or replace it with something that earns its place.

The slop is never the element. It is the reflexive, meaningless use of the element.

### 0.2 Three ways to use this document

1. **Negative-prompt mode:** paste the block in Part 1 into a system prompt, CLAUDE.md, or a skill. It is a compact distillation of every part.
2. **Reference mode:** give the full document to an agent as a knowledge file. Parts 3 to 11 are the catalog (tell, why it reads as AI, what to do instead). Part 13 is the positive protocol. Part 14 has before/after examples.
3. **Audit mode:** run Part 15 (scoring rubric, grep patterns, acceptance tests) against output the model just produced, and fix every hit before shipping.

### 0.3 Precedence

The user's brief always wins. If the user explicitly asks for glassmorphism, a purple brand, a cream-and-serif look or a dark terminal aesthetic, build exactly that. Every rule here is a default to resist when the brief is silent, never a ban on something the user asked for. A tell is evidence of a default nobody chose, never proof of anything else.

### 0.4 Severity tiers

| Tier | Meaning | Examples |
| --- | --- | --- |
| P0 | A layperson clocks it as AI in half a second | Purple/indigo-to-blue gradient, gradient headline text, centered hero + pill badge + three icon cards, Inter everywhere, untouched shadcn zinc, emoji as icons |
| P1 | A designer or developer clocks it | Colored left-border cards, rounded-2xl + shadow-lg on everything, glassmorphism by reflex, 'Welcome back, John' dashboards, Lucide icon in a tinted rounded square, 1-2-3 steps, stat banners |
| P2 | Craft-level giveaway | Uniform spacing with no rhythm, the same fade-up on every section, tracked all-caps eyebrows, missing hover/focus/empty/error states |

### 0.5 Operating protocol (do this in order)

1. **Read the brief for what it does NOT say.** Every silence is a slot the model will fill with the median. List the open axes: palette, type, layout, density, tone, motion, imagery.
2. **Write a design direction before any code** (Part 13): visual thesis, 4 to 6 named hex colors with roles, two typefaces with roles, one layout concept, one signature move, three explicit refusals.
3. **Derive the direction from the product's own materials** (its data, artifacts, vernacular), not from the category's cliche.
4. **Review the plan against the slop list.** If the plan could describe any other product in the category, rewrite it.
5. **Build with tokens** (CSS variables), never scattered hex values or untouched component-library defaults.
6. **Design every state:** empty, loading, error, success, disabled, focus, hover, active, long-text, no-data.
7. **Render and look** (screenshot at 375px and 1440px). Check against Part 15.
8. **Report the decisions you made and why**, so a human can argue with them.

## Part 1: The paste-ready negative prompt

Copy everything inside the block into a system prompt, CLAUDE.md, .cursorrules or a skill file. It is deliberately dense. Parts 3 to 12 explain each line with examples.

```text
ANTI-SLOP UI RULES. These are defaults to resist. An explicit user brief overrides any line.

PRE-FLIGHT (before writing any UI code)
- Write a design direction first: one-sentence visual thesis; 4-6 named colors (hex + role); 2 named typefaces (+ role); one layout concept; one signature move; 3 things this design refuses to do.
- Derive it from what this product is made of (its data, artifacts, vocabulary, users), not from its category. If the plan could describe any other product in the category, rewrite it.
- Pick the aesthetic by the brief, not by reputation. Never choose a font, color or layout because it is the known 'good' pick.
- Models also converge on the escape hatches. If you reach for a font or look because it feels like the non-generic choice (Space Grotesk, Fraunces, Instrument Serif, cream + terracotta, near-black + acid green), stop and choose again from the product.

NEVER (typography)
- Inter, Roboto, Arial, Open Sans, Poppins or the system stack as the only face. No headline/body contrast = no decision.
- Space Grotesk, Geist, Sora, Syne, Archivo, Plus Jakarta Sans, DM Sans, Manrope, Outfit, Fraunces, Instrument Serif, Playfair, Cormorant, Bodoni/Didot as an unexamined default.
- Gradient-filled headline text. One italic/colored/bold word inside an otherwise plain headline. A serif-italic accent word in a sans headline.
- Tracked-out ALL-CAPS eyebrow above every heading. ALL-CAPS section labels everywhere. Monospace as the 'technical' costume. '//' or '>' prefixes on labels. 01/02/03 markers on content that is not a real sequence.
- Flat hierarchy (sizes within 1.25x of each other), headline tracking tighter than -0.05em, 72px+ headlines over 40 characters, orphans, forced <br> breaks.

NEVER (color)
- Purple, violet, indigo or blue-to-purple gradients (hero, buttons, text, orbs, glows) unless the brand owns purple.
- Permanent dark mode by reflex; blue-charcoal (#0c0e15-ish) plus lilac accent; near-black plus one neon accent; glowing colored box-shadows; blurred aurora/orb blobs; grid or graph-paper backgrounds.
- Cream/beige page plus terracotta/clay accent (#D97757-ish) plus serif display as a reflex 'warm' look.
- Rainbow color with no semantics. Timid evenly-spread palettes. Gray text on colored backgrounds. Pure #000/#fff with no tint. Body text under WCAG AA (4.5:1).

NEVER (layout)
- Centered hero + pill badge above H1 + subhead + two buttons ('Get started' + ghost 'Learn more').
- Row of three identical icon-topped feature cards. Bento grid because it is trendy. Stat strip of invented numbers (10K+ users, 99.9% uptime, 4.9 stars).
- Canned page order: hero > logo soup > 3 cards > 1-2-3 steps > testimonials > 3-tier pricing with 'Most Popular' > FAQ accordion > gradient CTA slab > 4-column footer.
- One centered container width forever. Everything centered. Every section the same shape.

NEVER (components)
- rounded-2xl + shadow-lg + 1px gray border on every surface. Cards inside cards. Colored 3-4px left/top border stripe on cards. Glassmorphism/backdrop-blur by reflex.
- Lucide/Heroicons icon inside a tinted rounded square above a heading. Emoji as icons, bullets or nav labels. Sparkles icon = 'AI'.
- Pulsing status dots, 'Active', 'Verified', 'Live' badges that carry no real state. Gradient-circle initials avatars. Fake macOS window mockups with traffic-light dots. Fake code-snippet windows with a made-up SDK.
- Untouched shadcn/ui defaults (zinc base, 0.5rem radius). Hairline white/10 borders on every box. The same hover-lift + glow on every card.

NEVER (motion)
- The same fade-up-on-scroll on every section. hover:scale-105 on everything. Bouncing, wiggling, floating cards. Count-up stats. Marquees and parallax by reflex. Animated gradient blobs. Motion that ignores prefers-reduced-motion.

NEVER (app / dashboard UI)
- 'Welcome back, John' + 'Here's what's happening today' greeting. KPI-card row with sparklines and green/red percent deltas. Placeholder people and companies (John Doe, Jane Smith, Acme Corp, Nexus, Northwind, Sarah Chen). Invented metrics, activity feeds, testimonials and logos presented as real.
- Treating every screen like a landing page. Marketing copy inside tools. A chat panel bolted to the right of everything. Modals for anything that needs scrolling.
- Decorative sparklines, donut charts for non-parts-of-whole, charts with no axes or units.

NEVER (copy)
- Elevate, Seamless, Unleash, Unlock, Supercharge, Empower, Revolutionize, Next-generation, Cutting-edge, Robust, Leverage, Streamline, Game-changing, Delve, Tapestry, Journey, Ecosystem, Landscape.
- Em dashes and en dashes. 'Not just X, it is Y.' Tricolons of three abstract nouns. 'Whether you are X or Y.' 'In today's fast-paced world.' Emoji-led bullet headers. Redundant label + sublabel + helper + hint saying the same thing.
- Generic CTAs ('Get Started', 'Learn more', 'Submit'). Hype subtitles under every H1. Copy that echoes the chat prompt ('Built with Hugo. Written from Neovim.').

NEVER (UX / quality)
- Rationales without implementation. Only the happy path. Missing empty/loading/error/disabled/focus states. Contrast failures. Touch targets under 44px. Misaligned icons and text. No mobile menu. Breaks at 375px. Scroll hijacking. Decorative elements carrying no information.

ALWAYS
- Commit to one dominant color with one sharp accent (60/30/10). Tint your neutrals toward the brand hue.
- Pair a characterful display face with a clean text face; use weight extremes and 3x size jumps; body 16px+, 60-80 character measure, line-height 1.5-1.7.
- Break symmetry on purpose: left-aligned, asymmetric, type-led or content-led layouts. Vary section shape. One strong layout primitive, repeated, becomes the signature.
- Use real content, real numbers or none. Empty states say the one next action. Buttons name the result ('Send invoice').
- Use hierarchy of radius and elevation (not one global value). Separate surfaces by whitespace first, then a 3-5% lightness shift, then elevation. Borders last.
- One orchestrated moment of motion (a staggered load) beats scattered micro-interactions. Respect prefers-reduced-motion.
- Design every state. Test at 375px and 1440px. Run the self-check.

SELF-CHECK (fix any yes)
Default font? Any purple or gradient? Cream + terracotta or near-black + neon? Centered hero + badge? Three identical cards? Colored left stripe? Nested cards? Glass? Emoji or sparkle icons? Pulsing badges? Fake data? Hype words or em dashes? Same fade-up everywhere? Could this page belong to any other product with only the logo swapped? If yes to any, redo it from the direction.
```

Use the self-check as the final gate. The acceptance test from the research is blunt: if someone could look at the result and say 'AI made that' without doubt, it has failed.

## Part 2: Why slop happens

Understanding the mechanism lets a model generalize to tells that are not on any list yet. Every cause below is the same cause: **no decision was forced, so the average won.**

### 2.1 The mechanisms

1. **Regression to the mean.** A language model returns the most probable output. For a hero section, the most probable one is a centered headline, a blue/indigo button and three cards. An average is not a style; it is the absence of one.
2. **The Tailwind indigo-500 feedback loop.** Tailwind UI shipped indigo buttons as its default example. Years of tutorials, templates and repos copied it, which became training data, which produced indigo output, which got published and became the next round of training data. Adam Wathan (Tailwind's creator) publicly apologized on X in August 2025: 'I'd like to formally apologize for making every button in Tailwind UI bg-indigo-500 five years ago, leading to every AI generated UI on earth also being indigo.'
3. **Inherited library defaults.** shadcn/ui is designed to be copy-pasted, and its out-of-box look (zinc/slate neutrals, 0.5rem radius, rounded cards, Lucide icons) leaks into every generated project. Next.js starters ship Geist. Tailwind's most-used utilities (rounded-2xl, shadow-lg, backdrop-blur) are the ones in the official examples.
4. **Consistency is a feature for code and a bug for design.** LLMs are trained to write consistent code. They also write the code that represents designs, so they produce consistent designs and align on a generic mean (an observation from an engineer with Figma AI-tooling experience, reported in the discussion of Jim Nielsen's 'The AI Aesthetic', July 2026).
5. **Adjectives resolve to their own centroid.** 'Make it premium' gets a heavier font weight and a darker background. 'Make it unique' swaps violet for teal. The vocabulary underneath stays the same because nothing pinned it down.
6. **Frictionless generation invites acceptance.** The first plausible output looks finished, so people stop interrogating it (fixation). Defaults that were never discussed then get locked in by tests and decision records, and start to look like decisions.
7. **Chat context leaks into the product.** If the prompt mentioned Neovim, the footer says 'Written from Neovim'. If a manager asked to unify three apps, the splash says 'One campus. One app.' Information nobody needs appears because something in the context produced it and nobody asked whether it should stay.
8. **Models have house styles.** Different model families and versions have different signatures (reported in community discussion of the Show HN audit). Do not assume one list fits every model; audit the actual output.

### 2.2 The research, in numbers

| Source | What it found |
| --- | --- |
| Adrian Krebs, Show HN audit (Playwright, \~1,590 landing pages, 16 deterministic patterns) | 22% heavy (4+ patterns), 32% mild (2 to 3), 46% clean (0 to 1). Colored left-border cards were singled out as 'almost as reliable a sign of AI-generated design as em-dashes are for text'. |
| 'One Tool, One Taste?' (arXiv 2609.38183): 73 business sites built in Lovable by graduate students graded on originality | Six recurring archetypes cover 88% of sites; the effective number of distinct designs is about 12; the median site's nearest neighbor shares 49% visual similarity vs 23% across all pairs. Builders still reported high authorship and satisfaction. |
| 'Design Theater' benchmark (arXiv 2607.22928): 120 interfaces from 5 generative UI tools over 24 tasks | Over 25% of stated design rationales are not implemented (34% for functional requirements). Tools recognize only about half of the UX principles in the prompt; four of five implement 6% or fewer functional principles. Visual appearance and layout converge across tools; color varies more. |
| 'Interrogating Design Homogenization in Web Vibe Coding' (arXiv 2603.13036) | Frictionless generation invites the 'good enough' trap; proposes 'productive friction' as mitigation. |
| Goree et al., CHI 2021 (pre-LLM) | Web layouts became over 30% more similar after 2007, driven by shared libraries (Bootstrap and friends). LLMs scale that trend. |

### 2.3 The two waves

Ban the first set of defaults and the model does not become original; it moves to the next most probable look for a page 'trying not to look generated'.

- **Wave 1:** Inter everywhere, purple/indigo-to-blue gradient, glassmorphism, centered hero with pill badge, three rounded feature cards, the same fade-up everywhere.
- **Wave 2:** warm cream background with serif display and terracotta accent; near-black with one acid-green or vermilion accent; broadsheet hairlines with zero radius; identical SaaS cards with one shadow; tracked ALL-CAPS eyebrows, middle-dot meta strings, mono labels and arrows welded to every link.

Anthropic's own frontend-design guidance now names several wave-2 looks as tells (including a terracotta near its own Claude accent). The list also grew from three items to five in about eleven weeks, so any fixed list is a snapshot. The durable rule is: **make every visible decision traceable to something true about this product.**

### 2.4 Cost of slop

- **No recognition:** users cannot tell you apart from the five other tools that look identical.
- **No trust:** a template look signals 'assembled quickly', which is fatal for anything that handles real work or money.
- **No memory:** nothing to hold onto, recommend or return to.
- **Reflexive accessibility failures:** generated dark themes routinely ship body text that fails WCAG AA.
- **Hollow proof:** invented stats, testimonials and logos damage credibility the moment anyone checks.

## Part 3: Typography tells and fixes

Typography is the most visible and the cheapest place to stop looking generated. It is also where models fall into the second wave fastest.

### 3.1 Tells (what to refuse)

**T1. One neutral sans for every job (P0).** Inter, Roboto, Arial, Open Sans, Lato, Poppins or the system stack handling the 64px headline and the 12px footnote. No display/body contrast means nobody made a typography decision. Inter itself is excellent; the tell is an unchosen Inter.

**T2. The 'tasteful free font' cluster (P1).** The fonts models reach for to look non-generic have themselves become the tell: Space Grotesk, Geist, Sora, Syne, Archivo, Plus Jakarta Sans, DM Sans, Manrope, Outfit, Onest, Figtree, Gabarito, Hanken Grotesk, Schibsted Grotesk, Geologica, Spline Sans, Darker Grotesque; serifs Fraunces, Instrument Serif, Playfair Display, Cormorant Garamond, Newsreader, Bodoni Moda, Didot; display novelties like Bagel Fat One, Fredoka, Chewy. Anthropic's own cookbook warns that the model still converges on Space Grotesk across generations. The rule: **never ship the font the last three generations shipped, and never pick a font because it is the known good Google Fonts pick.**

**T3. Serif-italic accent word (P1).** 'The *modern* way to ship.' A single hero word in italic serif inside a sans headline is a recognizable instant-editorial move. Accenting one word via italic, bold or color is called out as among the commonest tells of a generated page.

**T4. Gradient-filled headline text (P0).** background-clip:text with magenta to purple to cyan on the H1 or on one word. Also common on big metrics. Weakens contrast and legibility.

**T5. Reflexive eyebrow label above every heading (P1/P2).** A tiny, tracked-out, ALL-CAPS line above each H2 ('FEATURES', 'HOW IT WORKS', 'PRICING'). Often in a lilac or accent color. Seen on nearly every dark SaaS page.

**T6. Monospace as the 'technical' costume (P1).** JetBrains Mono or IBM Plex Mono for copyright lines, captions, buttons, nav, tags and labels to signal 'developer'. Mono is correct for actual data (timestamps, hashes, code, tabular figures). Spread over non-code text it is a costume.

**T7. The '//' and '>' prefix, terminal chrome (P1).** '// features', '> run demo', '$ get-started' added whenever anything technical is mentioned. Typically arrives with the brainstorm, not the brief.

**T8. Numbered markers on non-sequences (P2).** '01 / 02 / 03' above cards that have no order. Allowed only when the content really is a sequence (and then a plain number is enough).

**T9. One label treatment on everything (P1).** The same tracked ALL-CAPS (or mono) used for the eyebrow, the button text, the figure numbers, the nav action and the footer colophon. It reads as a template, not a voice.

**T10. Flat hierarchy (P1).** Three or more font sizes with a max/min ratio under 2x; weights all 400 to 600. Nothing is emphasized because everything is.

**T11. Crushed or wide tracking (P2).** Display tracking tighter than -0.05em; body copy with letter-spacing above 0.05em; all-caps long passages.

**T12. Oversized or ragged headlines (P2).** A 40+ character headline at 72px+, orphaned last words, four-line headlines, forced line breaks with \<br>, a narrow floating subtitle.

**T13. Letterspaced serif wordmark (P2).** The 'luxury' logo: brand name in all-caps Cormorant/Didot with wide tracking and nothing else.

**T14. Tiny body text and fine print (P1).** Body under 14px, labels at 9 to 11px, gray on dark. Looks refined; reads as unreadable.

### 3.2 Examples

The slop (every line is a default):

```css
body { font-family: Inter, system-ui, sans-serif; background: #0b0b0f; color: #9ca3af; }
h1 { font-size: 4.5rem; font-weight: 800; letter-spacing: -0.05em;
     background: linear-gradient(135deg, #6366f1, #a855f7);
     -webkit-background-clip: text; color: transparent; }
.eyebrow { text-transform: uppercase; letter-spacing: .2em; font-size: 12px; color: #a78bfa; }
.label::before { content: '// '; font-family: 'JetBrains Mono', monospace; }
```

Slop headlines in the wild (all from the same template): 'The *modern* way to manage projects', 'Build faster. Ship smarter.', '// the future of work', 'FEATURES' above 'Everything you need to scale'.

### 3.3 Do instead

1. **Choose type from the brief, not from reputation.** Ask what the product is made of. A transit tool borrows from station signage (a humanist or signage grotesque with tabular numerals). A legal tool sets a book serif at 18px with real small caps. A pharmacy inventory uses a condensed grotesque for dense tables. A field-recording app might use a typewriter-adjacent face because its artifacts are logs.
2. **Pair on contrast axes.** Display plus mono; serif plus geometric sans; condensed plus wide; a variable font across weights. High contrast is interesting; two similar sans-serifs are not a pairing.
3. **Use extremes.** Weight 100/200 against 800/900, not 400 against 600. Size jumps of 3x or more between display and body, not 1.5x.
4. **Set a scale.** One ratio (about 1.25 for apps, 1.333 for editorial), six sizes at most, used consistently. Body 16px or larger. Measure 60 to 80 characters. Line-height 1.5 to 1.7 for body, 1.05 to 1.2 for display.
5. **Roles, not decoration.** Display for headlines and the wordmark; text face for reading; mono only for data. Different roles get different treatments; cut labels that add nothing.
6. **Details that signal care.** Tabular figures in tables, real curly quotes and apostrophes, proper hyphenation, optical sizes, no orphans (text-wrap: balance on headings, pretty on paragraphs).
7. **Licensing is a decision too.** Distinctive sites license or self-host real faces (grotesques like Neue Haas, Aktiv, Soehne, GT America, Untitled Sans; serifs like Tiempos, GT Sectra) and pair them with a neutral workhorse. If you must stay free, still choose by the brief and document why.
8. **Write the reason in the stylesheet.** A comment beside each font token with one sentence on why it is there. If you cannot write the sentence, it is a default.

A decision-grade type block (names are placeholders for the product's own choice):

```css
:root {
  --font-display: 'YourDisplayFace', 'Georgia', serif;   /* why: evokes the product's artifacts */
  --font-text: 'YourTextFace', 'Helvetica Neue', sans-serif;
  --font-data: 'YourDataFace', ui-monospace, monospace;  /* data only */
  --step-0: 1rem; --step-1: 1.25rem; --step-2: 1.563rem; --step-3: 1.953rem; --step-5: 3.05rem; --step-7: 4.77rem;
}
h1 { font-family: var(--font-display); font-weight: 200; font-size: var(--step-7); line-height: 1.02; text-wrap: balance; }
body { font-family: var(--font-text); font-size: var(--step-0); line-height: 1.6; max-width: 68ch; }
table td { font-family: var(--font-data); font-variant-numeric: tabular-nums; }
```

## Part 4: Color, gradient, dark mode, glow and contrast

Color is where the feedback loop is loudest. If you remember one rule: **a color must be there because of something true about the product, not because it is the color the model reaches for when nobody is steering.**

### 4.1 Tells (what to refuse)

**C1. The purple/indigo-to-blue diagonal gradient (P0).** linear-gradient(135deg, #6366f1, #a855f7) or similar on the hero, a button, a card, a glow blob or the headline text. The canonical tell. A purple brand with a purple logo gets a pass; an anonymous dashboard whose only color is this gradient does not.

**C2. 'VibeCode purple' primary buttons and links (P0/P1).** Indigo/violet (roughly HSL 240 to 295 degrees, mid-high saturation) on every filled CTA. Tailwind indigo-500/600 and shadcn violet are the origin.

**C3. Permanent dark mode (P1).** A dark page chosen because dark 'looks modern/technical', paired with medium-gray body text and ALL-CAPS section labels. The most common single reflex. Defaulting to light 'for safety' is the inverse retreat: both skip the decision.

**C4. The cool blue-charcoal dark base (P1).** A slate-indigo ink around #0c0e15, a slightly bluer panel and a lilac/periwinkle accent used 'sparingly'. It is the night-mode twin of the purple gradient: nobody chose it, the theme just defaulted.

**C5. Neon on dark with glowing borders (P0/P1).** Cyan or violet accents, glowing card edges, an animated accent-glow background. The v0/Cursor signature.

**C6. Colored glows, aurora blobs and inner-glow badges (P1).** box-shadow with 24px+ blur in a saturated color under buttons and cards; blurred radial or conic gradient 'orbs' behind the hero; pills lit from inside; a pulsing glow ring behind a status dot. Cut-off glows (clipped by overflow:hidden into a hard line) are the dead giveaway.

**C7. Rainbow vomit (P1).** Many unrelated colors with no semantic role: blue card, green card, orange card, pink card, because 'there is some distinction in fields'. Ignores the 60-30-10 discipline.

**C8. The timid evenly-spread palette (P0/P1).** Several colors at similar weight with no dominant and no sharp accent. Intentional brands do the opposite: one dominant color carries the page, an accent punctuates it.

**C9. Gradients everywhere (P1).** Five or more elements with gradient fills: button, card, avatar, pill, divider, background wash, pre-footer slab. A gradient on a big number 'for impact'.

**C10. Gray on color (P1).** Neutral mid-gray text on a chromatic background looks washed out. Use a darker shade of the background hue, or near-white.

**C11. Pure #000 or #fff with no tint (P2).** Harsh, flat, no depth. Tint neutrals toward the brand hue.

**C12. Barely-passing or failing contrast (P1).** Generated dark themes routinely ship body text that fails WCAG AA (4.5:1 body, 3:1 large). Thin gray text on dark is the usual culprit.

**C13. Untouched shadcn zinc/slate and Tailwind blue-600 (P0/P1).** The framework-level tell: the starter was deployed without theming.

**C14. Wave-2 palettes (P1).** Cream background near #F4F1EA with a high-contrast serif and a terracotta/clay accent near #D97757; near-black (#0B0B0B/#111) with one acid-green or vermilion accent; broadsheet hairlines. Legitimate for some briefs, but defaults when unchosen. See Part 12.

**C15. Pastel rainbow accents and mesh gradients (P1).** Soft multi-hue blobs as 'friendly' atmosphere.

**C16. Red/green deltas as the only color logic (P2).** Every KPI card with a green up-arrow or red down-arrow and nothing else expressing meaning (also fails color-blind users).

### 4.2 Examples

The slop palette:

```css
:root { --bg:#0b0b0f; --card:rgba(255,255,255,.04); --border:rgba(255,255,255,.1);
  --primary:#6366f1; --accent:#a855f7; --text:#9ca3af; }
.hero { background: radial-gradient(60% 50% at 50% 0%, rgba(99,102,241,.35), transparent); }
.btn-primary { background: linear-gradient(135deg,#6366f1,#a855f7); box-shadow: 0 0 40px rgba(139,92,246,.5); }
```

Slop in prose form (descriptions to refuse): 'dark navy page with a violet-to-blue glow behind the headline', 'glassmorphic cards with a subtle purple border', 'soft pastel gradient from lavender to sky', 'neon cyan accents on charcoal', 'cream background with terracotta buttons and a serif headline' (when nothing about the product asked for it).

### 4.3 Do instead

1. **Pick a color strategy before picking colors.**
   - *Restrained:* tinted neutrals plus one accent at 10% or less (tools, dashboards, documentation).
   - *Committed:* one saturated color carries 30 to 60% of the surface (brand-led pages).
   - *Full palette:* three or four named colors each with a role (data-heavy, playful, editorial).
   - *Drenched:* the surface itself is the color (campaigns, posters, event pages).
2. **Derive the palette from the product's materials.** Freight software: safety orange, asphalt, reflective white. A pharmacy tool: blister-pack silver, clinical green, label red. A brewing app: kettle copper and hop green on warm gray. A seismology tool: chart-paper red grid on white with ink black traces. A retention-analytics page: the cohort table's own color ramp becomes the only palette, the hero and the layout.
3. **Name every color and its job.** 4 to 6 tokens: ground, surface, ink, muted ink, accent, signal. Define in OKLCH or HSL ramps with CSS variables; ban arbitrary hex values in components.
4. **60-30-10.** 60% ground, 30% secondary, 10% accent. The accent is rare enough to mean something.
5. **Tint your neutrals.** Move black and white a few percent toward the brand hue (for example oklch(14% 0.01 250) instead of #000).
6. **If you want a gradient, make it a decision.** Tonal within one hue, or a duotone built from the brand's two real colors, used boldly in one place or not at all. No indigo-to-violet by default.
7. **Dark mode is a design, not a filter.** Choose the ground (warm near-black, green-black, oxblood, deep ink), a real text color at AA or better, and an accent that means something. Separate surfaces with lightness steps, not 10% white borders.
8. **Atmosphere without glow.** Depth from layered tonal surfaces, real textures (paper, grain, ruled lines, photo), and contextual patterns that match the subject. No colored shadow theater.
9. **Measure contrast, do not eyeball it.** Use APCA targets: Lc 75 or more for body text, 45 or more for large or bold text, 30 or more for non-text UI (icons, borders). WCAG 4.5:1 and 3:1 as the floor. Text over images or gradients needs a semi-transparent scrim that guarantees the value.
10. **Express meaning with more than hue.** Pair color with a label, icon or position so state survives color blindness.

Committed-palette tokens (example for a freight product):

```css
:root {
  --ground: oklch(97% 0.008 85);      /* paperwork white, tinted warm */
  --ink: oklch(22% 0.02 260);         /* asphalt */
  --ink-muted: oklch(45% 0.02 260);
  --accent: oklch(70% 0.19 55);       /* safety orange, used for the ONE primary action per view */
  --signal-ok: oklch(55% 0.13 150);
  --signal-stop: oklch(50% 0.2 27);
}
```

## Part 5: Layout and page-composition tells

The composition tells are the strongest evidence of a missing decision, because the skeleton is chosen before the content is considered. The research phrase for it: **structure chosen before content.**

### 5.1 Tells (what to refuse)

**L1. The centered hero template (P0).** Pill badge, then a 56 to 72px centered H1, then a gray subhead, then two buttons side by side ('Get started' with an arrow, plus a ghost 'Learn more' or 'See how it works'). Centering alone is not the tell; the combination is.

**L2. Three identical icon-topped feature cards (P0).** Same height, same padding, small icon on top, short title, one line of text. In a row of three (or a grid of six).

**L3. Bento grid as the reflex composition (P1).** A mixed-span rounded-card wall used because it is trendy and not because the tiles genuinely differ in importance.

**L4. The stat / social-proof strip (P1).** '10K+ users, 99.9% uptime, 4.9 stars' in a band. Round numbers, often for a product with no users. Hollow proof.

**L5. Numbered 1-2-3 'How it works' (P2).** Three big numerals with a sentence each, regardless of whether the process is ordered.

**L6. The default page shell (P1).** Every section wrapped in container mx-auto max-w-7xl px-4, nothing else. One width, centered, forever.

**L7. Three-tier pricing with a 'Most Popular' ring (P1).** Free / Pro / Enterprise; middle card scaled or ringed, a pill floating on its top edge, a checkmark feature list, a glowing primary button.

**L8. The four-column footer (P1).** Four equal link columns, a newsletter input, a row of social icons, whether or not those links exist.

**L9. Logo soup (P1).** A grayscale 'Trusted by teams at' strip with invented or generic logos.

**L10. The testimonial card (P1).** Large quote-mark glyph, centered quote with a fake-but-impressive metric ('velocity jumped 32%'), gradient-initials avatar, 'VP Engineering, Northwind Labs'.

**L11. Generic FAQ accordion (P2).** 'Frequently asked questions' with 3 to 6 invented questions ('Is my data secure?', 'Can I cancel anytime?').

**L12. The pre-footer CTA slab (P1).** A wide rounded box with a gradient, a centered 'Ready to get started?' headline, 'No credit card required', and two buttons.

**L13. The canned page order (P0).** Hero, logo strip, 3 feature cards, 1-2-3 steps, testimonials, 3-tier pricing, FAQ, CTA slab, footer, shipped as-is.

**L14. The split hero (P1).** Text column left (kicker, big headline with one emphasized word, subline, two buttons, a stat row under a hairline); framed visual card right (crude illustration with a caption and a floating tag pinned to a corner). Same skeleton for a photographer, a restaurant and a real-estate firm with only the colors changed.

**L15. Everything centered (P1).** Every text element center-aligned; no asymmetry; no left edge for the eye.

**L16. Identical section rhythm (P1).** Each section is H2 + subhead + grid. Nothing varies in width, density or shape, so nothing is emphasized.

**L17. The glassy sticky nav (P2).** Logo left, four links, 'Sign in' ghost, 'Get started' primary, backdrop-blur over scrolling content; sometimes a floating pill navbar.

**L18. Product screenshot in a fake browser frame (P1).** A dashboard mock with fake data under the hero, with a glow behind it.

**L19. Red X / green check comparison table (P2).** Us vs 'Others' with ticks and crosses.

**L20. Scroll hijacking and scroll-jacked storytelling (P1).** Pinned sections and custom scroll physics that break back, find-in-page and reduced motion.

### 5.2 What the slop looks like (as a wireframe)

```text
[ logo ]  Features  Pricing  Docs  Blog     [Sign in] [Get started]

              ( New: v2 is here )
         The modern way to ship faster
   Supercharge your workflow with our powerful platform.
        [ Get started -> ]  [ Learn more ]

        Trusted by teams at  (logo)(logo)(logo)(logo)

  [icon]            [icon]            [icon]
  Fast              Secure            Scalable
  One line.         One line.         One line.

  10K+ users     99.9% uptime     4.9 stars
  1 Sign up   2 Connect   3 Ship
  ( quote card with avatar )
  Free | Pro (Most Popular) | Enterprise
  FAQ accordion
  [ gradient slab: Ready to get started? ]
  footer x4 columns
```

If your layout can be drawn as this wireframe with the logo swapped, it is slop.

### 5.3 Do instead

1. **Lead with the most characteristic thing in the product's world.** The hero should be something only this product could have: the product itself running, a live artifact, a real dataset, a specimen, a before/after, a single bold claim in type, or evidence-first proof.
2. **Hero alternatives:** type-led poster; product-as-hero with a real interactive demo; data-as-hero (the cohort table, the timetable, the ledger); object-as-hero (a photographed or rendered real object); evidence-first (one specific, true metric with a source); editorial grid; long-form narrative opener; specimen sheet; receipt or ticket metaphor.
3. **Feature alternatives:** prose with inline emphasis; one large showcase plus smaller supporting points; alternating text-and-visual rows; an index or table; an annotated screenshot of a real state; a real demo. If a grid is right, vary tile size and density so it does not read as a template.
4. **Break symmetry on purpose.** Left-aligned hero with an asymmetric visual; an oversized type-led hero; a split layout; an editorial grid where content sits off-center; let one element be dramatically larger than the rest.
5. **Vary container width by section role.** Some content full-bleed, some narrow and editorial. Width is a tool, not a constant.
6. **One layout primitive, repeated.** Pick one strong primitive (a ledger row, a timeline rail, a poster block, a table) and repeat it until it becomes the site's visual signature, instead of seven card types and three stat banners.
7. **Pricing follows the real offer.** Two plans, one table, one plan plus add-ons, or an honest 'talk to us'. Earn any highlight with design, not a default ring.
8. **Build the footer from what exists.** Two columns and a line is often enough. No newsletter box unless it is real.
9. **Cut sections that carry no real content.** Delete the logo strip, stat strip, FAQ and testimonials if you do not have true ones. An empty or short page is better than an invented one.
10. **Order as an argument.** Sequence sections by what the visitor must believe next, not by a template.

Anti-example to alternative (landing page for a ferry timetable app):

- Slop: centered hero 'Never miss a ferry again', three cards (Real-time, Reliable, Beautiful), 4.9-star strip.
- Better: the page opens on the next three departures from the visitor's nearest terminal, set in the timetable's own typography, with the tide-and-delay data shown as a line directly under it; the 'features' are three annotated real states of the app; the only social proof is one named harbor master's sentence.

## Part 6: Component and surface tells

**The kitchen-sink card** is the clearest slop signature: one rounded card stacking an icon in a tinted tile, a category pill, a row of tag pills, a hairline divider, a big price and a glowy 'Add' button with a bottom shadow. No single piece is wrong; piling them all in one card is.

### 6.1 Tells (what to refuse)

**K1. Untouched shadcn/ui defaults (P0).** zinc/slate base, default --radius, unstyled Card/Button/Badge. The deployed starter.

**K2. rounded-2xl + shadow-lg + p-6 on everything (P1).** Identical radius, padding and soft shadow flatten hierarchy into a template. Also: soft rgba(0,0,0,.1) shadow on every surface.

**K3. Colored left or top border-accent cards (P1).** A 3 to 4px colored stripe on the edge of a rounded card or blockquote. Usually purple, blue or gradient. The border clashes with the radius. Reliable enough that designers call it the AI equivalent of em-dashes.

**K4. Cardocalypse, nested cards (P1).** Cards inside cards inside cards, each with its own padding, border and shadow. Every block boxed.

**K5. Glassmorphism and backdrop-blur by reflex (P1).** Frosted translucent cards and nav on a flat background with nothing to refract; blur banding; glow bleeding below the element; blur and shadow that visibly pop on hover. A bad blur is worse than none.

**K6. Icon in a rounded-square tile above a heading (P1).** The universal feature-card shape. Also: icon containers larger than the content they introduce.

**K7. Hairline light borders on every box (P2).** 1px white at 10% on dark, or gray on light, around every card, stat tile and countdown box, often with an inner highlight.

**K8. The universal hover-lift (P2).** translateY(-4px), an even shadow bloom and a glowing accent border applied to every card, whatever the card is.

**K9. The default CTA button pair (P1).** Gradient or indigo primary with an arrow icon and a glow, next to an outlined ghost secondary at the same medium radius. Plus pill-shaped everything (buttons, inputs, tags, all rounded-full).

**K10. Pill badges and chips as decoration (P1/P2).** 'New', 'Beta', 'Now in public beta', the eyebrow pill above the H1, floating tag pills pinned to images ('28C and clear'), tag-pill rows on every card.

**K11. Pulsing and meaningless status badges (P1).** A pulsing dot with 'Active' on a student ID that is never inactive; an 'Active student' badge on a profile; a 'Verified' tick that no API call verified; 'Live', 'Online', 'Ready to help' indicators with no state behind them. If the opposite state cannot exist, the badge carries no information.

**K12. Gradient-circle initials avatars and DiceBear/boring avatars (P1).** Two letters on a blue-to-purple circle standing in for a photo.

**K13. Fake window props (P1).** A faux macOS window with red/yellow/green traffic-light dots and a mock UI (kanban columns, avatars, status pills); a faux code window with a 'quickstart.ts' tab, JetBrains Mono, purple keywords, green strings and a made-up SDK call.

**K14. Floating, bobbing cards (P1).** Small cards layered over a hero that bob on a loop, with parallax or hover lift. Decorative motion with no purpose.

**K15. The accent-bar card and hero metric layout (P1).** A dark box with one bright line down an edge holding an icon, a big number and a caption; or 'big number, small label, three supporting stats, gradient accent'. Used everywhere, trusted nowhere.

**K16. Decorative sparklines (P1).** Tiny charts that look sophisticated and convey nothing. If the data matters, give it room, axes and units.

**K17. Modals by reflex (P1).** Complex settings crammed into a modal with its own scroll bar and three columns. If it needs that much room, it needs a page.

**K18. Fake urgency widgets (P1).** DAYS/HRS/MIN/SEC countdown boxes with nothing actually ending.

**K19. Whack-a-mole settings toggles (P1).** A toggle that triggers a full-screen repaint on every flip; a long list of toggles with identical hierarchy and no grouping.

**K20. Missing component states (P1).** Hover that does nothing; buttons that snap with no transition; forms with no focus, error, required, disabled or loading state; no visible keyboard focus.

### 6.2 Example: the slop card and the redesigned one

Slop:

```html
<div class='rounded-2xl border border-white/10 bg-white/5 p-6 shadow-lg backdrop-blur-xl hover:-translate-y-1 hover:border-indigo-500/50 hover:shadow-indigo-500/20 transition'>
  <div class='mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-500/10'><Zap class='text-indigo-400' /></div>
  <span class='rounded-full bg-indigo-500/10 px-2 py-1 text-xs uppercase tracking-widest text-indigo-300'>New</span>
  <h3 class='mt-3 text-xl font-semibold'>Lightning fast</h3>
  <p class='mt-2 text-gray-400'>Experience blazing performance with our cutting-edge engine.</p>
</div>
```

Better: no card at all. A row in an index, separated by whitespace and one rule:

```html
<li class='feature-row'>
  <h3>Cold start under 40 ms</h3>
  <p>Measured on the same 512 MB instance across 10,000 invocations; method and raw numbers linked.</p>
  <a href='/benchmarks'>See the run</a>
</li>
```

The fix removes the icon tile, the pill, the glow, the blur and the adjectives, and replaces the claim with a checkable fact.

### 6.3 Do instead

1. **Separate surfaces in this order and stop as soon as it reads:** whitespace; a 3 to 5% background lightness shift; soft elevation; and only then a border (never a flat gray line around everything).
2. **Use radius and elevation to express hierarchy.** Vary radius by element role (inputs, buttons, panels, overlays). Let some surfaces be flat, some sharp. Reserve strong shadows for things that genuinely float (menus, dialogs).
3. **Use rows, lists and tables where content is tabular.** Do not box what does not need a box.
4. **Reserve accent stripes for real semantic state** (an error row, a selected item), never for decoration.
5. **Use glass only where layering is real** (a nav over scrolling content, an overlay that should show what is behind it) and make it flawless; otherwise use a solid surface with a considered color.
6. **Make badges carry state.** A status pill must map to a distinct state that can actually occur; otherwise delete it.
7. **Photographs or initials on a flat, real color for avatars;** or no avatars.
8. **Style buttons with intent.** One primary action per view; secondary as a text link; distinct hover, active, focus-visible and disabled states; radius that matches the direction (sharp, soft or pill) and not the preset.
9. **Theme the library before shipping.** Change base color, radius, shadows and type in the tokens and restyle the components you use most.
10. **Design the full state matrix per component:** default, hover, focus-visible, active, disabled, loading, error, success, empty, long text, and RTL or narrow width where it applies.

## Part 7: Iconography, imagery and illustration tells

### 7.1 Tells (what to refuse)

**I1. The same thin-stroke icon library on every project (P1).** Lucide (Sparkles, Zap, Rocket, Shield, Lock, Globe, Layers, BarChart, ArrowRight) or Heroicons used unedited. The uniform stroke is a giveaway when it shows up everywhere.

**I2. Emoji as icons, bullets and nav labels (P0).** Rocket, sparkles, light bulb, fire, target, chart emojis on feature cards, headings, sidebar items and buttons. Sidebar or nav items prefixed with emoji are a measured Show HN tell.

**I3. Sparkles = 'AI' (P1).** A sparkle glyph or Sparkles icon on every AI feature, button, badge and empty state. It now reads as 'AI' almost exclusively and signals category, not function.

**I4. Icon in a colored rounded tile (P1).** A big icon centered in a soft-colored square or circle used as a feature bullet or hero visual.

**I5. Gradient placeholders where images should be (P1).** Gradient boxes, abstract floating circles, dashed orbit rings, a 'plate' of gradient balls, mock bar charts drawn from rounded divs. Hand-faked decorative graphics that look low-effort because they are placeholders.

**I6. Generic stock-photo energy (P1).** Handshakes, laptop-on-desk, diverse-team-around-table, smiling headset person; or no real imagery at all.

**I7. The AI-art look (P1).** 3D glass spheres, holographic or chromatic blobs, iridescent mesh gradients, isometric pastel illustration packs.

**I8. Backgrounds as wallpaper (P1).** Faint grid or graph-paper lines with a radial fade-out, dot grids, noise overlays and aurora blobs added whenever a plain background feels empty.

**I9. Fake proof assets (P1).** Invented logos in 'Trusted by', a mocked dashboard screenshot with fake data in a browser frame, invented avatars with stock faces.

**I10. Arrows welded to every link (P2).** A trailing '->' or arrow icon on every CTA, link, card and pagination control.

**I11. Inconsistent or model-drawn SVG icons (P1).** Mixed stroke widths, mismatched sizes, optical misalignment against text, or icon stroke thickness that does not match adjacent text weight (the 'wispy' look). Tiny sidebar icons in AI desktop apps that clash with native OS icon sizing.

**I12. Misaligned loose elements (P1).** SVGs, ASCII art or elements not in a box are almost always a few pixels off their intended alignment (list markers against timetable rows, icons against baselines).

### 7.2 Examples

Slop: a pricing card whose bullet list is three green checkmark emojis; a hero where a purple orb sits behind a floating card; a team section with DiceBear robots; a features section whose icons are Zap, Shield, Globe in indigo tiles.

Better: the product's real artifacts as imagery (an actual timetable, a scanned ledger page, the real UI in a real, ugly state), a labeled diagram drawn from real data, a single commissioned or bespoke illustration style used consistently, or typographic ornaments and rules as the only decoration.

### 7.3 Do instead

1. **Prefer text labels to icons.** Use an icon only where it is universal or encodes a real category, and keep the label.
2. **If you use icons, make them a system:** one family, deliberate stroke weight matched to the text weight, a 16/20/24 size grid, optical alignment, consistent corner treatment. Or draw a small custom set that belongs to the product.
3. **Never use emoji as UI.** Use them only where the user writes them (messages, reactions).
4. **Use real imagery.** Product shots, photography of the actual subject, screenshots of real states, real people with consent, diagrams generated from real data. If you have none, use none, rather than gradient placeholders.
5. **Bespoke over generic.** When an agent has image or video tools, generate or commission assets that carry the product's point of view (a custom hero video, food photography for a restaurant) instead of stock fillers.
6. **Texture from material.** Paper grain, ledger ruling, halftone, blueprint lines, tape, scanlines: only when the subject calls for it, not as a universal glow substitute.
7. **Always provide alt text and dimensions** (prevents layout shift and tells screen readers what the image is for).
8. **Check alignment visually.** Render, zoom to 200%, and align icons to text baselines and cap-height.

## Part 8: Motion and interaction tells

Motion is where AI interfaces give themselves away, because the model sprinkles it rather than choreographs it. Anthropic's aesthetics guidance puts the principle plainly: one well-orchestrated page load with staggered reveals creates more delight than scattered micro-interactions.

### 8.1 Tells (what to refuse)

**M1. The same fade-up on every section (P2).** Every block fades in and rises 20px on scroll with the identical duration and easing. The default AOS/Framer reveal.

**M2. Uniform hover:scale-105 and hover-lift (P2).** Every card, button and image grows or rises on hover regardless of role.

**M3. Bouncing buttons, wiggling icons, floating badges (P1).** 'When in doubt, animate everything': motion without meaning.

**M4. Count-up statistics (P2).** Numbers that tick up from zero when scrolled into view, especially for invented metrics.

**M5. Marquees and parallax by reflex (P2).** An infinite logo marquee; background layers drifting at different speeds.

**M6. Animated gradient and aurora backgrounds (P1).** Slowly morphing blobs behind the hero; continuous GPU cost for atmosphere.

**M7. Looping float/bob animations (P1).** Small cards or 3D objects bobbing forever.

**M8. Pulsing dots and halo rings (P1).** Pulsing 'live' indicators and glow rings with no real live state.

**M9. Scattered micro-interactions (P2).** Many small, unrelated hover and click effects with different easings and durations and no coherent motion language.

**M10. Wrong easing and janky properties (P2).** ease-in on UI transitions; elastic/bounce on serious tools; animating width, height, top or left instead of transform and opacity; layout thrash.

**M11. Cursor-follow spotlights and glow-on-hover borders (P1).** A radial highlight tracking the pointer across cards.

**M12. Typewriter and scramble-text hero (P2).** Text that types itself or glitches in for 'techy' effect.

**M13. Scroll hijacking (P1).** Pinned sections, custom scroll physics, horizontal-scroll stories that break back-button, find-in-page and keyboard scrolling.

**M14. No reduced-motion support (P1).** Ignoring prefers-reduced-motion entirely.

**M15. Fake loading (P1).** A spinner on a timer, a progress bar not tied to progress, random numbers ticking to look 'real-time'.

**M16. The opposite failure: no motion at all (P2).** Buttons that snap with no transition, no feedback on press, state changes that pop. The page looks fine but feels dead.

### 8.2 Example

Slop:

```jsx
<motion.section initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
  <motion.div whileHover={{ scale: 1.05 }} className='card'>...</motion.div>   {/* on every element */}
</motion.section>
```

Better: a defined motion language and one choreographed moment.

```css
:root { --dur-1: 120ms; --dur-2: 200ms; --dur-3: 320ms;
        --ease-out: cubic-bezier(.2,.7,.2,1); --ease-spring: cubic-bezier(.34,1.3,.64,1); }
.hero > * { opacity: 0; transform: translateY(8px); animation: rise var(--dur-3) var(--ease-out) forwards; }
.hero > *:nth-child(1) { animation-delay: 0ms; } .hero > *:nth-child(2) { animation-delay: 80ms; }
.hero > *:nth-child(3) { animation-delay: 160ms; }
@keyframes rise { to { opacity: 1; transform: none; } }
button:active { transform: translateY(1px); transition: transform var(--dur-1) var(--ease-out); }
@media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }
```

### 8.3 Do instead

1. **Define a motion language** before animating: two or three durations, two easings, one rule for when things move. Reuse it.
2. **Choreograph one or two high-impact moments** (a staggered page load, one meaningful state transition) rather than decorating every block.
3. **Move in response to the user.** Press, drag, open, close, reorder, undo. Motion should explain a state change.
4. **Animate transform and opacity only.** Keep UI transitions at or under about 300ms; ease-out for entrances, never ease-in for UI; spring only where physical.
5. **Respect prefers-reduced-motion** and offer a calm mode in dense tools.
6. **Honest loading.** Skeletons that match the final shape; real progress; no fake real-time.
7. **What is legitimately good:** streaming text and a shimmering 'thinking' indicator for genuinely unpredictable async work, skeleton loaders, and press feedback. These solve real status-communication problems. The slop is decorative repetition, not the technique.

## Part 9: App, dashboard and product-UI slop

Landing pages get the attention, but the same defaults dominate generated tools. The deepest app-level tell: **the model treats every screen like a landing page rather than a functional tool.**

### 9.1 Tells (what to refuse)

**A1. The 'Welcome back, John' greeting (P1).** 'Welcome back, John 👋 Here's what's happening with your business today.' Occasionally with sparkles. It pushes the real content down and says nothing.

**A2. The KPI-card row (P0/P1).** Four cards: icon, label, big number, green/red percent delta, sparkline. 'Total Revenue $128,427 +12.4% vs last month.' 'Conversion Rate 3.42%.' Hero KPI card in a gradient.

**A3. Placeholder people, companies and numbers presented as real (P0).** John Doe, Jane Smith, Sarah Chen, Alex, Emma Watson, Acme Corp, Nexus, Northwind Labs, Enterprise Corp, john@example.com, '$2,450.00 from Enterprise Corp', '10,000% ROI', '500,000 founders'. Even invented specifics like 'Sarah Chen scored 85/100 - High intent buyer identified'.

**A4. The invented activity feed (P1).** 'New deployment successful', 'Payment received', 'New team member joined', 'Bug report resolved', 'Database backup done (42.8 GB)', '2 min ago', 'Customer churn risk detected'. Events that no system emitted.

**A5. The stock dashboard composition (P1).** Revenue line chart, traffic-sources donut, 'Top products' list, 'Recent activity' feed, monthly/weekly/yearly toggle, always in that order.

**A6. The stock shell (P1).** Left sidebar of 6 to 8 icon+label items, workspace switcher on top, an 'Upgrade to Pro' card at the bottom; top bar with 'Search... Cmd+K', a bell with a red dot and an avatar.

**A7. The bolted-on AI assistant (P0/P1).** A chat panel or bubble bottom-right: 'AI Assistant, Online - Ready to help', suggested-prompt chips ('Analyze sales trends', 'Generate lead insights', 'Schedule follow-ups'), a sparkle icon. Invented 'AI insights' cards.

**A8. Meaningless status and trust badges (P1).** Pulsing 'Active', 'Verified', 'Live', 'Secure', 'Pro' on things that cannot be otherwise. 'Active student' badges. Shield icons next to nothing.

**A9. The stock settings page (P2).** Tabs: Profile, Account, Notifications, Billing, Security; a column of toggles; a red 'Danger zone' box.

**A10. Generic empty states (P1).** A large illustration and 'No data yet' with no explanation of what will appear or the one action to take.

**A11. Marketing language inside tools (P1).** H1 plus a gray hype subtitle on a settings or table screen: 'Experience the power of task management with our cutting-edge intuitive interface.' 'Supercharge your workflow.'

**A12. Cosmetic data tables (P1).** Avatar column, colored status pills, a kebab menu on every row, pagination, but no real sort, filter, density, column control, export or keyboard support.

**A13. Charts that decorate (P1).** Gradient area under a line; donut for things that are not parts of a whole; 3D pies; rainbow series; no axes, units or direct labels; tooltips as the only way to read values; decorative sparklines.

**A14. Fake real-time (P1).** setInterval random numbers, pulsing 'live' dots, an updating counter that is not connected to data.

**A15. The reflexive wizard and nag (P2).** A 3-step onboarding with progress dots and confetti; 'Upgrade' prompts; 'Success!' toasts after every action; 'Are you sure?' confirmations for reversible actions.

**A16. Mobile app defaults (P1).** Five-icon bottom tab bar, floating action button, oversized radii on every card, onboarding carousel of three illustrated slides, Material or Cupertino defaults with only a primary color swapped.

**A17. The AI chat wall (P1).** Chat UI where replies are markdown walls: H2 headers, emoji bullets, bold everywhere, a closing offer; a history sidebar identical to every other chat product.

**A18. Redundant information and chat-context leakage (P1).** Text added because something in the prompt produced it: 'Built with Hugo. Written from Neovim', 'One campus. One app.', 'Built with modern C++20 features' in READMEs.

### 9.2 Example: what the user actually needs vs what slop gives

Brief: 'an ops dashboard for our nightly data jobs'.

Slop output (all invented): 'Welcome back, Alex! Here's what's happening today.' Four KPI cards (Total Jobs 1,284 +12.4%; Success Rate 98.7%; Avg Duration 4m 12s; Active Pipelines 24), a purple line chart, a donut chart of 'Job Status', a Recent Activity feed, an AI Assistant bubble.

Designed output: the first screen answers the user's real question, 'which jobs failed since 06:00 and why'.

```text
FAILED SINCE 06:00 (3)
  orders_etl      failed 06:41   exit 137 (OOM) at step 4/7     last good: yesterday 06:12   [Re-run] [Logs]
  ads_sync        failed 07:03   401 from provider API          token expired 2h ago          [Rotate token]
  billing_export  failed 07:15   schema drift: column 'plan_id' [Diff] [Open ticket]
SLOW (>2x median) (2)       RUNNING (5)       OK (41)  [collapsed]
```

No greeting, no decoration; failures sorted by consequence; each row carries cause, recency of last good run and the next action; healthy things collapse out of the way.

### 9.3 Do instead

1. **Start from the job to be done.** Who is the user, what decision do they make in this screen, how often, under what pressure? Lead with what needs attention, not a greeting.
2. **Never invent data.** Use real data, an honest empty state, or clearly labeled sample data with an indicator that it is sample. If unknown, show a dash and say why.
3. **Name things in the user's vocabulary** (jobs, shipments, cases, patients), not generic SaaS nouns.
4. **Choose density deliberately.** Compact for pro tools, airy for reading; make it a token. Tables with real sorting, filtering, column control and keyboard support.
5. **Chart by question.** Trend over time is a line; comparison is bars; parts of a whole is stacked or a single donut with few slices; distribution is a histogram. Label directly, show axes and units, annotate the one event that explains the line, keep color for meaning.
6. **Status is information or it is deleted.** Every badge must map to a state that can truly occur, and the state should come with the next action.
7. **Empty states do work.** Say what will appear here and offer the one next action. Errors say what happened and how to fix it.
8. **Navigation by tasks, not features.** Fewer items, named by what people do; a real default landing view.
9. **Prefer undo to confirmation,** inline editing to modals, a page to a modal that scrolls.
10. **AI inside a product belongs where it changes the work.** If there is an assistant, make it do something specific (explain this failure, draft this reply from this record), expose its sources and uncertainty, and do not give it a sparkle and a chat bubble by default.
11. **Mobile is a design, not a shrink.** Decide the primary action, the thumb zone, and what disappears.

## Part 10: Copy and microcopy slop

Copy is slop's other half. One vendor analysis of AI-generated landing pages reported that 74% of generated headlines contained at least one of 'streamline', 'empower', 'unlock', 'revolutionize' or 'seamless', and that default AI copy scored below the human average for specificity (treat the exact figures as vendor data, but the direction matches every other source). The same median that produces the purple gradient produces the sentence 'Elevate your workflow'.

### 10.1 The banned lexicon (never use unless quoting)

- **Verbs:** elevate, unleash, unlock, supercharge, empower, revolutionize, leverage, harness, utilize, streamline, foster, embark, delve, showcase, underscore, navigate (metaphorical), transform, reimagine.
- **Adjectives:** seamless, robust, powerful, cutting-edge, next-generation, game-changing, intuitive, innovative, comprehensive, best-in-class, world-class, industry-leading, holistic, meticulous, dynamic, groundbreaking.
- **Nouns:** journey, ecosystem, landscape, tapestry, realm, paradigm, synergy, cornerstone, catalyst, solution, platform (as filler), experience (as filler).
- **Intensifiers and hedges:** truly, really, incredibly, simply, just, effortlessly, potentially, can help you.
- **Openers and transitions:** 'In today's fast-paced world', 'It's worth noting', 'Let's dive in', 'Imagine a world where', 'Say goodbye to X, hello to Y', 'Whether you're X or Y', 'Moreover', 'Furthermore'.

### 10.2 Structural tells

| Pattern | Slop example | Why it reads as AI |
| --- | --- | --- |
| Em dash density | 'Fast — reliable — secure' | Humans average about one per 500 words; models use about one per 50 to 80. Ban em and en dashes; use periods, commas, colons or parentheses. |
| 'Not just X, it is Y' | 'Not just a task manager, a command center for your team.' | Manufactured antithesis. |
| Tricolon of abstractions | 'Faster. Smarter. Simpler.' | Rule-of-three rhythm with no information. |
| Hype subtitle under every H1 | 'Experience the power of ...with our cutting-edge intuitive interface.' | Same grammar on every page. |
| Aphorism formulas | 'Symmetry is the language of trust.' | Sounds profound, claims nothing. |
| Staccato drama | 'No friction. No clutter. No compromise.' | Fragments with no content. |
| Rhetorical opener | 'Tired of juggling five tools?' | Fake-candid setup. |
| Emoji-led bullet headers | '🚀 Launch fast  ⚡ Scale easily' | Reads like a product launch post. |
| Title Case Headings | 'Everything You Need To Scale' | Template cadence. |
| Bold overuse and inline-header lists | '**Performance:** Performance improved' | Restates the heading. |
| Feature dump | Bulleted features, no outcomes | Mirrors the average landing page. |
| Hedged claims | 'Helps you potentially improve your workflow' | Careful copy does not convert. |
| Invented proof | '10,000+ happy users', '4.9 stars', '32% velocity jump', 'Trusted by 500,000 founders' | No source behind it. |
| Prompt leakage | 'Built with Hugo. Written from Neovim.' | Context from the chat leaked into the product. |

### 10.3 Microcopy tells

- **Buttons:** 'Get Started', 'Learn more', 'Submit', 'Click here', 'Continue', 'Next' with no result named. Arrow glyphs welded to every one.
- **Errors:** 'Oops! Something went wrong.' 'An error occurred.' Blame ('You entered an invalid email').
- **Success:** 'Success!' toasts after every action.
- **Empty states:** 'No data.' 'Nothing here yet.' with a sad illustration.
- **Confirmations:** 'Are you sure?' for a reversible action; destructive confirmations that do not state the consequence.
- **Redundant UX writing:** a label, a sublabel, a helper text and a hint saying the same thing in slightly different words.
- **Greetings and filler:** 'Welcome to your Dashboard, \[Name\] ✨', 'Hope you're having a great day'.

### 10.4 Before and after

| Slop | Better | What changed |
| --- | --- | --- |
| Elevate your workflow with seamless task management | Every task has one owner and one due date. Overdue ones go red. | Specific mechanism instead of adjectives. |
| Get Started | Create your first invoice | Button names the result. |
| Oops! Something went wrong. | Could not save: the file is over 10 MB. Compress it or split it. | Cause plus fix. |
| Success! | Invoice 1042 sent to ana@... | States what happened. |
| No data yet | No shipments yet. Import a CSV or connect your carrier account. | One next action, what will appear. |
| Trusted by 10,000+ teams | 214 clinics use it daily (list, with permission) | True, checkable, specific. |
| Are you sure? | Delete 12 contacts? This cannot be undone. \[Delete 12\] \[Keep\] | Consequence stated, verbs on buttons. |
| Welcome back, John! Here's what's happening today. | 3 jobs failed since 06:00 | Starts with the information. |
| Supercharge your team's productivity | Stand-up notes written from your Slack threads | A thing you can picture. |
| Not just a CRM, a revenue engine | A CRM that logs the call for you | Drops the antithesis. |

### 10.5 Do instead

1. **Specificity rule.** Every claim carries a number, a name, a mechanism or a constraint. If a sentence could sit on a competitor's page unchanged, rewrite it.
2. **The billboard test.** Would the line survive alone on a billboard and still mean something? Can the reader repeat the promise after one read?
3. **Name the reader's moment.** A lawyer at 7pm who just lost twenty minutes hunting for one deposition line wants 'find any line by searching', not 'unlock productivity'.
4. **Say it once.** One label, one helper if needed. No sublabel that repeats the label.
5. **Plain words.** use, not utilize; help, not facilitate. Sentence case. Vary sentence length. Fragments are fine only when they carry information ('Ships in seconds.').
6. **Have an opinion.** Copy without a position is wallpaper. A brand voice says things a PR team would flag.
7. **No fabrication.** Never invent product facts, metrics, testimonials, customer names or logos. If unknown, omit the element or mark it clearly as a placeholder to be replaced before launch.
8. **Keep the chat out of the product.** Do not echo the build context (the editor you use, the framework, the manager's slogan) into visible copy.
9. **Microcopy by moment.** Errors reach someone whose task just broke: what went wrong, then how to fix it, no blame. Empty states reach someone new: sell the single next action. Destructive confirmations: state the consequence and name the verb. Success: state the object and result.

## Part 11: UX, functional and accessibility slop beyond aesthetics

The visual tells are the cheap ones. The costly slop is behavioral: interfaces that look finished but only implement the happy path. A 2026 benchmark named the gap **Design Theater**: plausible, confident design rationales with little relationship to the implementation. Across 120 interfaces from five generative UI tools, over 25% of stated rationales were not implemented (34% for functional requirements), and tools implemented 6% or fewer of the functional UX principles in four of five cases. Near-universal collapse showed up on visibility of system status, user control and freedom, and error prevention and recovery.

### 11.1 Tells (what to refuse)

**F1. Rationale without implementation (P0).** The summary claims keyboard navigation, accessible contrast, responsive layout and error handling; the code has none. Never claim a design property you did not build and verify.

**F2. Happy path only (P0).** The UI renders the successful, populated, English, desktop, single-user case and nothing else.

**F3. Missing states (P1).** No empty, loading, error, success, disabled, offline, partial-data or permission-denied states. No hover, focus-visible, active or selected states. No long-text, many-items, zero-items or very-large-number cases.

**F4. Contrast failures (P1).** Gray on dark, gray on color, thin type under 4.5:1; text over images or gradients with no scrim; placeholder text used as the only label.

**F5. Keyboard and focus failures (P1).** outline:none with no replacement; focus order that does not match visual order; custom dropdowns and modals with no keyboard support, no focus trap and no Escape; clickable divs.

**F6. Tiny targets (P1).** Hit areas under 44px (24px minimum in WCAG 2.2); icon buttons with no accessible name; icons-only navigation.

**F7. Semantic and ARIA gaps (P1).** Skipped heading levels (h1 then h3), missing landmarks, inputs without labels or autocomplete attributes, icon buttons with no aria-label, images without alt.

**F8. Layout shift and jank (P2).** Images and embeds with no dimensions; fonts that swap with a flash; sticky bars covering content; animating layout properties.

**F9. Responsive breakage (P1).** Breaks at 375px; no mobile menu (the desktop nav simply overflows); horizontal scrolling on the body; fixed heights; tables that cannot scroll; text too small on phones; 100vh bugs and unsafe-area overlap.

**F10. Form slop (P1).** Placeholder as label; validation only on submit with a generic banner; no inline error association; no required indicator; no input types or inputmode; password fields that block paste.

**F11. Fake interactivity (P1).** Buttons that do nothing; links to #; sort icons that do not sort; search boxes that do not search; 'Coming soon' controls; settings that do not persist; fake 'Save' states.

**F12. Destructive actions with no undo (P1).** Delete without confirmation of consequence or an undo window.

**F13. Dark patterns by template (P1).** Fake countdowns, 'Only 2 left', pre-checked upsells, a 'Most Popular' ring on a plan chosen for margin, hidden cancel paths.

**F14. Inconsistency drift (P1).** Button height, radius, spacing and color differ page to page; page seven does not match page one because each was generated from scratch.

**F15. Locale and format blindness (P2).** Hardcoded US dates, 12-hour times, currency symbols and decimal separators; no tabular numerals; text that breaks on German-length strings or RTL.

**F16. Performance by decoration (P2).** Heavy backdrop-blur, large animated blobs, un-optimized hero images and several font families all on the critical path.

**F17. Unrequested information (P1).** Extra badges, taglines, footers and microcopy that nobody asked for and nobody needs.

### 11.2 Do instead

1. **Implement what you claim, and verify it.** After building, render at 375px and 1440px, tab through the page, zoom to 200%, throw bad data at forms, and screenshot the result. State what you tested and what you did not.
2. **Build a state matrix per screen and per component** and implement every cell: empty, loading, error, success, disabled, selected, focused, hovered, pressed, partial, offline, long text, large numbers, permission-denied.
3. **Meet accessibility floors:** contrast (4.5:1 body, 3:1 large and UI), visible focus-visible styles, full keyboard operation, semantic HTML first and ARIA second, labels on every control, 44px touch targets, prefers-reduced-motion, text resizing to 200%, proper heading outline, alt text.
4. **Use the web platform's affordances:** correct input types and autocomplete values, native dialog and details where possible, color-scheme and theme-color meta for dark mode, tabular-nums for tables, curly quotes, image width/height, text-wrap balance.
5. **Show system status and keep user control:** progress for long operations, undo instead of confirm, cancel, drafts preserved, errors preventable by constraints.
6. **Keep consistency in a file, not in your head.** Save the design direction and tokens to DESIGN.md (or a system file) and read it before every page so new screens do not drift.
7. **Close the loop with a browser.** Use an automated browser to open the app, screenshot, click through flows, read console logs, then fix what is broken before reporting done. The model cannot design well if it cannot see the result.
8. **Run deterministic checks** (axe, Lighthouse, a slop scanner, the grep patterns in Part 15) as a gate, not a suggestion.

## Part 12: Second-wave traps (the replacement defaults)

**The whack-a-mole rule: banning one default makes the model fall into the next most probable look for a page that is trying not to look generated.** Swapping Inter for Fraunces, indigo for terracotta, or dark navy for near-black is not a decision. It is the second default. Anthropic's own cookbook admits it: even when told to avoid generic choices, the model still converges on Space Grotesk across generations.

### 12.1 The second-wave clusters

As catalogued in Anthropic's frontend-design guidance (September 2026 update, as reported by several sources), AI design 'right now clusters around':

| Cluster | Signature | Why it reads as AI |
| --- | --- | --- |
| Warm editorial | Cream background near #F4F1EA, high-contrast serif display, terracotta/clay accent near #D97757 | It is the palette of the Claude interface itself; on someone else's brief it signals the tool, not the brand |
| Dark signal | Near-black (#0B0B0B, #111, #08090b) with a single bright acid-green or vermilion accent, mono labels | The standard answer to 'make it look technical' |
| Broadsheet cosplay | Hairline rules, zero border radius, dense newspaper columns, numbered kickers | Editorial styling applied to content that is not editorial |
| SaaS card kit | Identical rounded cards, one radius everywhere, the same soft shadow, decorative gradient washes | Structure chosen before content |
| Template chrome | Tracked ALL-CAPS eyebrow over every heading, middle-dot meta strings (A . B . C), mono face for small labels, arrow welded to every link, 01/02/03 markers | Decoration that appears whatever the subject is |

Additional second-wave looks to watch for:

- **Neo-brutalism that looks the same every time:** thick black borders, hard offset shadows, Space Mono, yellow/pink blocks. Fine once; identical across every generated 'brutalist' site.
- **Terminal/hacker:** green on black, scanlines, '$' prompts, '//' labels, JetBrains Mono everywhere.
- **Luxury editorial:** Cormorant or Didone serif, gold, letterspaced all-caps wordmark, the split hero skeleton.
- **Swiss minimal:** Helvetica clone, one red dot, a grid overlay, the same 12-column hero.
- **Retro-futurism:** chrome gradients, perspective grids, purple/teal.
- **Soft clay 3D and pastel blobs:** rounded 3D icons, pastel mesh backgrounds.
- **Liquid glass and aurora:** the glassmorphism of wave 1, relabeled.
- **Grain + serif + cream:** the 'indie product' look as a reflex.

### 12.2 The category-reflex check (two altitudes)

1. **Altitude one:** could the theme and palette be guessed from the product category alone? ('Fintech' = navy and teal; 'wellness' = sage and cream; 'AI tool' = violet and glow; 'developer tool' = near-black and green.) If yes, rework.
2. **Altitude two:** could it be guessed from the category plus the obvious anti-reference? ('Fintech, but not navy' = warm cream and serif.) If yes, that is the trap one tier deeper. Rework again.
3. **Acceptance:** the direction must be traceable to something particular to this product, its users, its materials or its history.

### 12.3 Over-correction failure modes

- **The sterile result:** a filter without a direction produces a plain, correct, forgettable page. 'A sterile result means the direction was missing, not that the filter failed.'
- **The costume swap:** replacing the old costume with the new trendy costume and calling it done.
- **Stripping meaningful affordances:** deleting a real status pill, a real icon, a real gradient because it appears on a ban list.
- **Letting tests pin defaults:** once snapshot tests lock a label style, a default starts to look like a decision. Ask each locked-in element for its reason.
- **Cross-conversation instructions:** 'do not converge across generations' cannot work because the model has no memory between sessions. Use per-generation constraints (a named direction, a locked theme) instead.
- **Banning a technique instead of a reflex:** slop is the unexamined use of an element, not the element.

### 12.4 The decision-log technique

For every visible design decision, write one sentence on why it exists, next to the token or component (or in DESIGN.md). Anything with no sentence is a default and goes. A real example of the method: a site author audited his own site after a slop checklist went viral, sorted elements into 'has a written reason' (dark ground, fonts, accent from a deliberate terminal brief) and 'arrived with a brainstorm and looked finished' (a '//' before every label, tracked caps, numbered markers, middle dots, arrows after links), and removed the second group.

## Part 13: The positive protocol (what to do instead)

Every serious source separates two jobs. **A filter removes defaults; a direction supplies the look.** A filter alone gives a sterile page; a direction alone still carries defaults. Do both, in this order: direction first, then filter.

### 13.1 Step 1: brief intake (answer before designing)

1. Who is the user and what are they doing in the 10 seconds before they open this?
2. What is the one job this screen/page does?
3. What is the product made of? (Its data, artifacts, files, instruments, forms, jargon, physical objects.)
4. What is the single most characteristic thing in the product's world?
5. What would a competitor never do?
6. What tone: and name two real references to blend (not clone).
7. Density: compact, medium, airy? Reading or scanning?
8. Light, dark, or both, and why?
9. Constraints: brand assets, accessibility needs, devices, performance budget, languages.
10. What are the three things this design refuses to do?

### 13.2 Step 2: derive the direction from the product's materials

| Product | Its materials | What they suggest |
| --- | --- | --- |
| Retention analytics | The cohort table, heat-map ramps | The table is the hero and the layout; its color ramp is the only palette |
| Ferry timetable | Station signage, departure boards, tide charts | Signage grotesque with tabular numerals; board-like rows; a tide line under the next departure |
| Legal notes | Deposition transcripts, exhibit stickers | Book serif at 18px, line numbers in the margin, exhibit-label tags |
| Pharmacy inventory | Blister packs, shelf labels, barcodes | Condensed type, dense tables, label-red alerts, barcode-style rules |
| Seed library | Seed packets, hand-written labels | Packet illustrations, label typography, scanned handwriting for notes |
| Debate or decision tool | Ledgers of arguments, scorecards, tallies | Two-column ledger rows, ruled score tallies, evidence citations as footnotes |
| Field-recording app | Logs, waveforms, tape labels | Waveform as the primary visual, log-style rows, tape-label type |

### 13.3 Step 3: write the token plan (required before code)

```markdown
# Design direction
Visual thesis: one sentence (what it feels like and why, tied to the product).
Colors (4-6, named, hex, role): Ground / Surface / Ink / Muted ink / Accent / Signal.
Typefaces (2, named, role): Display for ... ; Text for ... ; (Data only if real data).
Layout concept: the one primitive that repeats (ledger row, poster block, rail, table).
Signature move: the one memorable thing (a live board, an oversized figure, a margin of notes).
Motion language: durations, easing, the one orchestrated moment.
Refusals: three things this design will not do.
Default-check: which defaults might I be drifting toward, and how is each avoided?
```

Then review the plan: 'Which parts read like the generic default I would produce for any similar page?' Revise those parts before writing code.

### 13.4 Step 4: aesthetic families (pick one, then remix with a second)

Naming one family helps; remixing two anchors helps more ('Linear's typographic discipline plus a print magazine's editorial color') because the model has to triangulate instead of defaulting. Families to choose from, each with its directives:

| Family | Directives |
| --- | --- |
| Editorial minimalism | Serif display, strict grid, restrained color, pull quotes, generous measure |
| Data-dense pro | Compact type, tabular figures, tinted neutral ground, small radius, high information density |
| Terminal-core (earned) | Monospaced data, command-line affordances that really exist, phosphor or paper tones chosen by the product |
| Cinematic dark (earned) | Real photography, deep ink ground, one warm light source, sparse type |
| Playful color | Saturated flat color blocks, chunky type, big shapes, deliberate asymmetry |
| Swiss/International | Grid-first, flush-left ragged-right, one typeface family, color as signal only |
| Industrial/utility | Signage typography, hazard and safety palettes, labels and stencils |
| Warm editorial (only if the brief asks) | Paper tones, serif, ink, but with a non-default accent and real content structure |
| Craft/analog | Paper grain, ruled lines, stamps, hand-lettering, scanned artifacts |
| Neo-brutalism (only if asked) | Raw system type, visible borders, no radius, loud flat color; commit fully and avoid the stock yellow-and-pink |

Vary the family across projects and generations. Treat 'I always do X' as a defect.

### 13.5 Step 5: pick one layout primitive and one signature move

- **Primitive examples:** the ledger row; the timeline rail; the poster block; the specimen sheet; the board; the margin-notes column; the full-bleed photograph with a caption strip.
- **Signature move examples:** an oversized figure that is the page's only hero; a live, real-data strip at the top; a marginalia column; a single color that appears only on the primary action; a typographic scale with one deliberately enormous step.
- Repeat the primitive across the page until it becomes the visual signature, rather than mixing seven card styles.

### 13.6 Step 6: DESIGN.md, the memory file

For anything with more than one screen, write the direction into a DESIGN.md at the project root and have the agent read it before every page. Typical sections: visual theme; color tokens; typography rules; component styles; layout principles; depth and elevation; do's and don'ts; responsive behavior; a closing **rejection clause** listing what the agent must not do (paste Part 1 here). Without it, each new page is regenerated from scratch and drifts back toward the defaults. Sanity test: generate the same page under two or three different design systems; if they look like one template in different colors, the system is not being applied.

### 13.7 Step 7: how to prompt (what actually works)

- **Name the dimension, not the adjective.** 'Premium' and 'modern' resolve to the centroid. 'Display serif at weight 200 and 7rem, ink on warm paper, a single orange action color' does not.
- **Provide goal, layout, content and constraints,** in that order, plus a reference blend.
- **Use tokens,** never 'make it look nice': 'semantic tokens only' beats hex codes scattered across components.
- **Constrain before generating, not after.** Fixing backward means fighting the defaults (change the typeface and the sizes drift back to display-scale Inter; swap the purple and it returns through a hover gradient).
- **Ask for variants as text first.** Have the model propose three divergent design specs (with an honest 'typicality' guess for each), pick a low-typicality one, then generate. Separating direction from implementation is a practical way to explore alternatives without raising temperature on code.
- **Image-first is an option** (generate a reference composition with an image model, then implement it), but it can swap one converged look (code minimalism) for another (genre pastiche). Treat it as a source of direction, not a cure.
- **Iterate with targeted edits** (tweaks, comments) rather than re-prompting the whole design.
- **Make the model state its decisions** at the end, so a human can argue with them.

## Part 14: Worked before/after examples

Each example shows what the median model produces for a bare prompt, then what a made decision looks like. Use them as pattern-matching exemplars.

### Example 1: Landing page for an invoice-reminder tool

**Bare prompt:** 'Build a landing page for a SaaS that chases late invoices.'

**Median output (slop):** dark navy background with a violet-to-blue glow; pill badge 'New: AI-powered reminders'; centered H1 'Get paid faster, effortlessly' with 'faster' in gradient text; subhead 'Supercharge your cash flow with seamless automation'; buttons 'Get Started' and 'Learn more'; three icon cards (Automated, Secure, Insightful); stat strip '10K+ users, 99.9% uptime'; 1-2-3 steps; three-tier pricing with a ringed middle; FAQ; gradient CTA slab; Inter throughout.

**Made decisions (direction):**

- Thesis: the page behaves like the thing it sells, a polite but firm reminder. The hero is a real sample overdue notice, set large, with the amount, the days late and the escalation ladder printed on it.
- Colors: invoice paper white tinted warm, ink black, a single stamp red used only for the overdue amount and the primary action, a muted green for 'paid'.
- Type: a plain, sturdy text face for body; a stencil or typewriter-adjacent display used only for the stamp-like numerals.
- Layout: a left-aligned column that reads like a document; a ledger-row layout for the three reminder stages (day 3, day 10, day 21) with the actual wording of each email; a single table for pricing.
- Proof: one named customer sentence with permission, or none. No stat strip.
- CTA: 'Send your first reminder (free for 5 invoices)'.

### Example 2: Analytics dashboard for a small online shop

**Median output:** 'Welcome back, Sarah! 👋' + four KPI cards (Revenue $24,580 +12.5%; Orders 1,234; Customers 856; Conversion 3.2%) + purple area chart + 'Top Products' + 'Recent Orders' with avatars and colored pills + AI assistant bubble.

**Made decisions:**

- First screen is the question the owner has every morning: 'what do I need to ship or fix today?' A list of unfulfilled orders by age, stock-outs on best sellers, and failed payments, each with its action.
- A single revenue line with last year as a faint comparison and annotations on the days something changed (a promo, a stock-out). Axes and units visible.
- Numbers shown with absolute values and the period; deltas only when the comparison is meaningful, with the base shown.
- No greeting, no avatars, no assistant bubble. An 'Explain this dip' action on the chart that cites the orders and sessions it used.

### Example 3: Pricing page

**Median output:** Free / Pro / Enterprise cards, middle ringed 'Most Popular', checkmark lists of identical features, gradient buttons, monthly/annual toggle with a 'Save 20%' pill.

**Made decisions:** two plans because there are two real plans. A single comparison table grouped by what the customer actually asks ('How many seats', 'How long we keep your data', 'Who answers support, and how fast'). Prices stated with what happens at the limit. One line on what is not included. One primary action per plan with a verb: 'Start the 14-day trial', 'Talk to a person'.

### Example 4: AI chat product

**Median output:** left history sidebar, centered empty state with a sparkle logo and 'How can I help you today?', four suggested-prompt chips, assistant replies as markdown walls with emoji bullets, a shimmer 'Thinking...', an input with a gradient send button.

**Made decisions:** the empty state shows the product's actual scope and a recent real item (the last three documents it can read) instead of generic chips. Replies are plain prose with citations to the passages used and a visible 'what I did not check'. The input shows what context is attached (files, selection, date range) as removable chips that carry real state. Streaming and a status line ('Reading 14 pages... 6 of 14') for long work; no sparkle iconography.

### Example 5: Mobile habit/plant-care app

**Median output:** five-icon bottom bar, large rounded cards in pastel gradients, an emoji for each plant, a floating '+' button, an onboarding carousel of three illustrations, confetti on completion.

**Made decisions:** the home screen is today's list: which plants are thirsty, in the order you walk past them. A photograph you took of each plant replaces the emoji. One primary action (mark watered) as a large swipe or tap target in the thumb zone. No onboarding carousel: the first plant is added in-context. Completion is a quiet state change, not confetti.

### Example 6: Photographer portfolio

**Median output:** the split hero (Cormorant headline with one italic word, uppercase kicker, 'View work' ghost button, framed image with a floating caption chip), a masonry grid with hover-scale, a letterspaced serif wordmark.

**Made decisions:** the photographs run full-bleed with captions in the photographer's own words and EXIF-like facts that are real (place, date, lens). Navigation is two words. Type is whatever suits the work (contact-sheet numerals, handwritten notes scanned from the contact sheets). No hover-scale; a click opens the sequence in full resolution.

### Example 7: Login screen

**Median output:** centered glass card, gradient logo tile, 'Welcome back 👋', Google and GitHub buttons with brand icons, 'Forgot password?', 'Don't have an account? Sign up', purple glow behind the card.

**Made decisions:** a plain, left-aligned form with a clear label on each field (not placeholder-as-label), the correct input types and autocomplete values, show-password control, an error that names the problem and the fix ('That email has no account here. Create one or try another address'), and the one primary action. The brand shows up as type, color and a single sentence about what the user is returning to ('3 jobs are waiting for review').

### Example 8: Settings page

**Median output:** tabs (Profile, Account, Notifications, Billing, Security), a long column of toggles with identical weight, a red 'Danger zone' card.

**Made decisions:** group by what the user wants to accomplish (change who gets alerts, change who can edit, export my data), search across settings, show the effect of each setting in plain words ('You will get an email when a job fails for more than 10 minutes'), save per section with an undo toast, and place destructive actions behind a consequence-stating confirmation, not just a red border.
