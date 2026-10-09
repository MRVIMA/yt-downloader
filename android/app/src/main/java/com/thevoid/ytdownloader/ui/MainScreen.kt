package com.thevoid.ytdownloader.ui

import android.content.ActivityNotFoundException
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowDropDown
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.work.WorkInfo
import com.thevoid.ytdownloader.data.Preset
import com.thevoid.ytdownloader.download.DownloadItem
import com.thevoid.ytdownloader.download.YtDl

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(vm: MainViewModel) {
    val url by vm.url.collectAsStateWithLifecycle()
    val settings by vm.settings.collectAsStateWithLifecycle()
    val items by vm.items.collectAsStateWithLifecycle()
    val engine by vm.engine.collectAsStateWithLifecycle()
    val message by vm.messages.collectAsStateWithLifecycle()
    val context = LocalContext.current
    val snackbar = remember { SnackbarHostState() }
    var showSettings by remember { mutableStateOf(false) }

    LaunchedEffect(message) {
        message?.let { snackbar.showSnackbar(it); vm.messageShown() }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text("YT DOWNLOADER", fontWeight = FontWeight.Bold, letterSpacing = 3.sp)
                },
                actions = {
                    IconButton(onClick = { showSettings = true }) {
                        Icon(Icons.Filled.Settings, contentDescription = "Settings")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.background,
                ),
            )
        },
        snackbarHost = { SnackbarHost(snackbar) },
    ) { padding ->
        LazyColumn(
            modifier = Modifier.fillMaxSize().padding(padding),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            item {
                EngineBanner(engine)
                OutlinedTextField(
                    value = url,
                    onValueChange = vm::setUrl,
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("Video or playlist link") },
                    placeholder = { Text("https://…") },
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Uri, imeAction = ImeAction.Go),
                    keyboardActions = KeyboardActions(onGo = { vm.download() }),
                    trailingIcon = {
                        if (url.isEmpty()) {
                            TextButton(onClick = { vm.setUrl(clipboardText(context)) }) { Text("PASTE") }
                        } else {
                            IconButton(onClick = { vm.setUrl("") }) {
                                Icon(Icons.Filled.Close, contentDescription = "Clear")
                            }
                        }
                    },
                )
                Spacer(Modifier.height(12.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    PresetPicker(settings.preset, vm::setPreset, Modifier.weight(1f))
                    Spacer(Modifier.width(8.dp))
                    FilterChip(
                        selected = settings.playlist,
                        onClick = { vm.setPlaylist(!settings.playlist) },
                        label = { Text("Playlist") },
                    )
                }
                Spacer(Modifier.height(12.dp))
                Button(
                    onClick = vm::download,
                    enabled = url.isNotBlank() && engine !is YtDl.State.Failed,
                    modifier = Modifier.fillMaxWidth().height(52.dp),
                ) {
                    Text("DOWNLOAD", fontWeight = FontWeight.Bold, letterSpacing = 2.sp)
                }
            }

            item {
                Row(
                    modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(
                        "DOWNLOADS",
                        style = MaterialTheme.typography.labelLarge,
                        color = MaterialTheme.colorScheme.primary,
                        letterSpacing = 2.sp,
                        modifier = Modifier.weight(1f),
                    )
                    if (items.any { !it.isActive }) {
                        TextButton(onClick = vm::clearFinished) { Text("Clear finished") }
                    }
                }
            }

            if (items.isEmpty()) {
                item {
                    Text(
                        "No downloads yet.\nShare a video to YT Downloader, or paste a link above.",
                        modifier = Modifier.fillMaxWidth().padding(vertical = 32.dp),
                        textAlign = TextAlign.Center,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }

            items(items, key = { it.id }) { item ->
                DownloadCard(
                    item = item,
                    onCancel = { vm.cancel(item) },
                    onRetry = { vm.retry(item) },
                    onOpen = { open(context, item) { vm.show(it) } },
                )
            }
        }
    }

    if (showSettings) {
        SettingsDialog(vm, onDismiss = { showSettings = false })
    }
}

@Composable
private fun EngineBanner(state: YtDl.State) {
    when (state) {
        YtDl.State.Ready -> Unit
        YtDl.State.Loading -> Row(
            Modifier.fillMaxWidth().padding(bottom = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            CircularProgressIndicator(Modifier.size(18.dp), strokeWidth = 2.dp)
            Spacer(Modifier.width(12.dp))
            Text("Preparing downloader (first launch takes a few seconds)…",
                style = MaterialTheme.typography.bodySmall)
        }
        is YtDl.State.Failed -> Text(
            "Couldn't start the downloader: ${state.message}",
            color = MaterialTheme.colorScheme.error,
            modifier = Modifier.padding(bottom = 12.dp),
        )
    }
}

@Composable
private fun PresetPicker(selected: Preset, onSelect: (Preset) -> Unit, modifier: Modifier = Modifier) {
    var expanded by remember { mutableStateOf(false) }
    Box(modifier) {
        OutlinedButton(onClick = { expanded = true }, modifier = Modifier.fillMaxWidth()) {
            Text(selected.label, modifier = Modifier.weight(1f), maxLines = 1)
            Icon(Icons.Filled.ArrowDropDown, contentDescription = null)
        }
        DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
            Preset.entries.forEach { preset ->
                DropdownMenuItem(
                    text = { Text(preset.label) },
                    onClick = { onSelect(preset); expanded = false },
                )
            }
        }
    }
}

@Composable
private fun DownloadCard(
    item: DownloadItem,
    onCancel: () -> Unit,
    onRetry: () -> Unit,
    onOpen: () -> Unit,
) {
    val colors = MaterialTheme.colorScheme
    Card(
        colors = CardDefaults.cardColors(containerColor = colors.surfaceContainer),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Row(Modifier.padding(start = 16.dp, top = 12.dp, bottom = 12.dp, end = 4.dp),
            verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text(
                    item.title ?: item.spec.url,
                    style = MaterialTheme.typography.titleSmall,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                )
                Text(
                    item.spec.preset.label + if (item.spec.playlist) " · Playlist" else "",
                    style = MaterialTheme.typography.bodySmall,
                    color = colors.onSurfaceVariant,
                )
                Spacer(Modifier.height(8.dp))
                when (item.state) {
                    WorkInfo.State.RUNNING -> if (item.progress >= 0f) {
                        LinearProgressIndicator(
                            progress = { item.progress / 100f },
                            modifier = Modifier.fillMaxWidth(),
                        )
                    } else {
                        LinearProgressIndicator(Modifier.fillMaxWidth())
                    }
                    WorkInfo.State.SUCCEEDED -> LinearProgressIndicator(
                        progress = { 1f }, modifier = Modifier.fillMaxWidth())
                    else -> Unit
                }
                Spacer(Modifier.height(6.dp))
                val (text, color) = statusText(item)
                Text(text, style = MaterialTheme.typography.bodySmall, color = color(colors),
                    maxLines = 3, overflow = TextOverflow.Ellipsis)
            }
            when {
                item.isActive -> IconButton(onClick = onCancel) {
                    Icon(Icons.Filled.Close, contentDescription = "Cancel")
                }
                item.state == WorkInfo.State.SUCCEEDED -> IconButton(onClick = onOpen) {
                    Icon(Icons.Filled.PlayArrow, contentDescription = "Open")
                }
                else -> IconButton(onClick = onRetry) {
                    Icon(Icons.Filled.Refresh, contentDescription = "Retry")
                }
            }
        }
    }
}

private fun statusText(item: DownloadItem): Pair<String, (androidx.compose.material3.ColorScheme) -> androidx.compose.ui.graphics.Color> =
    when (item.state) {
        WorkInfo.State.ENQUEUED, WorkInfo.State.BLOCKED -> "Waiting…" to { it.onSurfaceVariant }
        WorkInfo.State.RUNNING -> (item.status ?: "Starting…") to { it.onSurfaceVariant }
        WorkInfo.State.SUCCEEDED -> (if (item.uris.size > 1) "Saved ${item.uris.size} files to Download/YT Downloader"
            else "Saved to Download/YT Downloader") to { it.secondary }
        WorkInfo.State.FAILED -> if (item.error == "Cancelled") "Cancelled" to { it.onSurfaceVariant }
            else (item.error ?: "Failed") to { it.error }
        WorkInfo.State.CANCELLED -> "Cancelled" to { it.onSurfaceVariant }
    }

private fun clipboardText(context: Context): String {
    val clip = context.getSystemService(ClipboardManager::class.java)?.primaryClip
    return clip?.takeIf { it.itemCount > 0 }?.getItemAt(0)?.coerceToText(context)?.toString()?.trim().orEmpty()
}

private fun open(context: Context, item: DownloadItem, onError: (String) -> Unit) {
    val uri = item.uris.firstOrNull() ?: return onError("File not found")
    val intent = Intent(Intent.ACTION_VIEW)
        .setDataAndType(uri, item.mime ?: context.contentResolver.getType(uri))
        .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    try {
        context.startActivity(intent)
    } catch (_: ActivityNotFoundException) {
        onError("No app installed that can open this file")
    } catch (_: SecurityException) {
        onError("The file was moved or deleted")
    }
}
