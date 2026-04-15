package com.tradingwatchlist.ui.alerts

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.tradingwatchlist.data.db.AlertEntity
import com.tradingwatchlist.databinding.ItemAlertBinding
import com.tradingwatchlist.domain.model.Asset
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class AlertsAdapter(
    private val onDelete: (AlertEntity) -> Unit
) : ListAdapter<AlertEntity, AlertsAdapter.AlertViewHolder>(DiffCallback()) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): AlertViewHolder {
        val binding = ItemAlertBinding.inflate(
            LayoutInflater.from(parent.context), parent, false
        )
        return AlertViewHolder(binding, onDelete)
    }

    override fun onBindViewHolder(holder: AlertViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    class AlertViewHolder(
        private val binding: ItemAlertBinding,
        private val onDelete: (AlertEntity) -> Unit
    ) : RecyclerView.ViewHolder(binding.root) {

        private val dateFormat = SimpleDateFormat("dd MMM HH:mm", Locale.getDefault())

        fun bind(alert: AlertEntity) {
            val assetName = Asset.fromSymbol(alert.assetSymbol)?.displayName ?: alert.assetSymbol
            val directionText = if (alert.direction == "ABOVE") "above" else "below"

            binding.tvAlertDescription.text =
                "$assetName price $directionText ${"%.2f".format(alert.targetPrice)}"
            binding.tvAlertDate.text = "Set: ${dateFormat.format(Date(alert.createdAt))}"
            binding.tvDirection.text = alert.direction
            binding.btnDelete.setOnClickListener { onDelete(alert) }
        }
    }

    private class DiffCallback : DiffUtil.ItemCallback<AlertEntity>() {
        override fun areItemsTheSame(old: AlertEntity, new: AlertEntity) = old.id == new.id
        override fun areContentsTheSame(old: AlertEntity, new: AlertEntity) = old == new
    }
}
