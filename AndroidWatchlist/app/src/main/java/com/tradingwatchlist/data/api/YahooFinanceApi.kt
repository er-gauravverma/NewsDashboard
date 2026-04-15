package com.tradingwatchlist.data.api

import com.tradingwatchlist.data.api.model.ChartResponse
import retrofit2.http.GET
import retrofit2.http.Path
import retrofit2.http.Query

interface YahooFinanceApi {

    /**
     * Fetch current price data.
     * Uses 1-minute interval with 1-day range to get the latest price.
     */
    @GET("v8/finance/chart/{symbol}")
    suspend fun getCurrentPrice(
        @Path("symbol", encoded = true) symbol: String,
        @Query("interval") interval: String = "1m",
        @Query("range") range: String = "1d"
    ): ChartResponse

    /**
     * Fetch 1Hr candles for the past 60 days.
     * Provides ~1,440 data points — sufficient for RSI-14 and SMA-200 calculation.
     */
    @GET("v8/finance/chart/{symbol}")
    suspend fun getHourlyCandles(
        @Path("symbol", encoded = true) symbol: String,
        @Query("interval") interval: String = "1h",
        @Query("range") range: String = "60d"
    ): ChartResponse
}
