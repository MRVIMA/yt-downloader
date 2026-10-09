package com.thevoid.ytdownloader

import com.thevoid.ytdownloader.data.Preset
import com.thevoid.ytdownloader.download.DownloadSpec
import com.thevoid.ytdownloader.download.buildArgs
import com.thevoid.ytdownloader.download.cleanError
import com.thevoid.ytdownloader.download.formatEta
import com.thevoid.ytdownloader.download.statusFromLine
import com.thevoid.ytdownloader.download.titleFromLine
import com.thevoid.ytdownloader.ui.extractUrls
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

class DownloadLogicTest {
    private val out = File("/out")

    private fun args(preset: Preset, playlist: Boolean = false, thumb: Boolean = true) =
        buildArgs(DownloadSpec("https://x.y/v", preset, playlist, embedThumbnail = thumb), out)

    private fun List<String>.after(flag: String) = this[indexOf(flag) + 1]

    @Test fun `video preset limits height and merges to mp4`() {
        val a = args(Preset.P720)
        assertEquals("bv*+ba/b", a.after("-f"))
        assertEquals("res:720,vcodec:avc,acodec:m4a", a.after("-S"))
        assertEquals("mp4", a.after("--merge-output-format"))
        assertTrue("--no-playlist" in a)
        assertTrue("--embed-chapters" in a)
    }

    @Test fun `best video has no resolution cap`() {
        assertEquals("res,vcodec:avc,acodec:m4a", args(Preset.BEST).after("-S"))
    }

    @Test fun `audio preset extracts audio`() {
        val a = args(Preset.MP3)
        assertEquals("ba/b", a.after("-f"))
        assertEquals("mp3", a.after("--audio-format"))
        assertFalse("--merge-output-format" in a)
        assertTrue("--embed-thumbnail" in a)
    }

    @Test fun `opus never embeds thumbnails`() {
        assertFalse("--embed-thumbnail" in args(Preset.OPUS))
    }

    @Test fun `playlist uses numbered subfolder template`() {
        val a = args(Preset.BEST, playlist = true)
        assertTrue(a.after("-o").startsWith("/out/%(playlist_title|)s/%(playlist_index&{:03d} - |)s"))
        assertTrue("--yes-playlist" in a)
    }

    @Test fun `title parsed from destination lines`() {
        assertEquals("Me at the zoo",
            titleFromLine("[download] Destination: /c/Me at the zoo [jNQXAC9IVRw].f137.mp4"))
        assertEquals("Song",
            titleFromLine("[Merger] Merging formats into \"/c/Song [abc].mp4\""))
        assertNull(titleFromLine("[download]  45.0% of 10MiB"))
    }

    @Test fun `status lines`() {
        assertEquals("Merging video and audio…", statusFromLine("[Merger] Merging formats into x"))
        assertEquals("Item 3 of 10", statusFromLine("[download] Downloading item 3 of 10"))
        assertNull(statusFromLine("[download]  12.5% of 3MiB"))
    }

    @Test fun `errors are cleaned`() {
        assertEquals("Video unavailable",
            cleanError("WARNING: x\nERROR: [youtube] abc123: Video unavailable"))
        assertEquals("Download failed", cleanError(null))
    }

    @Test fun `urls extracted from shared text`() {
        assertEquals(listOf("https://youtu.be/abc"),
            extractUrls("Check this out! https://youtu.be/abc."))
        assertTrue(extractUrls("no links").isEmpty())
    }

    @Test fun `eta formatting`() {
        assertEquals("01:05", formatEta(65))
        assertEquals("1:02:05", formatEta(3725))
    }
}
