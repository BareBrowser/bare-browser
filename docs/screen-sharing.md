# Full-display screen sharing

Patch 0205 adds a public Android MediaProjection fallback when Desktop Android has no service-loaded capture picker. It targets Chromium `156.0.8078.25` (`1228231501697ff7a4a0150ea8ae6df37bb99331`), after Bare's existing patch series through 0204.

## What it changes

An eligible `getDisplayMedia()` request shows a browser disclosure naming the requesting website and explaining that other apps and notifications will be visible. Continue opens Android's real capture-consent dialog. Canceling either dialog does not grant capture. The browser dialog text uses Chromium's GRIT resources; technical failure details remain in English.

The fallback requires Android 11 or later and the native `DESKTOP` capture level. A request requiring this tab or excluding monitors is rejected rather than silently widened to the display. Excluding the browser's own tab from a tab picker does not exclude the monitor. Existing secure-context, user-activation, permissions-policy and managed capture checks remain in Chromium. Android's protected-content restrictions are not bypassed.

On Android 14+, the intent requests `MediaProjectionConfig.createConfigForDefaultDisplay()`; earlier supported versions use the public full-display intent. The consent result is handed to `ScreenCapture` before native picker completion. Chromium's native capture thread, foreground notification, RGBA frame ownership and native stop path are retained. A display listener handles full-display rotation before Android 14; later versions retain the captured-content resize callback.

## Lifetime and failure handling

- One fallback request or session owns the pipeline at a time. Consent callbacks survive Activity recreation within the same task, but not process death. A destroyed native request or tab cannot complete the picker.
- If a request disappears while Android consent is open, ownership stays with that prompt until its result returns. A late result is not delivered to a newer website request.
- Foreground-service startup and the first frame each have a 15-second limit. Failures use a local dialog with **Copy report**. Reports contain API level, elapsed times, fixed stage names and exception classes, not URLs, accounts, permission-intent contents or exception messages. Nothing uploads them automatically.
- A grant not consumed by native capture within 30 seconds is discarded. Since the existing native handoff is a process-global slot without a request ID, this timeout deliberately keeps session ownership locked until the browser process restarts. Releasing it could let a late old capturer consume a newer grant. Normal stop/start and ordinary startup failures release ownership normally.
- The pinned native I420 callback is unimplemented. Unsupported formats stop capture and release the frame rather than presenting a stream that produces no usable frames. This guard also affects the shared capturer used by other picker implementations.

## Limits

This is full-display **video**, not a tab picker or system-audio implementation. Microphone and camera requests remain separate. The existing Android `WINDOW` transport is reused, so JavaScript may report `displaySurface: "window"` even when the display is being captured. Sites that require another surface type may refuse it. Android 10 can run Bare but cannot use this fallback. This patch does not change Bare's package identity, signing, update behavior or build configuration.

## Validation

On 2026-10-25, Bare plus patch 0205 built successfully for ARM64 from commit `382c268b8356e5a9541670f7ece881e89ecad3fa`. The test APK, version `1.0.1-pr127.1`, changed only the package/version GN arguments for side-by-side installation; it contained no downstream profile source changes.

The user installed this PR build on their Huawei tablet and confirmed screen sharing works. Automated unit tests were not run; the checklist below is available for further regression coverage.

## Repeating the checks

Prepare a separate Linux Chromium checkout using [BUILDING.md](../BUILDING.md), apply the complete Bare series including 0205, and configure it for Desktop Android. Do not apply the downstream capture patches as well. Build `chrome_public_apk` using that checkout's normal build command; a successful APK build does not run unit tests.

The optional helper below explicitly compiles `chrome_junit_tests` and `content_junit_tests`, then runs only `MediaCapturePickerInvokerTest` and `ScreenCaptureTest`. Pass the Chromium source directory and its already configured output directory. It does not install an APK or operate a device. Run it only when no other build is using that output:

```bash
bash tools/test-screen-sharing.sh /path/to/chromium/src out/Bare-arm64
```

The updated tests cover capture-policy filtering, session ownership, handoff timeout and unsupported-frame handling. They do not establish the end-to-end behavior of Android's system consent UI. On a manually installed test build, record the device, Android version and results for:

1. Start an HTTPS `getDisplayMedia()` request from an explicit tap, for example with the [WebRTC sample](https://webrtc.github.io/samples/src/content/getusermedia/getdisplaymedia/). Confirm the website disclosure and a separate Android consent prompt.
2. Cancel each dialog separately, then retry. Neither cancellation should leave a stream or capture notification active.
3. Approve capture, check moving frames and switch to another ordinary app. Check portrait/landscape rotation with the browser foregrounded and backgrounded. Protected windows may be black by Android design.
4. Stop from the website and, on a separate attempt, from Android's capture notification. Confirm the stream and indicators end, then start another request.
5. Make a second request during capture. It must not disturb the first stream or steal its grant.
6. Rotate while Android consent is open. Close or navigate the original tab where the UI allows it; a later result must not start capture for another website. Also exercise native request teardown before consent returns.
7. Check policy-restricted, current-tab-only and monitor-excluded requests. They must not gain full-display capture.
8. Exercise a real conferencing call and confirm the remote participant sees moving frames and rotation. Test microphone and camera independently.
9. Check Android 11–13 rotation and Android 14+ consent/resize behavior separately; verify Android 10 rejects the fallback cleanly. Record any unavailable coverage rather than assuming it passed.

On failure, use **Copy report** with the action that preceded it. A native-handoff-timeout report requires restarting the browser process before retrying, as the report explains.
