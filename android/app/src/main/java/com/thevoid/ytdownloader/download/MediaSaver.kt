package com.thevoid.ytdownloader.download

import android.content.ContentValues
import android.content.Context
import android.media.MediaScannerConnection
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import android.webkit.MimeTypeMap
import androidx.core.content.FileProvider
import java.io.File
import java.io.IOException

/** Copies finished files into the public Download/YT Downloader folder. */
object MediaSaver {
    const val FOLDER = "YT Downloader"

    fun mimeType(file: File): String =
        MimeTypeMap.getSingleton().getMimeTypeFromExtension(file.extension.lowercase())
            ?: "application/octet-stream"

    fun save(context: Context, file: File, subfolder: String?): Uri =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) saveMediaStore(context, file, subfolder)
        else saveLegacy(context, file, subfolder)

    private fun saveMediaStore(context: Context, file: File, subfolder: String?): Uri {
        val resolver = context.contentResolver
        val relative = listOfNotNull(Environment.DIRECTORY_DOWNLOADS, FOLDER, subfolder).joinToString("/")
        val values = ContentValues().apply {
            put(MediaStore.MediaColumns.DISPLAY_NAME, file.name)
            put(MediaStore.MediaColumns.MIME_TYPE, mimeType(file))
            put(MediaStore.MediaColumns.RELATIVE_PATH, relative)
            put(MediaStore.MediaColumns.IS_PENDING, 1)
        }
        val uri = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values)
            ?: throw IOException("Couldn't create ${file.name} in Downloads")
        try {
            resolver.openOutputStream(uri)?.use { out -> file.inputStream().use { it.copyTo(out) } }
                ?: throw IOException("Couldn't write ${file.name}")
            values.clear()
            values.put(MediaStore.MediaColumns.IS_PENDING, 0)
            resolver.update(uri, values, null, null)
        } catch (e: Exception) {
            resolver.delete(uri, null, null)
            throw e
        }
        return uri
    }

    @Suppress("DEPRECATION") // public storage access is the only option before Android 10
    private fun saveLegacy(context: Context, file: File, subfolder: String?): Uri {
        val base = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS)
        val dir = File(base, listOfNotNull(FOLDER, subfolder).joinToString("/")).apply { mkdirs() }
        var target = File(dir, file.name)
        var n = 1
        while (target.exists()) target = File(dir, "${file.nameWithoutExtension} (${n++}).${file.extension}")
        file.copyTo(target)
        MediaScannerConnection.scanFile(context, arrayOf(target.absolutePath), null, null)
        return FileProvider.getUriForFile(context, "${context.packageName}.files", target)
    }
}
