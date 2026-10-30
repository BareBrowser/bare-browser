# The patch series

The series in [`patches/`](../patches) is 217 files, `0000001.patch` to `0000218.patch`, numbered
in the order they apply. The files carry no descriptions.

`0000210.patch` is not in the series. That number belongs to the Google Play build, which compiles
the update check out. The GitHub build keeps the check.

From a clean Chromium checkout at the pinned revision, apply all of them in one command:

```bash
git apply --index patches/*.patch
```

The shell expands the glob in filename order, which is the order that matters. The patches are
staged and not committed. Use `git apply`, not `git am`: the last two files are plain diffs
without a mail header, which `git am` rejects.
