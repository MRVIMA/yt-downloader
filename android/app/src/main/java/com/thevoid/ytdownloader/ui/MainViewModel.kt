package com.thevoid.ytdownloader.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.thevoid.ytdownloader.data.AppSettings
import com.thevoid.ytdownloader.data.Preset
import com.thevoid.ytdownloader.data.SettingsRepository
import com.thevoid.ytdownloader.download.DownloadItem
import com.thevoid.ytdownloader.download.DownloadRepository
import com.thevoid.ytdownloader.download.DownloadSpec
import com.thevoid.ytdownloader.download.YtDl
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

private val URL_REGEX = Regex("""https?://\S+""")

/** Every http(s) link in [text], trimmed of trailing punctuation and de-duplicated. */
fun extractUrls(text: String): List<String> =
    URL_REGEX.findAll(text).map { it.value.trimEnd('.', ',', ';', ')', ']', '>', '\'', '"') }
        .distinct().toList()

class MainViewModel(app: Application) : AndroidViewModel(app) {
    private val settingsRepo = SettingsRepository(app)
    private val downloads = DownloadRepository(app)

    val settings: StateFlow<AppSettings> =
        settingsRepo.settings.stateIn(viewModelScope, SharingStarted.Eagerly, AppSettings())
    val items: StateFlow<List<DownloadItem>> =
        downloads.items.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())
    val engine: StateFlow<YtDl.State> = YtDl.state

    private val _url = MutableStateFlow("")
    val url: StateFlow<String> = _url.asStateFlow()

    private val _messages = MutableStateFlow<String?>(null)
    val messages: StateFlow<String?> = _messages.asStateFlow()

    private val _ytDlpVersion = MutableStateFlow<String?>(null)
    val ytDlpVersion: StateFlow<String?> = _ytDlpVersion.asStateFlow()

    private val _updating = MutableStateFlow(false)
    val updating: StateFlow<Boolean> = _updating.asStateFlow()

    init {
        viewModelScope.launch {
            runCatching { YtDl.ensureInitialized(app) }
            _ytDlpVersion.value = withContext(Dispatchers.IO) { YtDl.version(app) }
        }
    }

    fun setUrl(value: String) { _url.value = value }

    fun onShared(text: String) {
        extractUrls(text).firstOrNull()?.let { _url.value = it }
            ?: show("No link found in the shared text")
    }

    fun download() {
        val urls = extractUrls(_url.value)
        if (urls.isEmpty()) {
            show("Paste a link that starts with http:// or https://")
            return
        }
        val s = settings.value
        urls.forEach { downloads.enqueue(DownloadSpec(it, s.preset, s.playlist, s.embedThumbnail, s.embedMetadata)) }
        _url.value = ""
    }

    fun retry(item: DownloadItem) {
        val s = settings.value
        downloads.enqueue(item.spec.copy(embedThumbnail = s.embedThumbnail, embedMetadata = s.embedMetadata))
    }

    fun cancel(item: DownloadItem) = downloads.cancel(item.id)
    fun clearFinished() = downloads.clearFinished()

    fun setPreset(p: Preset) = viewModelScope.launch { settingsRepo.setPreset(p) }
    fun setPlaylist(v: Boolean) = viewModelScope.launch { settingsRepo.setPlaylist(v) }
    fun setEmbedThumbnail(v: Boolean) = viewModelScope.launch { settingsRepo.setEmbedThumbnail(v) }
    fun setEmbedMetadata(v: Boolean) = viewModelScope.launch { settingsRepo.setEmbedMetadata(v) }

    fun updateYtDlp() {
        if (_updating.value) return
        _updating.value = true
        viewModelScope.launch {
            val app = getApplication<Application>()
            val message = runCatching { YtDl.update(app) }.fold(
                onSuccess = { updated -> if (updated) "yt-dlp updated" else "yt-dlp is already up to date" },
                onFailure = { "Update failed: ${it.message}" },
            )
            _ytDlpVersion.value = withContext(Dispatchers.IO) { YtDl.version(app) }
            _updating.value = false
            show(message)
        }
    }

    fun show(message: String) { _messages.value = message }
    fun messageShown() { _messages.value = null }
}
