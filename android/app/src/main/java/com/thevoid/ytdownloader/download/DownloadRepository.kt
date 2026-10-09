package com.thevoid.ytdownloader.download

import android.content.Context
import android.net.Uri
import androidx.work.Constraints
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkInfo
import androidx.work.WorkManager
import androidx.work.workDataOf
import com.thevoid.ytdownloader.data.Preset
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import java.time.Duration
import java.util.UUID

data class DownloadItem(
    val id: UUID,
    val spec: DownloadSpec,
    val createdAt: Long,
    val state: WorkInfo.State,
    val title: String?,
    val status: String?,
    val progress: Float,
    val error: String?,
    val uris: List<Uri>,
    val mime: String?,
) {
    val isActive get() = !state.isFinished
}

/** The download queue, backed by WorkManager so it survives restarts. */
class DownloadRepository(context: Context) {
    private val workManager = WorkManager.getInstance(context)

    val items: Flow<List<DownloadItem>> = workManager.getWorkInfosByTagFlow(TAG)
        .map { infos -> infos.mapNotNull(::toItem).sortedByDescending { it.createdAt } }

    fun enqueue(spec: DownloadSpec): UUID {
        val request = OneTimeWorkRequestBuilder<DownloadWorker>()
            .setInputData(workDataOf(
                DownloadWorker.KEY_URL to spec.url,
                DownloadWorker.KEY_PRESET to spec.preset.name,
                DownloadWorker.KEY_PLAYLIST to spec.playlist,
                DownloadWorker.KEY_THUMBNAIL to spec.embedThumbnail,
                DownloadWorker.KEY_METADATA to spec.embedMetadata,
            ))
            .setConstraints(Constraints(requiredNetworkType = NetworkType.CONNECTED))
            .keepResultsForAtLeast(Duration.ofDays(7))
            .addTag(TAG)
            // Input data isn't readable from WorkInfo, so the spec also travels in tags.
            .addTag("$URL${spec.url}")
            .addTag("$PRESET${spec.preset.name}")
            .addTag("$PLAYLIST${spec.playlist}")
            .addTag("$CREATED${System.currentTimeMillis()}")
            .build()
        workManager.enqueue(request)
        return request.id
    }

    fun cancel(id: UUID) {
        workManager.cancelWorkById(id)
    }

    fun clearFinished() {
        workManager.pruneWork()
    }

    private fun toItem(info: WorkInfo): DownloadItem? {
        fun tag(prefix: String) = info.tags.firstOrNull { it.startsWith(prefix) }?.removePrefix(prefix)
        val url = tag(URL) ?: return null
        val data = if (info.state.isFinished) info.outputData else info.progress
        return DownloadItem(
            id = info.id,
            spec = DownloadSpec(url, Preset.fromName(tag(PRESET)), tag(PLAYLIST).toBoolean()),
            createdAt = tag(CREATED)?.toLongOrNull() ?: 0L,
            state = info.state,
            title = data.getString(DownloadWorker.KEY_TITLE)?.takeIf { it != url },
            status = data.getString(DownloadWorker.KEY_STATUS),
            progress = data.getFloat(DownloadWorker.KEY_PROGRESS, -1f),
            error = info.outputData.getString(DownloadWorker.KEY_ERROR),
            uris = info.outputData.getNullableStringArray(DownloadWorker.KEY_URIS)?.filterNotNull()?.map(Uri::parse).orEmpty(),
            mime = info.outputData.getString(DownloadWorker.KEY_MIME),
        )
    }

    private companion object {
        const val TAG = "download"
        const val URL = "url:"
        const val PRESET = "preset:"
        const val PLAYLIST = "playlist:"
        const val CREATED = "created:"
    }
}
