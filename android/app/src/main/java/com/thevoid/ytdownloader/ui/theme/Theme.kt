package com.thevoid.ytdownloader.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

// THE VOID brand palette (see Brand Core → Identity board).
val VoidBlack = Color(0xFF050505)
val CharcoalBlack = Color(0xFF151515)
val DarkSlate = Color(0xFF1B1B1B)
val SmokeGray = Color(0xFF2A2A2A)
val SteelGray = Color(0xFF3A3A3A)
val AshGray = Color(0xFF606060)
val LightAsh = Color(0xFFA0A0A0)
val MetallicSilver = Color(0xFFC8C8C8)
val BloodRed = Color(0xFF8B0000)
val CrimsonRed = Color(0xFFE10600)
val GlitchRed = Color(0xFFFF2D2D)

private val VoidColors = darkColorScheme(
    primary = CrimsonRed,
    onPrimary = Color.White,
    primaryContainer = BloodRed,
    onPrimaryContainer = Color.White,
    secondary = MetallicSilver,
    onSecondary = VoidBlack,
    secondaryContainer = SmokeGray,
    onSecondaryContainer = MetallicSilver,
    tertiary = GlitchRed,
    background = VoidBlack,
    onBackground = Color(0xFFE6E6E6),
    surface = VoidBlack,
    onSurface = Color(0xFFE6E6E6),
    surfaceVariant = DarkSlate,
    onSurfaceVariant = LightAsh,
    surfaceContainerLowest = VoidBlack,
    surfaceContainerLow = Color(0xFF0E0E0E),
    surfaceContainer = CharcoalBlack,
    surfaceContainerHigh = DarkSlate,
    surfaceContainerHighest = SmokeGray,
    outline = SteelGray,
    outlineVariant = SmokeGray,
    error = GlitchRed,
    onError = Color.White,
)

@Composable
fun VoidTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = VoidColors, content = content)
}
