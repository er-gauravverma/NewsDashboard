package com.tradingwatchlist.background

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build

object AlarmScheduler {

    private const val ALARM_REQUEST_CODE = 1001
    private const val INTERVAL_MS = 5 * 60 * 1000L  // 5 minutes

    fun schedulePriceUpdateAlarm(context: Context) {
        val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
        val pendingIntent = buildPendingIntent(context)

        // Cancel any existing alarm first (idempotent)
        alarmManager.cancel(pendingIntent)

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            if (alarmManager.canScheduleExactAlarms()) {
                // Use exact alarm for Android 12+ when permission is granted
                alarmManager.setExactAndAllowWhileIdle(
                    AlarmManager.RTC_WAKEUP,
                    System.currentTimeMillis() + INTERVAL_MS,
                    pendingIntent
                )
            } else {
                // Fall back to inexact repeating if exact alarm permission not granted
                alarmManager.setRepeating(
                    AlarmManager.RTC_WAKEUP,
                    System.currentTimeMillis() + INTERVAL_MS,
                    INTERVAL_MS,
                    pendingIntent
                )
            }
        } else {
            // For API < 31 use setRepeating
            alarmManager.setRepeating(
                AlarmManager.RTC_WAKEUP,
                System.currentTimeMillis() + INTERVAL_MS,
                INTERVAL_MS,
                pendingIntent
            )
        }
    }

    fun cancelPriceUpdateAlarm(context: Context) {
        val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
        alarmManager.cancel(buildPendingIntent(context))
    }

    private fun buildPendingIntent(context: Context): PendingIntent {
        val intent = Intent(context, PriceUpdateReceiver::class.java).apply {
            action = "com.tradingwatchlist.ACTION_PRICE_UPDATE"
        }
        return PendingIntent.getBroadcast(
            context,
            ALARM_REQUEST_CODE,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
    }
}
