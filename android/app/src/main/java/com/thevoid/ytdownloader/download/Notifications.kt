package com.thevoid.ytdownloader.download

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import com.thevoid.ytdownloader.MainActivity
import com.thevoid.ytdownloader.R

object Notifications {
    const val CHANNEL_PROGRESS = "downloads"
    const val CHANNEL_DONE = "completed"

    fun createChannels(context: Context) {
        val manager = context.getSystemService(NotificationManager::class.java)
        manager.createNotificationChannels(listOf(
            NotificationChannel(CHANNEL_PROGRESS, "Downloads in progress",
                NotificationManager.IMPORTANCE_LOW),
            NotificationChannel(CHANNEL_DONE, "Finished downloads",
                NotificationManager.IMPORTANCE_DEFAULT),
        ))
    }

    private fun openAppIntent(context: Context): PendingIntent = PendingIntent.getActivity(
        context, 0, Intent(context, MainActivity::class.java)
            .addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP),
        PendingIntent.FLAG_IMMUTABLE,
    )

    fun progress(
        context: Context, title: String, status: String, percent: Float, cancel: PendingIntent,
    ) = NotificationCompat.Builder(context, CHANNEL_PROGRESS)
        .setSmallIcon(R.drawable.ic_notification)
        .setContentTitle(title)
        .setContentText(status)
        .setOnlyAlertOnce(true)
        .setOngoing(true)
        .setSilent(true)
        .setContentIntent(openAppIntent(context))
        .setProgress(100, percent.coerceIn(0f, 100f).toInt(), percent < 0)
        .addAction(0, "Cancel", cancel)
        .build()

    fun finished(context: Context, id: Int, title: String, uri: Uri?, mime: String?) {
        if (!canNotify(context)) return
        val tap = uri?.let {
            val view = Intent(Intent.ACTION_VIEW).setDataAndType(it, mime)
                .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_ACTIVITY_NEW_TASK)
            PendingIntent.getActivity(context, id, view, PendingIntent.FLAG_IMMUTABLE)
        } ?: openAppIntent(context)
        val n = NotificationCompat.Builder(context, CHANNEL_DONE)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(title)
            .setContentText("Saved to Download/${MediaSaver.FOLDER}")
            .setContentIntent(tap)
            .setAutoCancel(true)
            .build()
        @Suppress("MissingPermission")
        NotificationManagerCompat.from(context).notify(id, n)
    }

    fun failed(context: Context, id: Int, title: String, message: String) {
        if (!canNotify(context)) return
        val n = NotificationCompat.Builder(context, CHANNEL_DONE)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle("Download failed: $title")
            .setContentText(message)
            .setStyle(NotificationCompat.BigTextStyle().bigText(message))
            .setContentIntent(openAppIntent(context))
            .setAutoCancel(true)
            .build()
        @Suppress("MissingPermission")
        NotificationManagerCompat.from(context).notify(id, n)
    }

    private fun canNotify(context: Context) =
        android.os.Build.VERSION.SDK_INT < 33 || ContextCompat.checkSelfPermission(
            context, Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED
}
