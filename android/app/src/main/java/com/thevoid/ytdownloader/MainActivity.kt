package com.thevoid.ytdownloader

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.core.content.ContextCompat
import com.thevoid.ytdownloader.ui.MainScreen
import com.thevoid.ytdownloader.ui.MainViewModel
import com.thevoid.ytdownloader.ui.theme.VoidTheme

class MainActivity : ComponentActivity() {
    private val vm: MainViewModel by viewModels()

    private val permissionLauncher =
        registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        if (savedInstanceState == null) handleShare(intent)
        requestPermissions()
        setContent {
            VoidTheme { MainScreen(vm) }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleShare(intent)
    }

    /** "Share → YT Downloader" from YouTube, a browser, etc. */
    private fun handleShare(intent: Intent?) {
        if (intent?.action == Intent.ACTION_SEND) {
            intent.getStringExtra(Intent.EXTRA_TEXT)?.let(vm::onShared)
        }
    }

    private fun requestPermissions() {
        val needed = buildList {
            if (Build.VERSION.SDK_INT >= 33) add(Manifest.permission.POST_NOTIFICATIONS)
            if (Build.VERSION.SDK_INT <= 28) add(Manifest.permission.WRITE_EXTERNAL_STORAGE)
        }.filter { ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED }
        if (needed.isNotEmpty()) permissionLauncher.launch(needed.toTypedArray())
    }
}
