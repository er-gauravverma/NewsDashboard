package com.tradingwatchlist.ui.watchlist

import android.graphics.Color
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.RecyclerView
import com.tradingwatchlist.R
import com.tradingwatchlist.databinding.ItemAssetCardBinding
import com.tradingwatchlist.domain.model.Asset
import com.tradingwatchlist.domain.model.AssetQuote
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class AssetCardViewHolder(
    private val binding: ItemAssetCardBinding,
    private val onAssetClick: (Asset) -> Unit
) : RecyclerView.ViewHolder(binding.root) {

    private val timeFormat = SimpleDateFormat("HH:mm:ss", Locale.getDefault())

    fun bind(quote: AssetQuote) {
        val ctx = binding.root.context

        binding.tvAssetName.text = quote.asset.displayName
        binding.tvSymbol.text = quote.asset.symbol
        binding.tvPrice.text = formatPrice(quote.currentPrice)

        // % change with color and arrow
        val change = quote.percentChange
        val changeText = "%+.2f%%".format(change)
        binding.tvPercentChange.text = changeText

        val positiveColor = ContextCompat.getColor(ctx, R.color.green_positive)
        val negativeColor = ContextCompat.getColor(ctx, R.color.red_negative)

        if (change >= 0) {
            binding.tvPercentChange.setTextColor(positiveColor)
            binding.ivChangeArrow.setImageResource(R.drawable.ic_arrow_up)
            binding.ivChangeArrow.setColorFilter(positiveColor)
        } else {
            binding.tvPercentChange.setTextColor(negativeColor)
            binding.ivChangeArrow.setImageResource(R.drawable.ic_arrow_down)
            binding.ivChangeArrow.setColorFilter(negativeColor)
        }

        // RSI with overbought/oversold color coding
        if (quote.rsi14 != null) {
            binding.tvRsi.text = "RSI(14): ${"%.1f".format(quote.rsi14)}"
            val rsiColor = when {
                quote.rsi14 >= 70 -> negativeColor   // overbought — red
                quote.rsi14 <= 30 -> positiveColor   // oversold — green
                else -> ContextCompat.getColor(ctx, R.color.text_primary)
            }
            binding.tvRsi.setTextColor(rsiColor)
        } else {
            binding.tvRsi.text = "RSI(14): loading…"
            binding.tvRsi.setTextColor(ContextCompat.getColor(ctx, R.color.text_secondary))
        }

        // SMA-200 with above/below border color on card
        if (quote.sma200 != null) {
            binding.tvSma200.text = "200 MA: ${formatPrice(quote.sma200)}"
            binding.cardView.strokeColor = if (quote.isAboveSma200) positiveColor else negativeColor
            binding.cardView.strokeWidth = 3
        } else {
            binding.tvSma200.text = "200 MA: loading…"
            binding.tvSma200.setTextColor(ContextCompat.getColor(ctx, R.color.text_secondary))
            binding.cardView.strokeColor = Color.TRANSPARENT
            binding.cardView.strokeWidth = 0
        }

        binding.tvLastUpdated.text = "Updated: ${timeFormat.format(Date(quote.lastUpdated))}"

        binding.root.setOnClickListener { onAssetClick(quote.asset) }
    }

    private fun formatPrice(price: Double): String =
        if (price >= 1000) "%,.2f".format(price) else "%.4f".format(price)
}
