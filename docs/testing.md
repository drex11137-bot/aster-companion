# GAUGE: System Monitor — Test Strategy & Verification Architecture

In strict adherence to **GEMINI.md §5 ("Tests must prove behavior")** and `instruction.md`, GAUGE implements a rigorous, layered testing suite designed to prove correctness, prevent regressions, and verify arithmetic and serialization contracts without relying on fake passes or weakened assertions.

---

## 1. Test Architecture & Principles

### 1.1 Non-Trivial Behavioral Assertions
Every test in GAUGE answers four mandatory questions:
1. **User/Contract Behavior Established**: Does the test verify real arithmetic calculations, data serialization boundaries, or OS capability limits?
2. **Defect Rejected**: Would off-by-one errors, negative byte bugs, unescaped CSV quotes, or invalid JSON syntax cause the test to fail?
3. **State Transition & Invariant Check**: Does the test check actual state mutations (e.g. timestamp cutoff boundaries) rather than merely executing code paths?
4. **Meaningful Boundaries Tested**: Does the test verify zero-total bytes, division-by-zero, empty datasets, and special characters?

### 1.2 Zero-Weakening Rule
In accordance with GEMINI.md §5.4:
- Failing tests are **never** deleted or weakened.
- Matchers are strictly typed.
- Mocks are not used to simulate away the component under test.

---

## 2. Unit Test Inventory

The test suite resides in `app/src/test/java/com/androidactivity/guage/`:

### 2.1 Arithmetic & Telemetry Math (`core/MemoryMathTest.kt`)
- `testMemoryPercentageCalculation`: Tests exact formula `(used / total) * 100.0` with known byte values (8GB total, 2GB available = 75.0% pressure).
- `testZeroTotalBytesHandling`: Tests edge case where device reports 0 total bytes, ensuring no `ArithmeticException` (division by zero) or `NaN` is propagated.
- `testByteFormatting`: Verifies threshold boundary between MB and GB formatting (`500.0 MB` vs `2.00 GB`).
- `testDurationFormatting`: Verifies milliseconds conversion to human-readable strings (`45s`, `15m 30s`, `2h 10m`).

### 2.2 Retention Policy & Pruning (`data/RetentionPolicyTest.kt`)
- `testCutoffCalculationSevenDays`: Tests exact 7-day millisecond delta (`604,800,000 ms`) subtraction from epoch timestamp.
- `testCutoffCalculationThirtyDays`: Tests 30-day millisecond delta (`2,592,000,000 ms`).
- `testCutoffCalculationNinetyDays`: Tests 90-day millisecond delta (`7,776,000,000 ms`).

### 2.3 Streaming Exporter Service (`data/ExportServiceTest.kt`)
- `testExportToCsvWithEmptyList`: Verifies valid RFC 4180 CSV header generation when history is empty.
- `testExportToCsvWithSampleData`: Verifies field ordering, timestamp ISO-8601 UTC formatting, and quote escaping for comma-containing labels (`"RAM Usage, High"`).
- `testExportToJsonWithEmptyList`: Verifies valid JSON document structure (`app`, `version`, `export_timestamp`, `total_samples: 0`, `samples: []`).
- `testExportToJsonWithSampleData`: Verifies valid JSON serialization of metric values, units, extra JSON objects, and trailing comma suppression.

### 2.4 Data Models & Invariants (`core/TelemetryModelsTest.kt`)
- `testMemoryTelemetryModel`: Verifies `MemoryTelemetry` properties, `usedBytes` subtraction, and `isLowMemory` boolean flags.
- `testBatteryTelemetryModel`: Verifies charging state, voltage (mV), and temperature (°C) values.
- `testThermalTelemetryModel`: Verifies `ThermalStatus` enum mappings and headroom float boundaries.
- `testDeviceCapabilitiesAudit`: Verifies capability flags, guaranteeing truthful disclosure of restricted `/proc/stat` and per-app private memory.

---

## 3. Test Execution Command

To execute all unit tests with full output:
```bash
JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 ./gradlew testDebugUnitTest --no-daemon
```

Test reports and HTML traces are automatically generated at:
```text
app/build/reports/tests/testDebugUnitTest/index.html
```
