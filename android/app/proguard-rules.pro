# youtubedl-android maps yt-dlp's JSON onto these classes with Jackson (reflection).
-keep class com.yausername.** { *; }
-keep class com.fasterxml.jackson.** { *; }
-keepattributes *Annotation*, Signature, InnerClasses, EnclosingMethod
-dontwarn com.fasterxml.jackson.databind.**
-dontwarn org.apache.commons.compress.**
-dontwarn java.beans.**

# ZipUtils (used to unpack Python/ffmpeg on first launch) relies on commons-compress, which
# registers zip extra-field classes reflectively — R8 must leave it intact.
-keep class org.apache.commons.compress.** { *; }
-keep class org.apache.commons.io.** { *; }
-dontwarn org.apache.commons.io.**
