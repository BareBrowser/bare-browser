# What the build flags cannot do, and what upstream already did

Two kinds of finding end up here. Things a GN flag looks able to switch off and
cannot, which is why some Google code is still compiled into Bare. And things
that look like they need a patch and do not, because a Chromium build outside
Google's own branding never had them.

Both matter to anyone reading the patch series and wondering why a particular
thing is missing from it.

## The XR group is coupled in both directions

`enable_arcore`, `enable_cardboard` and `enable_openxr` are accepted by
`gn gen` and then fail a full build. There is no GN-only configuration that
removes Google's XR SDKs from an Android build.

`enable_vr` is not independent. Its default is derived, in
`device/vr/buildflags/buildflags.gni`:

```gn
enable_vr = enable_openxr || enable_cardboard || enable_arcore || (is_linux && ...)
```

Turn the backends off and `enable_vr` follows them false, and then the omnibox
stops compiling:

```
searchbox_handler.cc:897 / :969  no member named 'GetVectorIcon' in 'AutocompleteMatch'
omnibox_edit_model.cc:1947       no member named 'GetVectorIcon' in 'AutocompleteMatch'
```

Both declarations sit behind
`#if (!BUILDFLAG(IS_ANDROID) || BUILDFLAG(ENABLE_VR)) && !BUILDFLAG(IS_IOS)`, so
an Android build wants `ENABLE_VR` for a reason that has nothing to do with VR.
Patch 0000008 guards those call sites so the flags can go off.

Manifest entries for ARCore, Cardboard and Daydream still arrive from library
manifests even with the code gone. They name components that are not there.

## Three flags each blocked by a single assert

`build_with_model_execution`, `enable_supervised_users` and
`enable_offline_pages` are each held on by one GN `assert()` rather than by
anything that needs them. Turning any of them off stops the build at the assert.

## Safe Browsing

One un-gated call site in the Android JNI bridge holds it in. Patches 0000077, 0000084
and 0000087 remove the settings surfaces that advertise it, since a row that offers
a protection level nothing implements is worse than no row.

## What a fork already does not send

Worth knowing before anyone writes a patch for it: a Chromium build that is not
Google-branded already sends no usage metrics, no URL-keyed metrics and no crash
reports. Upstream withholds the endpoints from forks rather than gating the code.

**Metrics.** `components/metrics/server_urls.cc` reads every endpoint from a
GRIT resource, and the public `server_urls.grd` carries a `-` placeholder for
each, which `GetUrl()` turns into an empty `GURL()`. The file says why: the real
URLs live in an internal grd "to prevent Chromium forks from accidentally
sending metrics to Google servers."

**Crash upload.** `components/crash/core/app/crash_reporter_client.cc`:

```cpp
std::string CrashReporterClient::GetUploadUrl() {
#if BUILDFLAG(GOOGLE_CHROME_BRANDING) && defined(OFFICIAL_BUILD)
  return kDefaultUploadURL;   // https://clients2.google.com/cr/report
#else
  return std::string();
#endif
}
```

**Translate** needs a Google API key and does not have one here. Chrome's translation is Google's
`element.js` and `translate.googleapis.com`, and it is the key that authorises that, so there is
nothing to restore without a key of Bare's own and a standing arrangement with Google. 0000174 offers
something else instead: Settings, Translate pages takes the address of a LibreTranslate-compatible
server, and the menu's Translate sends the page text there. Bare ships no server and no default
address. The server sees the text of every page you translate, and its quality and its terms are
its own.

This is also why the first-run screen had to go rather than be reworded. Its
footer said the browser "sends usage and crash data to Google", which was untrue
of the binary it shipped in. A build that claims to send data it cannot send is
worse than one that says nothing, so patches 0000015 and 0000039 removed the screen
and 0000040 replaced it with one that describes what this build actually does.

## Field trials

Bare is not Google-branded, so upstream compiles
`testing/variations/fieldtrial_testing_config.json` into the build and the
browser follows whichever experiment arm that file names rather than the code
defaults. Official Chrome is exempted by its branding; Bare has to say so
itself. `disable_fieldtrial_testing_config = true` in the release configuration says
it.

Four separate behaviours turned out to be coming from that file rather than from
the code: the navigation blur transition, the new tab page identity disc, the
Google Password Manager settings row, and the bottom bar disappearing on the new
tab page. Patches 0000106, 0000113, 0000114 and 0000117 deal with each. A feature default
changed in code is inert until that setting is on, so check the config first.
