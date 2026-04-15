package com.tradingwatchlist.di

import android.content.Context
import com.tradingwatchlist.data.api.YahooFinanceApi
import com.tradingwatchlist.data.api.YahooFinanceService
import com.tradingwatchlist.data.db.AppDatabase
import com.tradingwatchlist.data.repository.AlertRepository
import com.tradingwatchlist.data.repository.MarketRepository

object ServiceLocator {

    @Volatile private var database: AppDatabase? = null
    @Volatile private var api: YahooFinanceApi? = null
    @Volatile private var marketRepo: MarketRepository? = null
    @Volatile private var alertRepo: AlertRepository? = null

    fun getDatabase(context: Context): AppDatabase =
        database ?: synchronized(this) {
            database ?: AppDatabase.getInstance(context).also { database = it }
        }

    fun getApi(): YahooFinanceApi =
        api ?: synchronized(this) {
            api ?: YahooFinanceService.create().also { api = it }
        }

    fun getMarketRepository(context: Context): MarketRepository =
        marketRepo ?: synchronized(this) {
            marketRepo ?: MarketRepository(
                api = getApi(),
                alertDao = getDatabase(context).alertDao()
            ).also { marketRepo = it }
        }

    fun getAlertRepository(context: Context): AlertRepository =
        alertRepo ?: synchronized(this) {
            alertRepo ?: AlertRepository(
                alertDao = getDatabase(context).alertDao()
            ).also { alertRepo = it }
        }
}
