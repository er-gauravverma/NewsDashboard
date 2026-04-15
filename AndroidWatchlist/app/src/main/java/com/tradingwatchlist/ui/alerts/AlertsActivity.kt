package com.tradingwatchlist.ui.alerts

import android.os.Bundle
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.ItemTouchHelper
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.tradingwatchlist.R
import com.tradingwatchlist.databinding.ActivityAlertsBinding

class AlertsActivity : AppCompatActivity() {

    companion object {
        const val EXTRA_ASSET_SYMBOL = "extra_asset_symbol"
    }

    private lateinit var binding: ActivityAlertsBinding
    private val viewModel: AlertsViewModel by viewModels {
        AlertsViewModel.Factory(applicationContext)
    }
    private lateinit var adapter: AlertsAdapter

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityAlertsBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setSupportActionBar(binding.toolbar)
        supportActionBar?.apply {
            setDisplayHomeAsUpEnabled(true)
            title = getString(R.string.title_alerts)
        }

        val preselectedSymbol = intent.getStringExtra(EXTRA_ASSET_SYMBOL)

        setupRecyclerView()
        setupObservers()

        binding.fabAddAlert.setOnClickListener {
            AddAlertDialog(
                preselectedSymbol = preselectedSymbol,
                onConfirm = { symbol, price, direction ->
                    viewModel.addAlert(symbol, price, direction)
                }
            ).show(supportFragmentManager, "add_alert")
        }
    }

    private fun setupRecyclerView() {
        adapter = AlertsAdapter { alert ->
            viewModel.deleteAlert(alert)
        }
        binding.recyclerViewAlerts.apply {
            layoutManager = LinearLayoutManager(this@AlertsActivity)
            adapter = this@AlertsActivity.adapter
        }

        // Swipe-to-delete
        val swipeCallback = object : ItemTouchHelper.SimpleCallback(
            0, ItemTouchHelper.LEFT or ItemTouchHelper.RIGHT
        ) {
            override fun onMove(
                rv: RecyclerView, vh: RecyclerView.ViewHolder, target: RecyclerView.ViewHolder
            ) = false

            override fun onSwiped(viewHolder: RecyclerView.ViewHolder, direction: Int) {
                val alert = adapter.currentList[viewHolder.adapterPosition]
                viewModel.deleteAlert(alert)
            }
        }
        ItemTouchHelper(swipeCallback).attachToRecyclerView(binding.recyclerViewAlerts)
    }

    private fun setupObservers() {
        viewModel.alerts.observe(this) { alerts ->
            adapter.submitList(alerts)
            binding.tvEmptyAlerts.visibility =
                if (alerts.isEmpty()) android.view.View.VISIBLE else android.view.View.GONE
        }
    }

    override fun onSupportNavigateUp(): Boolean {
        onBackPressedDispatcher.onBackPressed()
        return true
    }
}
