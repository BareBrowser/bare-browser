#!/usr/bin/env python3
"""Compare APK contents while ignoring signing metadata.

Usage:
    tools/apk-content-hash.py app1.apk app2.apk
"""

import hashlib
import sys
import zipfile

V1_SIGNATURE_SUFFIXES = (".sf", ".rsa", ".dsa", ".ec")


def is_v1_signature_file(name):
    # The v1 (JAR) signature files: directly in META-INF, never deeper, with
    # the file name compared case-insensitively. A SIG-* name counts only
    # with no extension, or an extension of one to three ASCII letters or
    # digits.
    if not name.startswith("META-INF/"):
        return False
    rest = name[len("META-INF/"):]
    if "/" in rest:
        return False
    lower = rest.lower()
    if lower == "manifest.mf" or lower.endswith(V1_SIGNATURE_SUFFIXES):
        return True
    _, dot, ext = rest.rpartition(".")
    return lower.startswith("sig-") and (
        not dot or (len(ext) <= 3 and ext.isascii() and ext.isalnum()))


def names(info):
    # An entry has two names: the bytes the archive stores, and the name
    # zipfile reads from them, which can differ (cut at a NUL, decoded by the
    # UTF-8 flag, or replaced by an extra field). orig_filename is the stored
    # bytes decoded as UTF-8 (flag 0x800) or else CP437.
    stored = info.orig_filename.encode(
        "utf-8" if info.flag_bits & 0x800 else "cp437")
    return stored, info.filename.encode("utf-8")


def content_hash(path):
    h = hashlib.sha256()

    def feed(part):
        # Each name and content goes in behind its length, so bytes cannot
        # move from one entry into the next and hash the same.
        h.update(len(part).to_bytes(8, "big"))
        h.update(part)

    with zipfile.ZipFile(path) as z:
        # Every entry that is not a v1 signature file, each copy of a repeated
        # name included. Entries with both names equal keep their archive order.
        for info in sorted(z.infolist(), key=names):
            # The v1 signature lives in META-INF. The v2/v3 blocks live outside
            # the zip structure entirely, between the entries and the central
            # directory, so reading entries never sees them. An entry is
            # skipped only when both of its names are signature file names.
            if (is_v1_signature_file(info.orig_filename)
                    and is_v1_signature_file(info.filename)):
                continue
            for name in names(info):
                feed(name)
            feed(z.read(info))
    return h.hexdigest()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    results = [(p, content_hash(p)) for p in sys.argv[1:]]
    for path, digest in results:
        print("%s  %s" % (digest, path))
    if len(results) > 1:
        same = len({d for _, d in results}) == 1
        print()
        print("identical contents" if same else "CONTENTS DIFFER")
        sys.exit(0 if same else 1)
