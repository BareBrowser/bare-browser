# Build Bare from source

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
git checkout 2f9a11097447f226133bc1a31c787291a5eeab98
gclient sync -D --force --reset
./build/install-build-deps.sh --android
```

**4. Apply the series, and drop in the extension.** uBlock Origin is kept out of the patches
because a 4 MB signed binary as base64 would be unreviewable, so it is copied in separately.
Without it the build fails at packaging.

```bash
git apply --index /exchange/patches/*.patch
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
android_override_version_code = "802000025"
android_override_version_name = "2.0.0-beta.2"
```

The last two lines are what `tools/version.py gn arm64` emits at this release (run it to get them, rather
than trusting the numbers here), and they matter: they are written into the manifest, so a build
without them will not match the release.

`disable_fieldtrial_testing_config` matters as much. Without it the build follows
`testing/variations/fieldtrial_testing_config.json` instead of the code defaults, and several
patches here are inert. [docs/build-constraints.md](build-constraints.md) has the four
behaviours that came from that file rather than from the code.

The 32-bit build differs in exactly three lines: `target_cpu = "arm"`, the version code
`802000020` that `tools/version.py gn arm` emits, and `clang_use_default_sample_profile = false`,
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
tools/apk-content-hash.py out/Bare/apks/ChromePublic.apk Bare-2.0.0-beta.2-arm64-v8a.apk
```

See [BUILDING.md](../BUILDING.md) for the rest of the workflow, including versioning and how
releases are signed.

## Verifying a build

Three questions, and they have different answers.

**Is this the file that was published?** Compare its SHA-256 against the one on the release page.
That catches a truncated or tampered download and nothing else: the hash is published by the same
person as the file, so on its own it proves nothing about where the file came from.

**Is it genuinely Bare?** Check who signed it. Nothing signed by any other key is Bare.

```bash
apksigner verify --print-certs Bare-2.0.0-beta.2-arm64-v8a.apk
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
tools/apk-content-hash.py out/Bare/apks/ChromePublic.apk Bare-2.0.0-beta.2-arm64-v8a.apk
```

It hashes every entry except the signature, so two builds of the same source agree whoever signed
them. [What has been measured, and what has not](reproducibility.md).
