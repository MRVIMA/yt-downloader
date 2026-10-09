package com.thevoid.ytdownloader.ui

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.thevoid.ytdownloader.BuildConfig
import com.thevoid.ytdownloader.download.MediaSaver

@Composable
fun SettingsDialog(vm: MainViewModel, onDismiss: () -> Unit) {
    val settings by vm.settings.collectAsStateWithLifecycle()
    val version by vm.ytDlpVersion.collectAsStateWithLifecycle()
    val updating by vm.updating.collectAsStateWithLifecycle()

    AlertDialog(
        onDismissRequest = onDismiss,
        confirmButton = { TextButton(onClick = onDismiss) { Text("Done") } },
        title = { Text("Settings") },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState())) {
                SwitchRow("Embed cover art", settings.embedThumbnail, vm::setEmbedThumbnail)
                SwitchRow("Embed title, artist and chapters", settings.embedMetadata, vm::setEmbedMetadata)
                HorizontalDivider(Modifier.padding(vertical = 12.dp))
                Text("yt-dlp ${version ?: "…"}", style = MaterialTheme.typography.bodyMedium)
                Text(
                    "Update it when downloads start failing — sites change often.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                Spacer(Modifier.height(8.dp))
                OutlinedButton(onClick = vm::updateYtDlp, enabled = !updating) {
                    if (updating) {
                        CircularProgressIndicator(Modifier.size(16.dp), strokeWidth = 2.dp)
                        Spacer(Modifier.width(8.dp))
                    }
                    Text(if (updating) "Updating…" else "Update yt-dlp")
                }
                HorizontalDivider(Modifier.padding(vertical = 12.dp))
                Text("Files are saved to Download/${MediaSaver.FOLDER}.",
                    style = MaterialTheme.typography.bodySmall)
                HorizontalDivider(Modifier.padding(vertical = 12.dp))
                Text("CREDITS", style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.primary)
                Spacer(Modifier.height(4.dp))
                Text(
                    "A THE VOID project by THE VOID PROTOCOL\n" +
                        "Owner of THE VOID: MRVIMA (alias VOIDVIMA)",
                    style = MaterialTheme.typography.bodySmall,
                )
                Spacer(Modifier.height(8.dp))
                Text(
                    "THE VOID DOWNLOADER ${BuildConfig.VERSION_NAME} · Powered by yt-dlp\n" +
                        "github.com/MRVIMA/yt-downloader · MIT License\n\n" +
                        "Only download content you have the right to. Respect copyright " +
                        "and each site's terms of service.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        },
    )
}

@Composable
private fun SwitchRow(label: String, checked: Boolean, onChange: (Boolean) -> Unit) {
    Row(Modifier.fillMaxWidth().padding(vertical = 4.dp), verticalAlignment = Alignment.CenterVertically) {
        Text(label, Modifier.weight(1f), style = MaterialTheme.typography.bodyMedium)
        Switch(checked = checked, onCheckedChange = onChange)
    }
}
