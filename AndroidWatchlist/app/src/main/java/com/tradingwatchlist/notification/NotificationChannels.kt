package com.tradingwatchlist.notification

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context

object NotificationChannels {

    const val CHANNEL_ALERTS = "price_alerts"
    const val CHANNEL_LIVE_PRICE = "live_prices"

    fun createAll(context: Context) {
        val nm = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        // High-priority channel: fires when a price alert is triggered
        val alertsChannel = NotificationChannel(
            CHANNEL_ALERTS,
            "Price Alerts",
            NotificationManager.IMPORTANCE_HIGH
        ).apply {
            description = "Fires when an asset crosses your configured price target"
            enableVibration(true)
        }
        nm.createNotificationChannel(alertsChannel)

        // Low-priority channel: persistent price summary updated every 5 min
        val priceChannel = NotificationChannel(
            CHANNEL_LIVE_PRICE,
            "Price Updates",
            NotificationManager.IMPORTANCE_LOW
        ).apply {
            description = "Periodic price summary updated every 5 minutes"
        }
        nm.createNotificationChannel(priceChannel)
    }
}
