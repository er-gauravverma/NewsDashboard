package com.tradingwatchlist

import android.app.Application
import com.tradingwatchlist.background.AlarmScheduler
import com.tradingwatchlist.notification.NotificationChannels

class TradingWatchlistApp : Application() {

    override fun onCreate() {
        super.onCreate()
        NotificationChannels.createAll(this)
        AlarmScheduler.schedulePriceUpdateAlarm(this)
    }
}
