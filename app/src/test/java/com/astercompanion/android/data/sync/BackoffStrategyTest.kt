package com.astercompanion.android.data.sync

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.util.Random

class BackoffStrategyTest {

    @Test
    fun testAttemptZeroProducesZeroDelay() {
        val strategy = BackoffStrategy()
        assertEquals(0L, strategy.calculateDelayMs(0))
        assertEquals(0L, strategy.calculateDelayMs(-1))
    }

    @Test
    fun testExponentialGrowthWithJitterBounds() {
        val strategy = BackoffStrategy(
            initialDelayMs = 1000L,
            maxDelayMs = 16000L,
            factor = 2.0
        )

        // For attempt 1: cap is min(16000, 1000 * 2^0) = 1000. Delay must be between 500 and 1000 ms.
        for (i in 1..20) {
            val delay1 = strategy.calculateDelayMs(1)
            assertTrue("Delay $delay1 should be >= 500 and <= 1000", delay1 in 500..1000)
        }

        // For attempt 2: cap is min(16000, 1000 * 2^1) = 2000. Delay between 500 and 2000 ms.
        for (i in 1..20) {
            val delay2 = strategy.calculateDelayMs(2)
            assertTrue("Delay $delay2 should be >= 500 and <= 2000", delay2 in 500..2000)
        }

        // For attempt 10: cap is 16000 (maxDelay). Delay must never exceed maxDelayMs
        for (i in 1..50) {
            val delayMax = strategy.calculateDelayMs(10)
            assertTrue("Delay $delayMax must not exceed maxDelayMs 16000", delayMax <= 16000L)
            assertTrue("Delay $delayMax should be >= 500", delayMax >= 500L)
        }
    }
}
