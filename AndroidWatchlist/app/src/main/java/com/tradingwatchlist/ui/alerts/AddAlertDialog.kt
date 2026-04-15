package com.tradingwatchlist.ui.alerts

import android.app.Dialog
import android.os.Bundle
import android.widget.ArrayAdapter
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.fragment.app.DialogFragment
import com.tradingwatchlist.databinding.DialogAddAlertBinding
import com.tradingwatchlist.domain.model.AlertDirection
import com.tradingwatchlist.domain.model.Asset

class AddAlertDialog(
    private val preselectedSymbol: String? = null,
    private val onConfirm: (assetSymbol: String, targetPrice: Double, direction: AlertDirection) -> Unit
) : DialogFragment() {

    private var _binding: DialogAddAlertBinding? = null
    private val binding get() = _binding!!

    override fun onCreateDialog(savedInstanceState: Bundle?): Dialog {
        _binding = DialogAddAlertBinding.inflate(layoutInflater)

        // Populate asset spinner
        val assets = Asset.ALL
        val assetNames = assets.map { it.displayName }
        val adapter = ArrayAdapter(
            requireContext(),
            android.R.layout.simple_spinner_item,
            assetNames
        ).apply {
            setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        }
        binding.spinnerAsset.adapter = adapter

        // Pre-select asset if one was passed from the watchlist card click
        if (preselectedSymbol != null) {
            val idx = assets.indexOfFirst { it.symbol == preselectedSymbol }
            if (idx >= 0) binding.spinnerAsset.setSelection(idx)
        }

        return AlertDialog.Builder(requireContext())
            .setTitle("Add Price Alert")
            .setView(binding.root)
            .setPositiveButton("Add") { _, _ ->
                val selectedAsset = assets[binding.spinnerAsset.selectedItemPosition]
                val priceText = binding.etTargetPrice.text?.toString()?.trim()
                val targetPrice = priceText?.toDoubleOrNull()

                if (targetPrice == null || targetPrice <= 0) {
                    Toast.makeText(context, "Enter a valid price", Toast.LENGTH_SHORT).show()
                    return@setPositiveButton
                }

                val direction = if (binding.rbAbove.isChecked) AlertDirection.ABOVE
                else AlertDirection.BELOW

                onConfirm(selectedAsset.symbol, targetPrice, direction)
            }
            .setNegativeButton("Cancel", null)
            .create()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
