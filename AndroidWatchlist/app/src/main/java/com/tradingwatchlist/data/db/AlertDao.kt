package com.tradingwatchlist.data.db

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface AlertDao {

    @Query("SELECT * FROM alerts WHERE is_active = 1 ORDER BY created_at DESC")
    fun getActiveAlerts(): Flow<List<AlertEntity>>

    @Query("SELECT * FROM alerts WHERE is_active = 1")
    suspend fun getActiveAlertsList(): List<AlertEntity>

    @Query("SELECT * FROM alerts WHERE asset_symbol = :symbol AND is_active = 1")
    suspend fun getActiveAlertsForSymbol(symbol: String): List<AlertEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAlert(alert: AlertEntity): Long

    @Query("UPDATE alerts SET is_active = 0 WHERE id = :alertId")
    suspend fun deactivateAlert(alertId: Long)

    @Delete
    suspend fun deleteAlert(alert: AlertEntity)
}
