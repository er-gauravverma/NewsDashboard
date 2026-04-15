package com.tradingwatchlist.data.db

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "alerts")
data class AlertEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,

    @ColumnInfo(name = "asset_symbol")
    val assetSymbol: String,

    @ColumnInfo(name = "target_price")
    val targetPrice: Double,

    @ColumnInfo(name = "direction")
    val direction: String,       // "ABOVE" or "BELOW"

    @ColumnInfo(name = "is_active")
    val isActive: Boolean = true,

    @ColumnInfo(name = "created_at")
    val createdAt: Long = System.currentTimeMillis()
)
