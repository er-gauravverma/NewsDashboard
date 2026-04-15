package com.tradingwatchlist.ui.watchlist

import android.Manifest
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.view.Menu
import android.view.MenuItem
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.recyclerview.widget.LinearLayoutManager
import com.tradingwatchlist.R
import com.tradingwatchlist.databinding.ActivityWatchlistBinding
import com.tradingwatchlist.domain.model.Asset
import com.tradingwatchlist.ui.alerts.AlertsActivity
import kotlinx.coroutines.launch

class WatchlistActivity : AppCompatActivity() {

    private lateinit var binding: ActivityWatchlistBinding
    private val viewModel: WatchlistViewModel by viewModels {
        WatchlistViewModel.Factory(applicationContext)
    }
    private lateinit var adapter: WatchlistAdapter

    private val notificationPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { /* permission result handled silently */ }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityWatchlistBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setSupportActionBar(binding.toolbar)
        supportActionBar?.title = getString(R.string.app_name)

        setupRecyclerView()
        setupObservers()
        requestNotificationPermission()
    }

    private fun setupRecyclerView() {
        adapter = WatchlistAdapter { asset: Asset ->
            val intent = Intent(this, AlertsActivity::class.java).apply {
                putExtra(AlertsActivity.EXTRA_ASSET_SYMBOL, asset.symbol)
            }
            startActivity(intent)
        }
        binding.recyclerView.apply {
            layoutManager = LinearLayoutManager(this@WatchlistActivity)
            adapter = this@WatchlistActivity.adapter
            setHasFixedSize(false)
        }

        binding.swipeRefresh.setOnRefreshListener {
            viewModel.refresh()
        }
    }

    private fun setupObservers() {
        viewModel.isLoading.observe(this) { loading ->
            binding.swipeRefresh.isRefreshing = loading
        }

        viewModel.error.observe(this) { errorMsg ->
            if (!errorMsg.isNullOrEmpty()) {
                Toast.makeText(this, errorMsg, Toast.LENGTH_SHORT).show()
            }
        }

        lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.quotes.collect { quotesMap ->
                    val sortedList = Asset.ALL.mapNotNull { quotesMap[it] }
                    adapter.submitList(sortedList)
                }
            }
        }
    }

    private fun requestNotificationPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            notificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
        }
    }

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menuInflater.inflate(R.menu.menu_watchlist, menu)
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            R.id.action_alerts -> {
                startActivity(Intent(this, AlertsActivity::class.java))
                true
            }
            R.id.action_refresh -> {
                viewModel.refresh()
                true
            }
            else -> super.onOptionsItemSelected(item)
        }
    }
}
