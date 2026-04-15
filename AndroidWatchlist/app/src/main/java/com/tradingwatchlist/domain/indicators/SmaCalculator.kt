package com.tradingwatchlist.domain.indicators

object SmaCalculator {

    /**
     * Compute Simple Moving Average over the last [period] values.
     *
     * @param closes List of closing prices, chronologically oldest-first.
     * @param period Number of periods (default 200).
     * @return SMA value, or null if insufficient data.
     */
    fun compute(closes: List<Double>, period: Int = 200): Double? {
        if (closes.size < period) return null
        return closes.takeLast(period).sum() / period
    }
}
