package com.thevoid.ytdownloader

import android.app.Application
import com.thevoid.ytdownloader.download.Notifications
import com.thevoid.ytdownloader.download.YtDl
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

class YtDownloaderApp : Application() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    override fun onCreate() {
        super.onCreate()
        Notifications.createChannels(this)
        // Unpacking Python/yt-dlp takes a few seconds on first launch; start it right away.
        scope.launch { runCatching { YtDl.ensureInitialized(this@YtDownloaderApp) } }
    }
}
