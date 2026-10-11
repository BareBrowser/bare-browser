# uBlock Origin

Bare ships uBlock Origin so that content blocking works the moment the browser
is installed. It is pre-installed but not pinned, and it can be disabled or
removed like any other extension.

## What this is

`uBlockOrigin-1.75.0.crx` is the extension exactly as its author publishes it,
downloaded from the project's GitHub release. Nothing in it has been changed,
repackaged or re-signed.

    version   1.75.0
    id        fkgkibajhfbepljeaefdnfnegdcjomkh
    source    https://github.com/gorhill/uBlock/releases/tag/1.75.0
              (uBlock0_1.75.0.chromium.crx)
    sha256    see uBlockOrigin-1.75.0.crx.sha256, which matches the digest
              GitHub publishes for that asset

The Chrome Web Store stopped carrying Manifest V2 extensions on 31 August 2026,
and 1.74.0 was the last release uploaded there. Bare shipped the store's copy up
to 1.73.0, under the store id `cjpalhdlnbpafiamejdnhcphjbkeiagm`. The author
signs his own builds with a different key, so this copy has a different id.
When a profile that has the store copy is upgraded, Bare moves its settings
across to this one and then removes the old copy. A profile whose user removed
the store copy does not get this one either.

## Updates

The manifest's `update_url` points at the author's update file on jsDelivr
(`cdn.jsdelivr.net/gh/gorhill/uBlock@master/dist/chromium/update.xml`), which
names the latest stable release on GitHub. Chromium's extension updater checks it
about every five hours and installs newer versions from github.com. Filter lists
update separately, from uBlock Origin's own list sources.

## Licence

uBlock Origin is copyright Raymond Hill and contributors, and is licensed under
the **GNU General Public License v3.0**. The full licence text ships inside the
extension as `LICENSE.txt`.

Bare itself is BSD licensed. Distributing the two together is mere aggregation:
uBlock Origin remains under the GPL and Bare's licence is unaffected. Because
the extension is redistributed unmodified, the corresponding source is the
upstream release:

    https://github.com/gorhill/uBlock/releases/tag/1.75.0

## Changing the version

Replace the `.crx`, refresh the `.sha256`, and update the id, version and file
name in `chrome/browser/extensions/bare_bundled_extensions_loader.cc`.
