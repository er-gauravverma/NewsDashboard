package com.tradingwatchlist.domain.model

enum class AlertDirection { ABOVE, BELOW }

data class PriceAlert(
    val id: Long = 0,
    val assetSymbol: String,
    val targetPrice: Double,
    val direction: AlertDirection,
    val isActive: Boolean = true,
    val createdAt: Long = System.currentTimeMillis()
)
