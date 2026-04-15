package com.tradingwatchlist.data.repository

import com.tradingwatchlist.data.db.AlertDao
import com.tradingwatchlist.data.db.AlertEntity
import com.tradingwatchlist.domain.model.AlertDirection
import kotlinx.coroutines.flow.Flow

class AlertRepository(private val alertDao: AlertDao) {

    val activeAlerts: Flow<List<AlertEntity>> = alertDao.getActiveAlerts()

    suspend fun addAlert(
        assetSymbol: String,
        targetPrice: Double,
        direction: AlertDirection
    ): Long = alertDao.insertAlert(
        AlertEntity(
            assetSymbol = assetSymbol,
            targetPrice = targetPrice,
            direction = direction.name
        )
    )

    suspend fun deleteAlert(alert: AlertEntity) = alertDao.deleteAlert(alert)

    suspend fun deactivateAlert(alertId: Long) = alertDao.deactivateAlert(alertId)
}
