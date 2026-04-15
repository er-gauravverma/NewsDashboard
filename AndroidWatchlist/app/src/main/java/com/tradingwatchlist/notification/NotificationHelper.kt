package com.tradingwatchlist.notification

import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import com.tradingwatchlist.R
import com.tradingwatchlist.data.db.AlertEntity
import com.tradingwatchlist.domain.model.Asset
import com.tradingwatchlist.domain.model.AssetQuote
import com.tradingwatchlist.ui.watchlist.WatchlistActivity
import java.util.concurrent.atomic.AtomicInteger

object NotificationHelper {

    private val alertNotificationIdCounter = AtomicInteger(2000)
    private const val SUMMARY_NOTIFICATION_ID = 1001

    fun sendAlertNotification(
        context: Context,
        alert: AlertEntity,
        quote: AssetQuote
    ) {
        val directionWord = if (alert.direction == "ABOVE") "above" else "below"
        val title = "${quote.asset.displayName} Alert Triggered"
        val body = "Price ${quote.currentPrice.formatPrice()} crossed $directionWord " +
                "target ${alert.targetPrice.formatPrice()}"

        val tapIntent = Intent(context, WatchlistActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        }
        val tapPendingIntent = PendingIntent.getActivity(
            context, 0, tapIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(context, NotificationChannels.CHANNEL_ALERTS)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(title)
            .setContentText(body)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .setContentIntent(tapPendingIntent)
            .build()

        try {
            NotificationManagerCompat.from(context)
                .notify(alertNotificationIdCounter.incrementAndGet(), notification)
        } catch (e: SecurityException) {
            // POST_NOTIFICATIONS permission not granted — silently skip
        }
    }

    /**
     * Updates the persistent price summary notification (fixed ID 1001).
     * Shows current price and % change for each tracked asset.
     */
    fun updatePriceSummaryNotification(
        context: Context,
        quotes: Map<Asset, AssetQuote>
    ) {
        if (quotes.isEmpty()) return

        val lines = Asset.ALL.mapNotNull { quotes[it] }.joinToString("\n") { q ->
            val change = q.percentChange
            val arrow = if (change >= 0) "▲" else "▼"
            val rsiText = q.rsi14?.let { " | RSI ${it.toInt()}" } ?: ""
            "${q.asset.displayName}: ${q.currentPrice.formatPrice()} $arrow ${"%.2f".format(change)}%$rsiText"
        }

        val tapIntent = Intent(context, WatchlistActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        }
        val tapPendingIntent = PendingIntent.getActivity(
            context, 0, tapIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(context, NotificationChannels.CHANNEL_LIVE_PRICE)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle("Market Prices")
            .setStyle(NotificationCompat.BigTextStyle().bigText(lines))
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setOngoing(false)
            .setContentIntent(tapPendingIntent)
            .build()

        try {
            NotificationManagerCompat.from(context).notify(SUMMARY_NOTIFICATION_ID, notification)
        } catch (e: SecurityException) {
            // POST_NOTIFICATIONS permission not granted — silently skip
        }
    }

    private fun Double.formatPrice(): String = "%.2f".format(this)
}
