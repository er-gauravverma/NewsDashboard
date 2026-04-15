package com.tradingwatchlist.domain.model

data class AssetQuote(
    val asset: Asset,
    val currentPrice: Double,
    val previousClose: Double,
    val rsi14: Double? = null,
    val sma200: Double? = null,
    val lastUpdated: Long = System.currentTimeMillis()
) {
    val percentChange: Double
        get() = if (previousClose != 0.0)
            ((currentPrice - previousClose) / previousClose) * 100.0
        else 0.0

    val isAboveSma200: Boolean
        get() = sma200 != null && currentPrice > sma200
}
