package com.thevoid.ytdownloader.download

import com.thevoid.ytdownloader.data.Preset
import java.io.File

/** Everything needed to start (or retry) one download. */
data class DownloadSpec(
    val url: String,
    val preset: Preset,
    val playlist: Boolean,
    val embedThumbnail: Boolean = true,
    val embedMetadata: Boolean = true,
)

private const val NAME = "%(title).180B [%(id)s].%(ext)s"

/** yt-dlp command-line arguments for [spec], writing into [outputDir]. Pure, so it's unit-tested. */
fun buildArgs(spec: DownloadSpec, outputDir: File): List<String> = buildList {
    val template = if (spec.playlist) {
        // Empty fields collapse to "", so single videos still land directly in outputDir.
        "%(playlist_title|)s/%(playlist_index&{:03d} - |)s$NAME"
    } else {
        NAME
    }
    addAll(listOf("-o", "${outputDir.absolutePath}/$template", "--no-mtime"))
    if (spec.playlist) addAll(listOf("--yes-playlist", "--ignore-errors")) else add("--no-playlist")

    val preset = spec.preset
    if (preset.isAudio) {
        addAll(listOf("-f", "ba/b", "-x", "--audio-format", preset.audioFormat!!, "--audio-quality", "0"))
    } else {
        // Highest resolution up to the preset's limit; at each resolution prefer H.264 + AAC,
        // which every phone can play (AV1/VP9 only when H.264 isn't offered, e.g. 4K).
        val res = preset.maxHeight?.let { "res:$it" } ?: "res"
        addAll(listOf("-f", "bv*+ba/b", "-S", "$res,vcodec:avc,acodec:m4a"))
        addAll(listOf("--merge-output-format", "mp4"))
        if (spec.embedMetadata) add("--embed-chapters")
    }
    if (spec.embedMetadata) add("--embed-metadata")
    // Opus cover art needs mutagen, which the bundled Python lacks.
    if (spec.embedThumbnail && preset != Preset.OPUS) {
        addAll(listOf("--embed-thumbnail", "--convert-thumbnails", "jpg"))
    }
}

private val DESTINATION = Regex("""(?:Destination: |Merging formats into ")(.+?)"?$""")
private val FORMAT_SUFFIX = Regex("""\.f\d+(-\d+)?$""")
private val ID_SUFFIX = Regex("""\s*\[[^\]]+]$""")

/** Pulls a human title out of a yt-dlp output line such as "[download] Destination: …". */
fun titleFromLine(line: String): String? {
    val path = DESTINATION.find(line.trim())?.groupValues?.get(1) ?: return null
    val stem = File(path).nameWithoutExtension
    return stem.replace(FORMAT_SUFFIX, "").replace(ID_SUFFIX, "").ifBlank { null }
}

/** Short status for post-processing lines, or null for lines we don't surface. */
fun statusFromLine(line: String): String? = when {
    line.startsWith("[Merger]") -> "Merging video and audio…"
    line.startsWith("[ExtractAudio]") -> "Converting audio…"
    line.startsWith("[EmbedThumbnail]") -> "Embedding cover art…"
    line.startsWith("[Metadata]") -> "Writing metadata…"
    line.startsWith("[download] Downloading item") ->
        line.removePrefix("[download] Downloading ").replaceFirstChar { it.uppercase() }
    line.startsWith("[youtube]") || line.startsWith("[info]") -> "Fetching info…"
    else -> null
}

/** Reduces yt-dlp's stderr to the most useful single line. */
fun cleanError(raw: String?): String {
    val lines = raw.orEmpty().lines().map { it.trim() }.filter { it.isNotEmpty() }
    val error = lines.lastOrNull { it.startsWith("ERROR:") } ?: lines.lastOrNull() ?: return "Download failed"
    return error.removePrefix("ERROR:").trim()
        .replace(Regex("""^\[[\w:]+]\s*[\w-]+:\s*"""), "")
        .take(300)
}
