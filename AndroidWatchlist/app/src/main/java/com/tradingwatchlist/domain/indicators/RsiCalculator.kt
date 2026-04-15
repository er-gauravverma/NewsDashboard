package com.tradingwatchlist.domain.indicators

object RsiCalculator {

    /**
     * Compute RSI using Wilder's Smoothed Moving Average.
     *
     * @param closes List of closing prices, chronologically oldest-first.
     * @param period RSI period (default 14).
     * @return RSI value in range 0..100, or null if insufficient data (need at least period+1 points).
     */
    fun compute(closes: List<Double>, period: Int = 14): Double? {
        if (closes.size < period + 1) return null

        val changes = closes.zipWithNext { a, b -> b - a }

        // Initial average gain and loss over the first [period] changes
        var avgGain = changes.take(period).filter { it > 0.0 }.sum() / period
        var avgLoss = changes.take(period).filter { it < 0.0 }.sumOf { -it } / period

        // Wilder's smoothing for remaining changes
        for (i in period until changes.size) {
            val gain = if (changes[i] > 0) changes[i] else 0.0
            val loss = if (changes[i] < 0) -changes[i] else 0.0
            avgGain = (avgGain * (period - 1) + gain) / period
            avgLoss = (avgLoss * (period - 1) + loss) / period
        }

        if (avgLoss == 0.0) return 100.0
        val rs = avgGain / avgLoss
        return 100.0 - (100.0 / (1.0 + rs))
    }
}
