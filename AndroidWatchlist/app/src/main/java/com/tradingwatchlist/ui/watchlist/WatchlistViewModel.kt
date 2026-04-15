package com.tradingwatchlist.ui.watchlist

import android.content.Context
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.tradingwatchlist.data.repository.MarketRepository
import com.tradingwatchlist.di.ServiceLocator
import com.tradingwatchlist.domain.model.Asset
import com.tradingwatchlist.domain.model.AssetQuote
import kotlinx.coroutines.async
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

class WatchlistViewModel(
    private val marketRepository: MarketRepository
) : ViewModel() {

    val quotes: StateFlow<Map<Asset, AssetQuote>> = marketRepository.quotes

    private val _isLoading = MutableLiveData(false)
    val isLoading: LiveData<Boolean> = _isLoading

    private val _error = MutableLiveData<String?>(null)
    val error: LiveData<String?> = _error

    init {
        loadAll()
    }

    fun loadAll() {
        viewModelScope.launch {
            _isLoading.value = true
            _error.value = null

            // Fetch prices and 1Hr indicators in parallel
            val priceJob = async { marketRepository.refreshAllPrices() }
            val indicatorJob = async { marketRepository.refreshIndicators() }

            priceJob.await().onFailure { _error.value = "Price fetch failed: ${it.message}" }
            indicatorJob.await().onFailure { _error.value = "Indicator fetch failed: ${it.message}" }

            _isLoading.value = false
        }
    }

    fun refresh() = loadAll()

    class Factory(private val context: Context) : ViewModelProvider.Factory {
        override fun <T : ViewModel> create(modelClass: Class<T>): T {
            @Suppress("UNCHECKED_CAST")
            return WatchlistViewModel(
                ServiceLocator.getMarketRepository(context)
            ) as T
        }
    }
}
