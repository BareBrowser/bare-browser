<div align="center">

<img src="assets/logo_bare_blend.png" width="132" alt="">

# Bare Browser

**Shaped by the community**

**Extensions. Privacy. Freedom**

[barebrowser.org](https://barebrowser.org)

</div>

---

Bare is a de-Googled Chromium build for Android, designed to give you more privacy, control and
freedom on the web. It strips Google tracking, telemetry and AI integration while keeping
powerful features like browser extensions and uBlock Origin. Bare also adds background video
playback, the ability to save media from sites that normally block it, support for choosing your
preferred download manager, and much more.

It is a patch series rather than a fork: 128 patches against one pinned revision of **Chromium
Desktop Android**, so what this repository holds is exactly the difference between stock Chromium
and Bare, and nothing else.

Built and used on a Pixel 10 Pro XL. Not affiliated with Google or the Chromium project.

- **Base:** Chromium `153.0.8010.27` (commit `ac9b84a0`)
- **Target:** `is_desktop_android = true`, `target_cpu = "arm64"` and `"arm"`
- **Version:** `1.0.0-alpha.3`, versionCode `801000065` (arm64) / `801000060` (32-bit arm)
- **Size:** 128 patches, 14,605 insertions across 341 files

## What you get

- **Real browser extensions.** Bitwarden, Dark Reader, uBlock Origin: the desktop ones, on your
  phone. Pin the ones you use to the toolbar.
- **[uBlock Origin](https://github.com/gorhill/uBlock), already installed.** The full version,
  not Lite, because Bare keeps Manifest V2 working. Shipped exactly as its author publishes
  it. Remove it like anything else if you would rather not have it.
- **No telemetry, no AI, no sign-in prompts.** DuckDuckGo is the default from first launch. Two
  things still reach a server on their own, and both are named in
  [Network behaviour](#network-behaviour) rather than glossed over.
- **Save what a page is playing.** Long press a video or an audio player and Bare offers you the
  file, including on sites that stream in pieces and normally offer nothing at all.
- **Video keeps playing in the background.** Lock the phone or switch apps and the audio carries
  on, for sites that support it.
- **Your download manager, if you want one.** Hand downloads to 1DM or similar instead of the
  browser, or leave it off and keep them in Bare.
- **Links open in the browser, not in apps.** A Reddit or YouTube result stays where you are.
  Phone numbers and email links still open the right app.
- **Video that behaves.** H.264 and AAC are included. Fullscreen follows your rotation lock
  instead of forcing landscape, and clears the camera cutout instead of sitting beside it.
- **Dark stays dark.** No white flash while a page loads on a dark theme. There is also an
  optional setting to have Bare darken light sites itself.
- **Add your own search engine.** Chromium ships the add-engine screen on Android but leaves it
  switched off. It is on here, under Settings, Search engine, Manage search engines.

## Screenshots

| | |
| --- | --- |
| <img src="assets/screenshots/welcome-screen.png" width="260"> | <img src="assets/screenshots/new-tab-noai.png" width="260"> |
| The welcome screen, where the choices are made | A new tab, with no logo to fetch |
| <img src="assets/screenshots/ublock-origin-popup.png" width="260"> | <img src="assets/screenshots/extension-toolbar.png" width="260"> |
| uBlock Origin, the full version | Extensions in the toolbar |
| <img src="assets/screenshots/save-image-menu.png" width="260"> | <img src="assets/screenshots/download-video-menu.png" width="260"> |
| Saving an image | Saving video a site does not offer |
| <img src="assets/screenshots/video-download-dialog.png" width="260"> | <img src="assets/screenshots/clean-address-bar.png" width="260"> |
| Picking a stream to keep | The address bar |
| <img src="assets/screenshots/toolbar-shortcuts.png" width="260"> | <img src="assets/screenshots/toolbar-tap-hold-actions.png" width="260"> |
| Arranging the toolbar | A second action on a hold |
| <img src="assets/screenshots/toolbar-swipe-action.png" width="260"> | <img src="assets/screenshots/open-links-in-apps.png" width="260"> |
| A sideways drag along the bar | Whether links leave for an app |
| <img src="assets/screenshots/theme-settings.png" width="260"> | <img src="assets/screenshots/clear-on-exit.png" width="260"> |
| Themes, including AMOLED | Choosing what Exit deletes |
| <img src="assets/screenshots/tab-view-setting.png" width="260"> | <img src="assets/screenshots/tab-list-view.png" width="260"> |
| Grid or list | Tabs as a list |

## Support the project

Bare is one person and one phone. There is no company behind it, nothing in the browser sells
you anything, and there is nothing to upsell you to later, which is rather the point of it.

If it is useful to you, you can buy me a coffee. Entirely optional. It buys build hours and a
second device to test on, and it changes nothing about the browser either way.

<a href="https://buymeacoffee.com/sheshtawy">
  <img src="assets/bmc-button.png" width="200" alt="Buy me a coffee">
</a>

## Why

Chromium's Desktop Android build supports real browser extensions, which mobile Chrome does
not. That makes it a genuinely better browser to live in, but it still ships Google's AI
stack, phones home on a schedule, and hands your links to other apps. Bare fixes that as a
patch series rather than a fork, so every change stays readable and reviewable.

## What the patches do

A hundred and twenty-eight patches against one pinned Chromium revision: crash fixes, the
extensions toolbar on phone layouts, every Google callback and AI surface removed, and the
features Bare adds on top.

**[The full list, patch by patch, is in docs/patches.md](docs/patches.md)** along with what is
removed by build flag instead of by patch, and what is deliberately kept.

## Network behaviour

Measured on a Pixel 3 running Android 12 and an Android 17 emulator, by watching the sockets
opened under Bare's own uid on a wiped profile. What follows is what was actually observed, not
what was intended.

**On a second and later start, with an established profile, one host is contacted without being
asked: `update.googleapis.com`.** That is Chromium's component updater. It is kept deliberately,
because the components left registered are the ones that carry security or web compatibility:

| Component | Why it stays |
| --- | --- |
| CRLSet | certificate revocation |
| PKIMetadata | Certificate Transparency |
| SSLErrorAssistant | quality of the TLS interstitial |
| FileTypePolicies | download danger classification |
| OriginTrials | web compatibility |
| Widevine | DRM playback |
| SafetyTips, CrowdDeny | lookalike-domain and abusive-notification lists, applied locally |

Registration tells Google an install exists, along with a component id, a version, an install
date and a cohort. Twelve other components were dropped in patch 0085 for buying nothing here:
the Privacy Sandbox set, Google's omnibox suggestion model, the optimization-hints feed, shopping
and checkout heuristics, on-device AI history strings, and two Safe Browsing lists that nothing
can consult. Three more, ActorSafetyLists, Indigo and CaptchaProvider, are still registered
because their purpose is not clear enough in the tree to remove them confidently.

**On the first run of a fresh profile there is more, and almost all of it is uBlock Origin**
fetching the filter lists it ships enabled, from the list maintainers and their CDNs rather than
from Google. That happens once and then on the extension's own schedule.

**The update check contacts GitHub**, and only after the welcome screen has been completed and an
update preference stored. It is at most one request a day, to a public release feed. It sends two
headers, `User-Agent: Bare/<version>` and `Accept: application/atom+xml`, so the request does say
which version is asking. What it carries beyond that is nothing that identifies you or the phone:
no cookies, no installation identifier, no device model, no Android build. The platform default
User-Agent would have carried the model and the build, so it is replaced. Choosing manual means
nothing leaves the device until the Check for updates row is tapped.

**What no longer happens**, each verified by re-running the same capture:

- No Firebase or InstanceID registration. A fresh profile previously fetched two FCM tokens for
  Chromium's cloud-policy invalidation projects and kept them in shared preferences as durable
  identifiers. Patches 0081 and 0086 removed both consumers; the token files are no longer
  created at all.
- No lookup against `accounts.google.com`, from the omnibox or at startup. Typing in the address
  bar used to reach GAIA ListAccounts to decide whether to personalise suggestions. Separately, a
  fresh profile used to POST to ListAccounts about a tenth of a second into every cold start,
  before the welcome screen had been answered. Neither the omnibox nor the account reconcilor was
  behind the startup one: two services asked for the cookie jar while the profile was still being
  built, both only to report metrics, and reading the cookie jar fetched it from Google whenever
  the cached answer was stale. Patch 0093 stops the read from reaching the network, so the answer
  now comes from the cache. Visiting Google sites and signing in to them is unaffected.
- No Safe Browsing traffic. There was never any: see below.

Traffic from Android itself and from Google Play Services is separate from all of this and is not
affected by anything Bare does.

**Safe Browsing does not work in this build, and no longer claims to.** Chromium Android performs
lookups through a handler that Google injects in its own build and that no public build has. The
settings, the Safety Hub module and the promotional cards all described protection that never
ran, so patch 0080 removed them. Bare shows no phishing or malware interstitial. Treat unknown
links with the caution you would give a browser with no such feature, because that is what this
is.

## Requirements

- Docker, with at least **32 GB** allocated to the VM. At 16 GB a full build is
  reliably OOM-killed partway through.
- ~100 GB free disk. The Chromium checkout alone is ~50 GB.
- An arm64 Android device for testing.

Builds run in an x86-64 Ubuntu 22.04 container. On Apple Silicon this means Rosetta
emulation, and a full build takes hours.

## Build it yourself

Everything runs in the container. The Chromium checkout stays in its volume, because building
from a macOS bind mount is slow and unreliable; only small files cross to the host, through
`exchange/`, which is the one directory shared with the container.

**1. Start the container.**

```bash
./builder.sh build
./builder.sh start
```

**2. Put what the build needs where the container can see it.**

```bash
cp -R patches exchange/
cp third_party/ublock_origin/uBlockOrigin-1.75.0.crx exchange/
tools/version.py gn arm64 > exchange/version-args.gn
```

**3. Fetch Chromium.** Inside the container (`./builder.sh shell`). depot_tools is on the PATH
but not installed, so clone it first. This part is Chromium's own procedure rather than
anything specific to Bare. See the upstream [Android build
instructions](https://chromium.googlesource.com/chromium/src/+/main/docs/android_build_instructions.md)
if a step needs explaining. Expect hours and about 50 GB.

```bash
git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git ~/depot_tools
mkdir -p /work/chromium && cd /work/chromium
fetch --nohooks android
cd src
git checkout ac9b84a0b321cc741e9eb650f29e7177b68f0f48
gclient sync -D --force --reset
./build/install-build-deps.sh --android
```

**4. Apply the series, and drop in the extension.** uBlock Origin is kept out of the patches
because a 4 MB signed binary as base64 would be unreviewable, so it is copied in separately.
Without it the build fails at packaging.

```bash
git am /exchange/patches/*.patch
mkdir -p chrome/browser/resources/bare
cp /exchange/uBlockOrigin-1.75.0.crx chrome/browser/resources/bare/ublock_origin.crx
```

**5. Configure.** This is the complete configuration the published release was built with,
nothing omitted:

```gn
target_os = "android"
target_cpu = "arm64"
is_desktop_android = true
is_official_build = true
is_debug = false
is_java_debug = false
is_component_build = false
dcheck_always_on = false
android_static_analysis = "off"
symbol_level = 0
blink_symbol_level = 0
v8_symbol_level = 0
use_remoteexec = false
use_reclient = false

proprietary_codecs = true
ffmpeg_branding = "Chrome"

use_mlkit_for_aicore = false
enable_glic_internal_resources = false
enable_reporting = false
enable_service_discovery = false
enable_mdns = false
enable_arcore = false
enable_cardboard = false
enable_openxr = false

disable_fieldtrial_testing_config = true

chrome_public_manifest_package = "org.barebrowser"
android_override_version_code = "801000065"
android_override_version_name = "1.0.0-alpha.3"
```

The last two lines are what `tools/version.py gn arm64` emits, and they matter: they are written into
the manifest, so a build without them will not match the release.

`disable_fieldtrial_testing_config` matters as much. Without it the build follows
`testing/variations/fieldtrial_testing_config.json` instead of the code defaults, and several
patches here are inert. [docs/build-constraints.md](docs/build-constraints.md) has the four
behaviours that came from that file rather than from the code.

The 32-bit build differs in exactly three lines: `target_cpu = "arm"`, the version code
`801000060` that `tools/version.py gn arm` emits, and `clang_use_default_sample_profile = false`,
which stops GN demanding an AFDO profile this checkout never syncs.

```bash
mkdir -p out/Bare
$EDITOR out/Bare/args.gn          # paste the block above
gn gen out/Bare
autoninja -C out/Bare chrome_public_apk
```

**6. Compare.** Your APK will not be byte-identical to the published one, because that one
carries a signature only its key can produce. Everything else should match:

```bash
tools/apk-content-hash.py out/Bare/apks/ChromePublic.apk Bare-1.0.0-alpha.3.apk
```

See [BUILDING.md](BUILDING.md) for the rest of the workflow, including versioning and how
releases are signed.

## Verifying a build

Three questions, and they have different answers.

**Is this the file that was published?** Compare its SHA-256 against the one on the release page.
That catches a truncated or tampered download and nothing else: the hash is published by the same
person as the file, so on its own it proves nothing about where the file came from.

**Is it genuinely Bare?** Check who signed it. Nothing signed by any other key is Bare.

```bash
apksigner verify --print-certs Bare-1.0.0-alpha.3.apk
```

    SHA-256  ae:2a:0e:7f:b7:a1:32:ec:51:7d:26:a8:e7:c8:3d:27
             5e:83:74:7b:0a:77:7d:4a:42:22:5b:1d:34:32:71:a0
    subject  CN=Bare Browser, O=Bare Browser, OU=Release
    key      RSA 4096

**Releases before `v1.0.0-alpha.1` were signed with Chromium's debug key**, which is checked into
Chromium's tree and therefore public. Anyone can build an APK that installs as an update over one
of those. If you are running a Chromium Extend build, uninstall it rather than updating; a Bare
release cannot replace it in place anyway, because the signing identity deliberately changed.

**Can you rebuild it yourself?** Yes, and that is the only one of the three that proves where a
binary came from. The signature is deliberately not reproducible, since nobody but the key holder
can produce it, but everything else is. Follow [Build it yourself](#build-it-yourself) exactly,
including the version arguments, then compare:

```bash
tools/apk-content-hash.py out/Bare/apks/ChromePublic.apk Bare-1.0.0-alpha.3.apk
```

It hashes every entry except the signature, so two builds of the same source agree whoever signed
them. [What has been measured, and what has not](docs/reproducibility.md).

## Known limitations

- **Extension popups can be cropped.** Extensions auto-size their popup to content and may
  request a width wider than a phone screen. `kMaxSize` in
  `chrome/browser/ui/android/extensions/extension_action_popup_contents.cc` is hardcoded to
  800dp. Two attempts to bound it failed; the second stopped popups rendering entirely, so
  both were reverted. Needs instrumenting rather than guessing.
- **The omnibox is squeezed** when several extensions are pinned. `ToolbarPhone` has none of
  the `ToolbarWidthConsumer` negotiation `ToolbarTablet` uses. Unpinning all but one extension
  works around it.
- **Links leave for an app only when you say so.** Patch 0005 kept every `http(s)` navigation
  in the browser; 0107 turned that into a setting, Never by default, and 0110 judges a web page
  wrapped in an `intent://` as the page rather than the wrapper. On Never, an OAuth flow or deep
  link that expects an app handoff will not get one, and the app menu is the way to reach the
  app. `tel:`, `mailto:` and `sms:` are untouched by any of it.
- **The DuckDuckGo default only applies to new profiles.** Patch 0014 seeds the default at
  first run. An existing profile has `kDefaultSearchProviderData` persisted and
  `DefaultSearchManager` prefers it, so upgrading over an older install keeps Google until you
  change it in Settings → Search engine.
- **The New Tab Page still has Discover.** The Google logo, the promo cards and the AI Mode
  button are gone; Discover remains.
- **External downloads lose your sign-in.** With "Use an external download manager" on, a file
  that requires you to be signed in will fail in the other app: the interception point in
  `ChromeDownloadManagerDelegate` carries no cookie. Passing credentials needs a different
  interception layer, not an extra argument. The setting's own summary says so.
- **Passkeys work, but only through a third-party password manager, and only after you trust
  Bare once.** Two different APIs are involved. Google's own path,
  `Fido.FIDO2_PRIVILEGED_API`, is restricted to Google-signed browsers, so a self-built
  Chromium is refused with `ApiException: 17`; passkeys held in Google Password Manager are
  therefore out of reach, and no patch here can change that. Android's Credential Manager is a
  separate path and it does reach third-party providers such as Bitwarden, 1Password and Proton
  Pass. Those providers only complete a passkey for a browser they recognise, keyed on package
  name plus signing certificate, and Bare is not on any published list yet. The first attempt
  fails with "browser is not recognized"; choose **Trust** when prompted, or add
  `org.barebrowser` by hand under Bitwarden → Settings → Autofill → **Privileged apps**. If you
  had trusted an earlier self-built Bare you will see "browser signature does not match"
  instead, because release builds are signed with a different key than local ones: delete the
  stale entry, then trust it again.
- **Web Push is gone**, as a consequence of removing the GCM channel in patch 0007.
- **Password managers need one setting turned on.** Chromium uses its own autofill by default
  and never consults Android's autofill framework, so Bitwarden, 1Password and similar are
  simply never asked. Turn on Settings → Autofill options → use another service and they work.
  This is upstream behaviour, not something these patches introduce; the availability check
  also refuses Google's own autofill service, so the path is third-party only.
- **A custom search engine has no logo on the new tab page.** Engines added by hand carry no
  logo image, so the page shows none. Cosmetic only.
- **A downloaded adaptive stream arrives as two files.** Sites that stream video split the sound
  into a separate track, so Bare offers the video and the audio as two downloads and leaves you
  to put them together. Joining them in the browser means demuxing and remuxing both, which is
  built out of pieces already in the tree but is not built yet.
- **Segmented HLS and DASH offer nothing.** A `.m3u8` or `.mpd` is a list of where the pieces
  are, and a lone `.ts` or `.m4s` segment is not playable on its own, so both are refused rather
  than handed over as a download that would disappoint. Assembling a segmented stream is the same
  missing job as above.
- **This is not a YouTube downloader.** YouTube keeps audio and video in separate streams and
  asks for them in ranges Bare does not reassemble, so it will not produce a usable file there.
  [Seal](https://github.com/JunkFood02/Seal), a yt-dlp front end, is the right tool for that.
- **On a site that never reloads, the offered video may be one you scrolled past.** Feeds navigate
  without loading a new document, so what the tab fetched accumulates, and Bare offers whichever
  video it pulled the most of. Usually that is the one you watched. Not always.
- **Protected streaming is unproven.** Widevine is detected, and a DRM test page reports it
  as the available key system, but paid playback has never been exercised end to end. Treat
  Netflix and the like as untested rather than working.
- **DRM-protected media cannot be downloaded**, and nothing here tries. Everything Bare offers is
  a file the page already fetched in the clear.
- **The first incognito tab of a session is slow to appear**, showing a blank panel or a fade
  before it settles. Measured, understood, not yet fixed.
- **Third-party autofill can stop being offered** until you navigate away and back. Bitwarden has
  been seen to go quiet mid-session with no error anywhere; the silent early return that causes
  it is known, the reason it triggers is not.
- **No x86 build**, so an emulator cannot install it. arm64 and armeabi-v7a are both released.

## Not done yet

Each is described in [docs/build-constraints.md](docs/build-constraints.md):

- Safe Browsing, blocked by one un-gated call site in the Android JNI bridge
- Google XR SDKs (ARCore, Cardboard, VrCore, OpenXR), blocked by three omnibox call sites;
  the flags are coupled in both directions and there is no GN-only configuration that works
- `build_with_model_execution`, `enable_supervised_users`, `enable_offline_pages`, each
  blocked by a single GN `assert()`
- The New Tab Page still carries Discover. The AI Mode button is gone: 0025 turned it off by
  default and 0113 stopped it depending on the search engine. Its Google logo is gone as a side
  effect of 0014, the NTP logo follows the default search engine
- ARCore, Cardboard and Daydream manifest entries persist from library manifests, though their
  code is gone

### Already inert, no work needed

Worth knowing before anyone patches them: a public (non-Chrome-branded) Chromium build already
sends no usage metrics, no URL-keyed metrics and no crash reports, because upstream withholds
those endpoints from forks. Translate is likewise disabled without a Google API key. Details and
evidence are in [docs/build-constraints.md](docs/build-constraints.md).

## Repository layout

```
patches/                 the patch series, applied in order
docker/                  container image definition
docker-compose.yml       build environment
builder.sh               container wrapper
assets/                  logo, screenshots and the support button used in this README
tools/                   version numbers, release signing, build comparison
VERSION                  Bare's version, independent of Chromium's
third_party/             uBlock Origin as shipped, with its provenance
docs/patches.md          what every patch does
docs/reproducibility.md  what rebuilding has and has not proven
docs/build-constraints.md  what a build flag cannot switch off, and what upstream already did
```

The Chromium checkout, build output, and APKs are not tracked: they live in a Docker volume
and would be far past GitHub's file size limits.

## Credits

Bare is a thin layer on other people's work.

**[Chromium](https://www.chromium.org/)** is the browser. The patches modify its source and are
therefore subject to its **BSD-3-Clause** licence. See the
[Chromium LICENSE](https://chromium.googlesource.com/chromium/src/+/main/LICENSE).

**[uBlock Origin](https://github.com/gorhill/uBlock)**, by Raymond Hill and contributors, is
licensed under the **GPL-3.0** and ships inside the apk. It is the extension exactly as its
author publishes it: downloaded from the Chrome Web Store, unmodified, not repackaged and not
re-signed, so it keeps its original extension id and his signature. The licence text travels
inside it, the corresponding source is the upstream release, and provenance and checksum are in
[third_party/ublock_origin](third_party/ublock_origin). Bundling it beside a BSD project is mere
aggregation; uBlock Origin remains under the GPL and Bare's licence does not touch it. Bare is
not affiliated with or endorsed by the uBlock Origin project.

**[Titanium](https://github.com/jqssun/android-titanium-browser)**, by jqssun, is built from the
same `is_desktop_android` target and ships to phones, which makes it a working reference for the
places Chromium still treats that target as a desktop. Patch 0078 came out of reading its
`patch.sh`, which showed which two files gate the omnibox verbatim match. The edits here came out
different: Titanium switches both off, Bare keeps a device check where the code allows one.

**[Cromite](https://github.com/uazo/cromite)** and
**[ungoogled-chromium](https://github.com/ungoogled-software/ungoogled-chromium)** were used as
reference throughout. Finding every call site that reaches a Google service is the hard part of
this work, and both projects had already found many of them. A couple of the patches here do the
same job as theirs.

`assets/logo_bare_blend.svg` and `assets/logo_bare_blend.png` are the Bare mark and belong to
this project.

Chromium is a trademark of Google LLC. Bare is unaffiliated with Google or the Chromium project,
and is not Chromium.
