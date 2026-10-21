# Local Chromium Android Desktop builder

This project uses an x86-64 Ubuntu 22.04 container running locally through Docker Desktop.
The Chromium checkout and build output live in the Docker volume `chromium-android-source`.
The Chromium checkout itself is never pushed anywhere: only the patch series in `patches/`,
the build environment, and the docs are tracked. Build output and APKs stay local.

## Matched snapshot

- Snapshot platform: `AndroidDesktop_arm64`
- Commit position: `refs/branch-heads/8078@{#583}`
- Branched from: `refs/heads/main@{#1706539}`
- Chromium commit: `1228231501697ff7a4a0150ea8ae6df37bb99331`
- Chromium version: `156.0.8078.25`

## Builder commands

```bash
./builder.sh build
./builder.sh start
./builder.sh shell
./builder.sh status
./builder.sh stop
```

Files that need to cross between Linux and macOS go through `exchange/`. Chromium source must
remain in the Linux volume because building from a macOS bind mount is unreliable and slow.

## Bundled extensions

uBlock Origin ships inside the apk, but its `.crx` is kept out of the patch
series: it is a 4MB signed third party binary and base64 in a patch would be
unreviewable. Copy it into the Chromium tree before building:

```
cp third_party/ublock_origin/uBlockOrigin-1.75.0.crx \
   $CHROMIUM_SRC/chrome/browser/resources/bare/ublock_origin.crx
```

Without it the assets target has no input and the build fails at packaging.
See `third_party/ublock_origin/README.md` for provenance, checksum and licence.

## Versioning

Bare's version lives in `VERSION` at the repo root and is independent of the
Chromium underneath it. `tools/version.py` derives everything else from it:

    tools/version.py                # versionName, both versionCodes and tag
    tools/version.py gn arm64       # the two gn args to append to args.gn
    tools/version.py gn arm         # the same, for the 32-bit build

Chromium derives its Android versionCode from its own build number, so two Bare
releases built on the same Chromium would carry the same one. Android compares
only versionCode when deciding whether an APK may replace another, so that
would make updates unrecognisable. Bare owns its own number instead:

    versionCode = 800000000 + MAJOR*1000000 + MINOR*10000 + PATCH*100 + BUILD*10 + ABI

The last digit is the ABI, using Chromium's own values: 0 for arm, 5 for
arm64. That makes the 64-bit APK the higher number of any release, so Android
refuses to replace it with the 32-bit one, and it gives the two APKs the
distinct codes that Play and F-Droid require. `code` and `gn` therefore take
the ABI as an argument; there is no default, so no number can be emitted
without saying which APK it belongs to.

The base clears 799900074, the highest the old Chromium Extend line shipped.
Android refuses a downgrade, so anything below that could not replace an
existing install. Bump `BUILD` for every published artifact, including a rebuild
of the same version. It has a single digit now; `version.py` refuses a tenth
rebuild rather than letting it collide with the next PATCH level.

Both values reach the build through `android_override_version_code` and
`android_override_version_name`, which are plain `declare_args` in
`build/config/android/config.gni`. Append them to `out/<dir>/args.gn` and
re-run `gn gen`; no patch is needed.

## Signing

Release builds are signed with Bare's own key, not the Chromium debug keystore
that `build/android/chromium-debug.keystore` provides by default. That keystore
is checked into Chromium and public, so anything signed with it can be replaced
by an APK anyone can build.

    tools/sign-release.sh out/Bare-arm64/apks/ChromePublic.apk Bare-<version>-arm64-v8a.apk

The key sits outside this repo and its password is in the macOS login keychain,
read only when it signs. Neither is ever written where the build or
the container can see it, and neither belongs in this repository. The signing
certificate's SHA-256 is published with each release so a download can be
checked with `apksigner verify --print-certs`.

Releases from the Chromium Extend line were signed with the debug key, so they
cannot be updated in place by a Bare release. That break is deliberate.

## Storage guardrail

Chromium officially requires at least 100 GB free. Check `./builder.sh status` before checkout and
major builds. Stop if macOS free space approaches 30 GB. Do not prune unrelated Docker images,
volumes, or containers; they belong to other local applications.
