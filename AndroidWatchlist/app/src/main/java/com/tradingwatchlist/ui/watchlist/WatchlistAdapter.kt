package com.tradingwatchlist.ui.watchlist

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import com.tradingwatchlist.databinding.ItemAssetCardBinding
import com.tradingwatchlist.domain.model.Asset
import com.tradingwatchlist.domain.model.AssetQuote

class WatchlistAdapter(
    private val onAssetClick: (Asset) -> Unit
) : ListAdapter<AssetQuote, AssetCardViewHolder>(DiffCallback()) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): AssetCardViewHolder {
        val binding = ItemAssetCardBinding.inflate(
            LayoutInflater.from(parent.context), parent, false
        )
        return AssetCardViewHolder(binding, onAssetClick)
    }

    override fun onBindViewHolder(holder: AssetCardViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    private class DiffCallback : DiffUtil.ItemCallback<AssetQuote>() {
        override fun areItemsTheSame(old: AssetQuote, new: AssetQuote) =
            old.asset == new.asset

        override fun areContentsTheSame(old: AssetQuote, new: AssetQuote) =
            old.currentPrice == new.currentPrice &&
                    old.rsi14 == new.rsi14 &&
                    old.sma200 == new.sma200 &&
                    old.lastUpdated == new.lastUpdated
    }
}
