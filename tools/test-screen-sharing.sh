#!/bin/bash
# Manual only: compile and run the two capture unit-test classes, without a device.
set -euo pipefail

if [[ $# != 2 || "$(uname -s)" != Linux ]]; then
    printf 'Usage on Linux: bash tools/test-screen-sharing.sh CHROMIUM_SRC OUTPUT_DIR\n' >&2
    exit 1
fi

SOURCE="$(cd "$1" && pwd)"
OUTPUT="$2"
if [[ "$OUTPUT" != /* ]]; then
    OUTPUT="$SOURCE/$OUTPUT"
fi
if [[ ! -f "$SOURCE/content/public/android/BUILD.gn" || ! -f "$OUTPUT/args.gn" ]]; then
    printf 'Provide a patched Chromium checkout and its configured Desktop Android output.\n' >&2
    exit 1
fi
if ! command -v autoninja >/dev/null 2>&1; then
    printf 'Add the matching depot_tools directory to PATH first.\n' >&2
    exit 1
fi
JOBS="${JOBS:-8}"
if [[ ! "$JOBS" =~ ^[1-9][0-9]*$ ]]; then
    printf 'JOBS must be a positive integer.\n' >&2
    exit 1
fi

cd "$SOURCE"
autoninja -C "$OUTPUT" -j "$JOBS" chrome_junit_tests content_junit_tests
"$OUTPUT/bin/run_chrome_junit_tests" --test-filter='*MediaCapturePickerInvokerTest*'
"$OUTPUT/bin/run_content_junit_tests" --test-filter='*ScreenCaptureTest*'
