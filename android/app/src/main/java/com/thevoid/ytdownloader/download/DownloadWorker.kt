package com.thevoid.ytdownloader.download

import android.content.Context
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.SystemClock
import android.util.Log
import androidx.core.app.NotificationManagerCompat
import androidx.work.CoroutineWorker
import androidx.work.ForegroundInfo
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import androidx.work.workDataOf
import com.thevoid.ytdownloader.data.Preset
import com.yausername.youtubedl_android.YoutubeDL
import com.yausername.youtubedl_android.YoutubeDLRequest
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.withContext
import java.io.File

/** Runs one download in the background (survives the app being closed). */
class DownloadWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {

    private val notificationId = id.hashCode()
    private var title: String = inputData.getString(KEY_URL).orEmpty()
    private var lastUpdate = 0L

    override suspend fun getForegroundInfo(): ForegroundInfo = foregroundInfo("Starting…", -1f)

    override suspend fun doWork(): Result {
        val spec = DownloadSpec(
            url = inputData.getString(KEY_URL) ?: return Result.failure(),
            preset = Preset.fromName(inputData.getString(KEY_PRESET)),
            playlist = inputData.getBoolean(KEY_PLAYLIST, false),
            embedThumbnail = inputData.getBoolean(KEY_THUMBNAIL, true),
            embedMetadata = inputData.getBoolean(KEY_METADATA, true),
        )
        runCatching { setForeground(foregroundInfo("Fetching info…", -1f)) }
            .onFailure { Log.w(TAG, "Could not start foreground service", it) }

        val workDir = File(applicationContext.cacheDir, "downloads/$id")
        try {
            YtDl.ensureInitialized(applicationContext)
            workDir.deleteRecursively()
            workDir.mkdirs()
            val response = execute(spec, workDir)
            val files = workDir.walkTopDown()
                .filter { it.isFile && it.extension !in TEMP_EXTENSIONS }
                .toList()
            if (files.isEmpty()) {
                return fail(cleanError(response.err.ifBlank { "Nothing was downloaded" }))
            }
            val uris = files.map { file ->
                val sub = file.parentFile?.takeIf { it != workDir }?.relativeTo(workDir)?.path
                MediaSaver.save(applicationContext, file, sub)
            }
            val doneTitle = if (files.size == 1) titleFromLine("Destination: ${files[0].path}") ?: title
            else "$title (${files.size} files)"
            Notifications.finished(applicationContext, notificationId + 1, doneTitle, uris.first(),
                MediaSaver.mimeType(files.first()))
            return Result.success(workDataOf(
                KEY_TITLE to doneTitle,
                KEY_URIS to uris.map { it.toString() }.toTypedArray(),
                KEY_MIME to MediaSaver.mimeType(files.first()),
            ))
        } catch (e: CancellationException) {
            throw e
        } catch (e: YoutubeDL.CanceledException) {
            return Result.failure(workDataOf(KEY_TITLE to title, KEY_ERROR to "Cancelled"))
        } catch (e: Throwable) {
            Log.w(TAG, "Download failed: ${spec.url}", e)
            return fail(cleanError(e.message ?: e.javaClass.simpleName))
        } finally {
            withContext(Dispatchers.IO + kotlinx.coroutines.NonCancellable) { workDir.deleteRecursively() }
            NotificationManagerCompat.from(applicationContext).cancel(notificationId)
        }
    }

    private suspend fun execute(spec: DownloadSpec, workDir: File) = coroutineScope {
        val request = YoutubeDLRequest(spec.url).addCommands(buildArgs(spec, workDir))
        val processId = id.toString()
        val job = async(Dispatchers.IO) {
            YoutubeDL.getInstance().execute(request, processId) { progress, eta, line ->
                onOutput(progress, eta, line)
            }
        }
        try {
            job.await()
        } catch (e: CancellationException) {
            // WorkManager cancelled us: kill the yt-dlp process so the blocking call returns.
            YoutubeDL.getInstance().destroyProcessById(processId)
            throw e
        }
    }

    private fun onOutput(progress: Float, eta: Long, line: String) {
        titleFromLine(line)?.let { title = it }
        val status = statusFromLine(line)
        val downloading = progress >= 0f && line.startsWith("[download]") && status == null
        val now = SystemClock.elapsedRealtime()
        if (downloading && now - lastUpdate < 500) return
        lastUpdate = now
        val text = when {
            status != null -> status
            downloading -> "${progress.toInt()}%" + if (eta > 0) " · ${formatEta(eta)} left" else ""
            else -> return
        }
        val percent = if (downloading) progress else -1f
        setProgressAsync(workDataOf(KEY_TITLE to title, KEY_STATUS to text, KEY_PROGRESS to percent))
        runCatching {
            @Suppress("MissingPermission")
            NotificationManagerCompat.from(applicationContext)
                .notify(notificationId, Notifications.progress(applicationContext, title, text,
                    percent, cancelIntent()))
        }
    }

    private fun fail(message: String): Result {
        Notifications.failed(applicationContext, notificationId + 1, title, message)
        return Result.failure(workDataOf(KEY_TITLE to title, KEY_ERROR to message))
    }

    private fun cancelIntent() = WorkManager.getInstance(applicationContext).createCancelPendingIntent(id)

    private fun foregroundInfo(status: String, percent: Float): ForegroundInfo {
        val n = Notifications.progress(applicationContext, title, status, percent, cancelIntent())
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            ForegroundInfo(notificationId, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC)
        } else {
            ForegroundInfo(notificationId, n)
        }
    }

    companion object {
        private const val TAG = "DownloadWorker"
        const val KEY_URL = "url"
        const val KEY_PRESET = "preset"
        const val KEY_PLAYLIST = "playlist"
        const val KEY_THUMBNAIL = "thumbnail"
        const val KEY_METADATA = "metadata"
        const val KEY_TITLE = "title"
        const val KEY_STATUS = "status"
        const val KEY_PROGRESS = "progress"
        const val KEY_URIS = "uris"
        const val KEY_MIME = "mime"
        const val KEY_ERROR = "error"
        private val TEMP_EXTENSIONS = setOf("part", "ytdl", "temp", "jpg", "webp", "png")
    }
}

fun formatEta(seconds: Long): String {
    val h = seconds / 3600
    val m = (seconds % 3600) / 60
    val s = seconds % 60
    return if (h > 0) "%d:%02d:%02d".format(h, m, s) else "%02d:%02d".format(m, s)
}
