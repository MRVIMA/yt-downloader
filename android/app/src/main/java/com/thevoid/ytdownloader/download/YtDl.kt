package com.thevoid.ytdownloader.download

import android.content.Context
import android.util.Log
import com.yausername.ffmpeg.FFmpeg
import com.yausername.youtubedl_android.YoutubeDL
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext

/** One-time setup of the bundled Python/yt-dlp/ffmpeg (unpacks on first launch). */
object YtDl {
    sealed interface State {
        data object Loading : State
        data object Ready : State
        data class Failed(val message: String) : State
    }

    private val mutex = Mutex()
    private val _state = MutableStateFlow<State>(State.Loading)
    val state: StateFlow<State> = _state.asStateFlow()

    suspend fun ensureInitialized(context: Context) = withContext(Dispatchers.IO) {
        mutex.withLock {
            if (_state.value == State.Ready) return@withLock
            _state.value = State.Loading
            try {
                YoutubeDL.getInstance().init(context.applicationContext)
                FFmpeg.getInstance().init(context.applicationContext)
                _state.value = State.Ready
            } catch (e: Throwable) { // also Errors (e.g. a missing class) so the UI never hangs
                if (e is kotlinx.coroutines.CancellationException) throw e
                Log.e("YtDl", "init failed", e)
                _state.value = State.Failed(e.message ?: e.javaClass.simpleName)
                throw e
            }
        }
    }

    fun version(context: Context): String? =
        runCatching { YoutubeDL.getInstance().versionName(context) }.getOrNull()

    /** Returns true if a newer yt-dlp was installed. */
    suspend fun update(context: Context): Boolean = withContext(Dispatchers.IO) {
        ensureInitialized(context)
        YoutubeDL.getInstance().updateYoutubeDL(context, YoutubeDL.UpdateChannel.STABLE) ==
            YoutubeDL.UpdateStatus.DONE
    }
}
