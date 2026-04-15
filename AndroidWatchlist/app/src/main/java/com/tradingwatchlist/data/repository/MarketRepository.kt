package com.tradingwatchlist.data.repository

import com.tradingwatchlist.data.api.YahooFinanceApi
import com.tradingwatchlist.data.api.model.ChartResult
import com.tradingwatchlist.data.db.AlertDao
import com.tradingwatchlist.data.db.AlertEntity
import com.tradingwatchlist.domain.indicators.RsiCalculator
import com.tradingwatchlist.domain.indicators.SmaCalculator
import com.tradingwatchlist.domain.model.Asset
import com.tradingwatchlist.domain.model.AssetQuote
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

class MarketRepository(
    private val api: YahooFinanceApi,
    private val alertDao: AlertDao
) {
    private val _quotes = MutableStateFlow<Map<Asset, AssetQuote>>(emptyMap())
    val quotes: StateFlow<Map<Asset, AssetQuote>> = _quotes.asStateFlow()

    /**
     * Fetch the current price for all assets.
     * Called every 5 minutes by PriceUpdateReceiver and on manual refresh.
     */
    suspend fun refreshAllPrices(): Result<Unit> = runCatching {
        val newQuotes = _quotes.value.toMutableMap()
        for (asset in Asset.ALL) {
            try {
                val response = api.getCurrentPrice(asset.yahooSymbol)
                val result = response.chart.result?.firstOrNull() ?: continue
                val existing = newQuotes[asset]
                newQuotes[asset] = AssetQuote(
                    asset = asset,
                    currentPrice = result.meta.regularMarketPrice,
                    previousClose = result.meta.chartPreviousClose,
                    rsi14 = existing?.rsi14,
                    sma200 = existing?.sma200,
                    lastUpdated = System.currentTimeMillis()
                )
            } catch (e: Exception) {
                // Keep previous data for this asset if fetch fails
            }
        }
        _quotes.value = newQuotes
    }

    /**
     * Fetch 1Hr candles and compute RSI-14 and SMA-200 for all assets.
     * Called on app launch and every 30 minutes — not on every 5-min alarm.
     */
    suspend fun refreshIndicators(): Result<Unit> = runCatching {
        val updated = _quotes.value.toMutableMap()
        for (asset in Asset.ALL) {
            try {
                val response = api.getHourlyCandles(asset.yahooSymbol)
                val result = response.chart.result?.firstOrNull() ?: continue
                val closes = extractCloses(result)
                val rsi = RsiCalculator.compute(closes)
                val sma = SmaCalculator.compute(closes)
                val existing = updated[asset]
                updated[asset] = if (existing != null) {
                    existing.copy(rsi14 = rsi, sma200 = sma)
                } else {
                    AssetQuote(
                        asset = asset,
                        currentPrice = result.meta.regularMarketPrice,
                        previousClose = result.meta.chartPreviousClose,
                        rsi14 = rsi,
                        sma200 = sma,
                        lastUpdated = System.currentTimeMillis()
                    )
                }
            } catch (e: Exception) {
                // Keep previous indicators if fetch fails
            }
        }
        _quotes.value = updated
    }

    /**
     * Check all active alerts against current prices.
     * Deactivates triggered alerts and returns the list so notifications can be sent.
     */
    suspend fun checkAndFireAlerts(): List<Pair<AlertEntity, AssetQuote>> {
        val triggered = mutableListOf<Pair<AlertEntity, AssetQuote>>()
        val currentQuotes = _quotes.value
        for ((asset, quote) in currentQuotes) {
            val alerts = alertDao.getActiveAlertsForSymbol(asset.symbol)
            for (alert in alerts) {
                val shouldFire = when (alert.direction) {
                    "ABOVE" -> quote.currentPrice >= alert.targetPrice
                    "BELOW" -> quote.currentPrice <= alert.targetPrice
                    else -> false
                }
                if (shouldFire) {
                    alertDao.deactivateAlert(alert.id)
                    triggered.add(alert to quote)
                }
            }
        }
        return triggered
    }

    private fun extractCloses(result: ChartResult): List<Double> =
        result.indicators?.quote?.firstOrNull()
            ?.close?.filterNotNull()
            ?: emptyList()
}
