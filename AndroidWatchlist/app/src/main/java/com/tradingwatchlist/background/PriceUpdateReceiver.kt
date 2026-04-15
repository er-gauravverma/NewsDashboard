package com.tradingwatchlist.background

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import com.tradingwatchlist.di.ServiceLocator
import com.tradingwatchlist.notification.NotificationHelper
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withTimeout

class PriceUpdateReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        val pendingResult = goAsync()

        CoroutineScope(Dispatchers.IO).launch {
            try {
                withTimeout(9_000L) {
                    val repo = ServiceLocator.getMarketRepository(context)

                    // 1. Refresh current prices for all assets
                    repo.refreshAllPrices()

                    // 2. Check configured alerts against new prices
                    val triggered = repo.checkAndFireAlerts()

                    // 3. Fire a notification for each triggered alert
                    for ((alert, quote) in triggered) {
                        NotificationHelper.sendAlertNotification(context, alert, quote)
                    }

                    // 4. Update the persistent price summary notification
                    NotificationHelper.updatePriceSummaryNotification(context, repo.quotes.value)
                }
            } catch (e: Exception) {
                // Swallow exceptions — we must call finish() regardless
            } finally {
                pendingResult.finish()
            }

            // Reschedule the next exact alarm (required on Android 12+)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                AlarmScheduler.schedulePriceUpdateAlarm(context)
            }
        }
    }
}
