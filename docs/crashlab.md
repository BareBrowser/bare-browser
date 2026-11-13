# Bare CrashLab

CrashLab is Bare built with `bare_diagnostics = true`. It installs next to Bare as
`org.barebrowser.crashlab`, has its own profile, and carries an orange icon with a pulse badge.

It writes a log of each session to Downloads, named `bare-crashlab-<date>-<time>.txt`. The file is
written as the session runs, so it is there after a crash, a kill or a normal exit. It holds the
app's own logcat, Java crashes, lifecycle events, a status line every 30 seconds, and a header with
the Bare version, device, Android version and memory. On Android 11 and newer the header also says
how the previous session ended.

Page addresses are cut to scheme and host before they are written. The file stays on the phone.
Nothing is sent anywhere.

A native crash cannot write to the file, so it shows as the last lines before the crash plus the
previous session note in the next log. The renderer and GPU processes run under their own user and
are not in the app's logcat.

Every GitHub release since 2.0.0-beta.5 has a CrashLab APK for each ABI. The Play build does not
have one.

Version codes for 2.0.3: 802000317 for arm64, 802000312 for 32-bit ARM.
