package com.tradingwatchlist.ui.alerts

import android.content.Context
import androidx.lifecycle.LiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.asLiveData
import androidx.lifecycle.viewModelScope
import com.tradingwatchlist.data.db.AlertEntity
import com.tradingwatchlist.data.repository.AlertRepository
import com.tradingwatchlist.di.ServiceLocator
import com.tradingwatchlist.domain.model.AlertDirection
import kotlinx.coroutines.launch

class AlertsViewModel(
    private val alertRepository: AlertRepository
) : ViewModel() {

    val alerts: LiveData<List<AlertEntity>> = alertRepository.activeAlerts.asLiveData()

    fun addAlert(assetSymbol: String, targetPrice: Double, direction: AlertDirection) {
        viewModelScope.launch {
            alertRepository.addAlert(assetSymbol, targetPrice, direction)
        }
    }

    fun deleteAlert(alert: AlertEntity) {
        viewModelScope.launch {
            alertRepository.deleteAlert(alert)
        }
    }

    class Factory(private val context: Context) : ViewModelProvider.Factory {
        override fun <T : ViewModel> create(modelClass: Class<T>): T {
            @Suppress("UNCHECKED_CAST")
            return AlertsViewModel(
                ServiceLocator.getAlertRepository(context)
            ) as T
        }
    }
}
