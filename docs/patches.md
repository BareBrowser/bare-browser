# The patch series

The series in [`patches/`](../patches) is 298 files, `0000001.patch` to `0000326.patch`, numbered
in the order they apply. The files carry no descriptions.

`0000210.patch` is not in the series. That number belongs to the Google Play build, which compiles
the update check out. The GitHub build keeps the check. `0000117.patch` is also missing: Chromium 157
removed the code it changed. `0000298.patch` to `0000323.patch` are not in this series either; those numbers belong to the 2.1 line.

From a clean Chromium checkout at the pinned revision, apply all of them in one command:

```bash
git apply --index patches/*.patch
```

The shell expands the glob in filename order, which is the order that matters. The patches are
staged and not committed. Use `git apply`, not `git am`: the files from `0000195.patch` on are plain
diffs without a mail header, which `git am` rejects.
