package com.tradingwatchlist.data.api.model

import com.google.gson.annotations.SerializedName

data class ChartResponse(
    @SerializedName("chart") val chart: ChartWrapper
)

data class ChartWrapper(
    @SerializedName("result") val result: List<ChartResult>?,
    @SerializedName("error") val error: Any?
)

data class ChartResult(
    @SerializedName("meta") val meta: ChartMeta,
    @SerializedName("timestamp") val timestamp: List<Long>?,
    @SerializedName("indicators") val indicators: IndicatorWrapper?
)

data class ChartMeta(
    @SerializedName("regularMarketPrice") val regularMarketPrice: Double,
    @SerializedName("chartPreviousClose") val chartPreviousClose: Double,
    @SerializedName("symbol") val symbol: String
)

data class IndicatorWrapper(
    @SerializedName("quote") val quote: List<QuoteData>?
)

data class QuoteData(
    @SerializedName("open") val open: List<Double?>?,
    @SerializedName("high") val high: List<Double?>?,
    @SerializedName("low") val low: List<Double?>?,
    @SerializedName("close") val close: List<Double?>?,
    @SerializedName("volume") val volume: List<Long?>?
)
