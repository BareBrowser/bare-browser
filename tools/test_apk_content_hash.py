"""Tests for apk-content-hash.py. Run: python3 -m unittest discover -s tools

Each archive is a small zip built in memory; none is a real APK.
"""
import io
import os
import runpy
import unittest
import warnings
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
content_hash = runpy.run_path(os.path.join(HERE, "apk-content-hash.py"))["content_hash"]

DEX = ("classes.dex", b"dex\n035\0code")
APP = [("AndroidManifest.xml", b"<manifest package='org.example'/>"), DEX, ("assets/note.txt", b"hello")]


class ContentHashTest(unittest.TestCase):
    def digest(self, entries, swap=None):
        buf = io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # zipfile warns about a repeated name
            with zipfile.ZipFile(buf, "w") as z:
                for name, data in entries:
                    z.writestr(name, data)
        raw = buf.getvalue()
        if swap:  # stored names or flags zipfile will not write: change them afterwards
            self.assertEqual(raw.count(swap[0]), 2)  # local header and central directory
            raw = raw.replace(*swap)
        return content_hash(io.BytesIO(raw))

    def test_identical_archives_agree(self):
        self.assertEqual(self.digest(APP), self.digest(APP))

    def test_v1_signature_files_are_ignored(self):
        signed = [("META-INF/MANIFEST.MF", b"Manifest-Version: 1.0\n"),
                  ("META-INF/CERT.SF", b"Signature-Version: 1.0\n"),
                  ("META-INF/cert.rsa", b"\x30\x82sig"),
                  ("META-INF/SIG-BARE", b"sig"),
                  ("META-INF/SIG-BARE.x1", b"sig")]
        self.assertEqual(self.digest(APP), self.digest(APP + signed))

    def test_changed_byte_differs(self):
        self.assertNotEqual(self.digest(APP), self.digest(APP[:-1] + [("assets/note.txt", b"hellp")]))

    def test_bytes_moved_between_entries_differ(self):
        two = [("assets/a.bin", b"AAAA"), ("assets/b.bin", b"BBBB")]
        # The second entry folded into the first, as the old stream and as this one would run them together.
        for folded in (b"assets/b.bin" + b"\0" + b"BBBB", b"assets/b.bin" + b"assets/b.bin" + b"BBBB"):
            self.assertNotEqual(self.digest(two), self.digest([("assets/a.bin", b"AAAA" + folded)]), folded)

    def test_other_meta_inf_entries_differ(self):
        self.assertNotEqual(self.digest([DEX, ("META-INF/services/org.example.Plugin", b"org.example.A\n")]),
                            self.digest([DEX, ("META-INF/services/org.example.Plugin", b"org.example.B\n")]))

    def test_sig_names_that_are_not_signature_files_differ(self):
        for name in ("META-INF/SIG-BARE.properties", "META-INF/SIG-BARE.", "META-INF/SIG-BARE.\u212a"):  # Kelvin sign
            self.assertNotEqual(self.digest([DEX, (name, b"a")]), self.digest([DEX, (name, b"b")]), name)

    def test_every_copy_of_a_repeated_name_counts(self):
        self.assertNotEqual(self.digest([DEX, ("assets/a.bin", b"first-1"), ("assets/a.bin", b"second")]),
                            self.digest([DEX, ("assets/a.bin", b"first-2"), ("assets/a.bin", b"second")]))

    def test_bytes_after_a_nul_in_a_name_differ(self):
        self.assertNotEqual(self.digest([DEX, ("assets/a.bin", b"AAAA")]),
                            self.digest([DEX, ("assets/a.bin~.bak", b"AAAA")], swap=(b"a.bin~", b"a.bin\0")))

    def test_same_name_text_stored_as_other_bytes_differs(self):
        # UTF-8 with the flag set, against CP437 0x82 (e acute) with it clear: the same text.
        self.assertNotEqual(self.digest([DEX, ("assets/caf\u00e9.txt", b"AAAA")]),
                            self.digest([DEX, ("assets/caf~.txt", b"AAAA")], swap=(b"caf~", b"caf\x82")))

    def test_same_stored_name_read_as_other_text_differs(self):
        # The same stored bytes, read as UTF-8 and then, with the flag cleared in both headers, as CP437.
        entries = [DEX, ("assets/caf\u00e9.txt", b"AAAA")]
        self.assertNotEqual(self.digest(entries), self.digest(entries, swap=(b"\x14\0\0\x08", b"\x14\0\0\0")))

    def test_entry_is_skipped_only_when_both_names_are_signature_names(self):
        # Stored X\0.SF reads as X; stored X.SF\0x reads as X.SF. Either way one name is not a signature file name.
        for name, swap in (("META-INF/X~.SF", (b"X~.SF", b"X\0.SF")),
                           ("META-INF/X.SF~x", (b"X.SF~x", b"X.SF\0x"))):
            self.assertNotEqual(self.digest([DEX, (name, b"a")], swap=swap),
                                self.digest([DEX, (name, b"b")], swap=swap), name)


if __name__ == "__main__":
    unittest.main()
