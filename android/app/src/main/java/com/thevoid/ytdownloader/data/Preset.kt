package com.thevoid.ytdownloader.data

/** Quality choices, mirroring the desktop app's presets. */
enum class Preset(val label: String, val maxHeight: Int? = null, val audioFormat: String? = null) {
    BEST("Video · Best available"),
    P2160("Video · 4K (2160p)", maxHeight = 2160),
    P1440("Video · 1440p", maxHeight = 1440),
    P1080("Video · 1080p", maxHeight = 1080),
    P720("Video · 720p", maxHeight = 720),
    P480("Video · 480p", maxHeight = 480),
    P360("Video · 360p", maxHeight = 360),
    MP3("Audio · MP3", audioFormat = "mp3"),
    M4A("Audio · M4A (AAC)", audioFormat = "m4a"),
    OPUS("Audio · Opus", audioFormat = "opus");

    val isAudio: Boolean get() = audioFormat != null

    companion object {
        fun fromName(name: String?): Preset = entries.firstOrNull { it.name == name } ?: BEST
    }
}
