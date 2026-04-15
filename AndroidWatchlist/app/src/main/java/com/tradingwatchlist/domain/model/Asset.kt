package com.tradingwatchlist.domain.model

enum class Asset(
    val symbol: String,
    val displayName: String,
    val yahooSymbol: String
) {
    GOLD("GC=F", "Gold", "GC%3DF"),
    SILVER("SI=F", "Silver", "SI%3DF"),
    CRUDE_OIL("CL=F", "Crude Oil", "CL%3DF"),
    NATURAL_GAS("NG=F", "Natural Gas", "NG%3DF"),
    NASDAQ("NQ=F", "Nasdaq", "NQ%3DF");

    companion object {
        val ALL: List<Asset> = values().toList()

        fun fromSymbol(symbol: String): Asset? = ALL.find { it.symbol == symbol }
    }
}
