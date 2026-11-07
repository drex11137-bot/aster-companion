# ADR-003: Jetpack Compose & Material 3 Technical UI Architecture

## Status
Accepted

## Context
Mobile telemetry interfaces require responsive, high-refresh-rate rendering without excessive CPU or GC churn. XML layouts with heavy nested view hierarchies introduce measurable layout overhead.

## Decision
GAUGE is built 100% with Jetpack Compose 1.5, Material 3, and custom Canvas-drawn instruments (`MemoryPressureDial`, `GaugeMascot`, `TrendChart`). All colors are strictly governed by an audited design system avoiding generic AI-slop palettes and the 8 forbidden hex colors.

## Consequences
- **Positive**: Declarative unidirectional data flow (UDF) via Kotlin Coroutine `StateFlow`, sub-millisecond dial animations, zero XML view bloat.
- **Trade-off**: Requires Compose Compiler 1.5.14 and Kotlin 1.9.24.
