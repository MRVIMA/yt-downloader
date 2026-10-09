package com.thevoid.ytdownloader.data

import android.content.Context
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.dataStore by preferencesDataStore(name = "settings")

data class AppSettings(
    val preset: Preset = Preset.BEST,
    val playlist: Boolean = false,
    val embedThumbnail: Boolean = true,
    val embedMetadata: Boolean = true,
)

class SettingsRepository(private val context: Context) {
    private object Keys {
        val PRESET = stringPreferencesKey("preset")
        val PLAYLIST = booleanPreferencesKey("playlist")
        val THUMBNAIL = booleanPreferencesKey("embed_thumbnail")
        val METADATA = booleanPreferencesKey("embed_metadata")
    }

    val settings: Flow<AppSettings> = context.dataStore.data.map { it.toSettings() }

    suspend fun setPreset(preset: Preset) = edit { it[Keys.PRESET] = preset.name }
    suspend fun setPlaylist(value: Boolean) = edit { it[Keys.PLAYLIST] = value }
    suspend fun setEmbedThumbnail(value: Boolean) = edit { it[Keys.THUMBNAIL] = value }
    suspend fun setEmbedMetadata(value: Boolean) = edit { it[Keys.METADATA] = value }

    private suspend fun edit(block: (androidx.datastore.preferences.core.MutablePreferences) -> Unit) {
        context.dataStore.edit(block)
    }

    private fun Preferences.toSettings() = AppSettings(
        preset = Preset.fromName(this[Keys.PRESET]),
        playlist = this[Keys.PLAYLIST] ?: false,
        embedThumbnail = this[Keys.THUMBNAIL] ?: true,
        embedMetadata = this[Keys.METADATA] ?: true,
    )
}
