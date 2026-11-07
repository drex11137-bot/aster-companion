package com.astercompanion.android.data.sync

import java.util.Random
import kotlin.math.min
import kotlin.math.pow

/**
 * Exponential backoff with full jitter strategy for network retries (PRD v1.1 §6.3).
 * Formula: delay = random_between(0, min(maxDelayMs, initialDelayMs * factor^attempt))
 */
class BackoffStrategy(
    val initialDelayMs: Long = 1000L,
    val maxDelayMs: Long = 30000L,
    val factor: Double = 2.0,
    private val random: Random = Random()
) {
    /**
     * Calculates the backoff delay in milliseconds for the given retry attempt (0-indexed).
     * Includes full jitter to prevent thundering herd problem.
     */
    fun calculateDelayMs(attempt: Int): Long {
        if (attempt <= 0) return 0L
        val calculatedDelay = initialDelayMs * factor.pow((attempt - 1).toDouble())
        val cappedDelay = min(maxDelayMs.toDouble(), calculatedDelay).toLong()
        if (cappedDelay <= 0L) return 0L

        // Full jitter: uniformly random between initialDelayMs/2 and cappedDelay
        val minJitter = initialDelayMs / 2
        return if (cappedDelay > minJitter) {
            minJitter + (random.nextDouble() * (cappedDelay - minJitter)).toLong()
        } else {
            (random.nextDouble() * cappedDelay).toLong()
        }
    }
}
