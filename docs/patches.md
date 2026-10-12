# What the patches do

Every change Bare makes to Chromium, in the order the series applies. The patches
themselves are in [`patches/`](../patches); this is the summary of what each one is for.

| # | Patch | Effect |
| --- | --- | --- |
| 0001 | Fix two Desktop Android crashes | Extension popup keyboard events and the sign-in Add Account action both crashed the browser |
| 0002 | Harden extensions menu | The menu action crashed when no toolbar coordinator existed |
| 0003 | Extensions toolbar on phone layouts | Extension icons, popups, and pinning were tablet-only; now available at phone widths |
| 0004 | Remove variations and network-time callbacks | Two periodic requests to Google, sent regardless of activity |
| 0005 | Keep web navigations in the browser | `http(s)` links no longer get handed to whichever app claims the domain |
| 0006 | Stop Autofill crowdsourcing uploads | Form structure was uploaded to Google to train its field-classification heuristics |
| 0007 | Remove the GCM push channel | Google Cloud Messaging services, the c2dm permission and the Firebase receiver |
| 0008 | Guard omnibox vector icon calls | Unblocks disabling the Google XR SDKs, which previously broke the build |
| 0009 | Hide Google Password Manager and sign-in promo | Both were permanently non-functional and advertised as broken |
| 0010 | Remove the "You and Google" settings section | Sign-in and Google services entries, neither of which can work here |
| 0011 | Ignore page requests to lock screen orientation | Fullscreen video forced landscape, overriding the system rotation lock |
| 0012 | Draw fullscreen content into the display cutout | Fullscreen video was letterboxed off the camera edge, leaving it off-centre |
| 0013 | Size fullscreen video to its picture | The seekbar sat at the bottom of the screen instead of on the video |
| 0014 | DuckDuckGo as the default search provider | Google was the shipped default, selected by engine ID rather than list order |
| 0015 | Remove the sign-in first-run screen | Promoted a sign-in this build cannot do, and claimed data is sent to Google |
| 0016 | Stop showing the NTP sign-in card | "Get better content": sign in to personalise a feed this build cannot use |
| 0017 | Remove the Chrome tips module | A carousel of Google promos: history sync, sign-in, passwords, Safe Browsing |
| 0019 | Remove the Ask Gemini button | The bottom bar's extra slot resolved to Gemini, which demands account verification |
| 0020 | Remove the avatar sign-in button | "Signed out. Opens options to sign in." on every new tab page |
| 0021 | Stop offering Gemini as a toolbar shortcut | Otherwise the button removed in 0019 could be put back from Settings |
| 0022 | Offer downloads to an installed download manager | Hands a download to an app such as 1DM instead of fetching it in the browser |
| 0023 | Add a setting to choose the download manager | Settings → Downloads, off by default |
| 0024 | Browse the Chrome Web Store as a desktop site | The mobile store has no install button, so extensions could not be installed |
| 0025 | Turn off the AI Mode omnibox button | An AI entry point in the omnibox, on by default |
| 0026 | Hide the shortcuts row and NTP cards by default | Both already had toggles; only the starting state changed |
| 0027 | Lower the search box into thumb reach | Sits around 40% down the page rather than near the top |
| 0028 | Move the tab switcher toolbar to the bottom | Its buttons stayed at the top while the browsing toolbar sits at the bottom |
| 0029 | Pick which download manager receives downloads | Lists installed handlers, or ask every time |
| 0030 | Add an incognito toggle to the bottom bar | Fills the slot 0019 emptied; red while incognito is active |
| 0031 | Reword the toolbar shortcut window width note | "Only available for small windows" read as excluding phones |
| 0032 | Lower the search box to the middle of the screen | 40% was still higher than a thumb comfortably reaches |
| 0033 | Stop painting white while a page loads on a dark theme | Three surfaces defaulted to white; adds the darken-websites setting |
| 0034 | Default the toolbar shortcut to Share | It defaulted to "based on your usage", which moves the button as habits change |
| 0035 | Let the user add their own search engine | Chromium's add-engine screen existed but was switched off on Android |
| 0036 | Remove the built-in Gemini and AI Mode shortcuts | @gemini and @aimode shipped as search shortcuts pointing at Google |
| 0037 | Round the search engine icon in the omnibox | The rounding provider was built and updated but never attached to the view |
| 0038 | Rename the browser to Bare | Launcher, widgets, About page and the menu description |
| 0039 | Use the Bare icon | Legacy, adaptive and monochrome variants in every density |
| 0041 | Skip the first run experience | It opened a second Activity that only showed a spinner |
| 0042 | Add the Bare welcome screen | One-time welcome layered over the browser, not its own Activity |
| 0043 | Let supported sites keep playing media in the background | Opt-in, off by default; the page is told it is still visible so it does not pause itself |
| 0044 | Rename the browser in the remaining Android strings | 337 strings still said Chrome; Google's own products keep their names |
| 0045 | Remove the Autofill AI and personal context settings | "Smarter form understanding" shared page URLs and content with Google |
| 0046 | Use the installed password manager by default | And relabel the built-in option, which claimed to use your Google Account |
| 0048 | Keep the search engine icon round in thumbnails | Outline clipping is skipped when a view is drawn into a software canvas |
| 0049 | Add a Video autostart site setting | Chromium stored an autoplay setting nothing ever read |
| 0050 | Keep sites told the page is visible in the background | Sites paused their own video on `visibilitychange`, defeating background playback |
| 0051 | Keep background playback permission when hidden | The permission was withdrawn the moment the page stopped being visible |
| 0052 | Add DuckDuckGo No AI as a prepopulated engine | Selectable from the engine list rather than added by hand |
| 0053 | Show the NOAI wordmark on the new tab page | The engine had no logo, so the page showed nothing |
| 0054 | Fix a crash when Video autostart is switched back on | Introduced by 0049 |
| 0055 | Use the Bare mark in the media notification | The lock screen still showed Chromium's |
| 0056 | Find the media under a click-blocking overlay | Sites cover media with a transparent layer, which defeated the long press |
| 0057 | Keep Manifest V2 extensions working | Chromium 153 disables MV2 outright; full uBlock Origin needs it |
| 0058 | Ship the MV2 action schemas in this build | Their absence killed the renderer for any extension using them |
| 0059 | Ship uBlock Origin with the browser | Pre-installed, unpinned, removable like anything else |
| 0060 | Use the Bare mark for the launcher icon | Adaptive, themed and legacy variants |
| 0061 | Offer the main settings on the welcome screen | Search engine, ad blocker, address bar, downloads, chosen before anything loads |
| 0062 | Finish renaming the browser in the remaining strings | The strings the first rename pass missed |
| 0063 | Remove Ask Gemini from the app menu | It appeared once on first launch, then never again |
| 0064 | Offer a download for audio elements | A long press on an `<audio>` element produced an empty menu |
| 0065 | Offer a download for video the page only streams | Media Source video has no downloadable src, so upstream offers nothing |
| 0066 | Follow range requests back to the whole file | A range-fetched URL names a slice, not the file, and audio is a separate track |
| 0067 | Stop asking the user to sign in to a Google account | Six surfaces built the same promo; all six ask one method first |
| 0068 | Let extension context menu items run their own command | The menu overwrote the listener extensions arrive with, so tapping one did nothing |
| 0069 | Add a Dark AMOLED theme | A third theme taking flat surfaces to true black; raised surfaces keep a small lift so menus stay separable |
| 0070 | Turn off Glic, the Gemini integration | Every Glic surface asks one class first, so closing that gate removes all of them at once |
| 0071 | Cover the activity relaunch when the theme changes | Switching theme recreates the activity, which flashed the outgoing colours on the way through |
| 0072 | Rename the browser in eleven more strings | The strings the earlier renaming passes missed |
| 0073 | Make Google sign-in and sync unreachable | The settings rows, the sign-in and Google services deep-link routes (five since Chromium 156) and the settings-search entries |
| 0074 | Look for Bare's own updates on GitHub | One plain request to the public release feed, no identifier and nothing scheduled; automatic or manual |
| 0075 | Stop the launch splash flashing white on a dark theme | Android resolves the splash against the system's night mode, before any of the browser runs |
| 0076 | Let the current page row reach the omnibox on phones | The desktop Android target hid share, copy and edit for the page you are on |
| 0077 | Read night mode from the browser, not from a Context | The renderer filled white because the Context reachable from a WebContents answered for the system |
| 0078 | Keep the verbatim match the current page row needs | The row is built from a match the desktop target declined to produce |
| 0079 | Name the filter list that strips tracking from links | uBlock Origin ships the list that does it switched off, and nothing surfaced that |
| 0080 | Stop advertising Safe Browsing | No public Chromium Android build has the handler the lookups need, so the settings, the Safety Hub module and the promo card all described nothing |
| 0081 | Stop the caBLE messaging token | An InstanceID token was fetched at every cold start for a phone-as-security-key feature that needs Chrome Sync |
| 0082 | Stop the omnibox asking who is signed in | Typing reached GAIA ListAccounts at accounts.google.com, only to decide whether to personalise suggestions |
| 0083 | Remove Send to your devices | Upstream shows it to signed-out users on purpose, to recruit a Google sign-in that cannot complete here |
| 0084 | Fix the welcome screen on Android 12 | The reveal was driven only by the splash exit; when that never fired the rows stayed invisible and the circle silently banked defaults |
| 0085 | Register twelve fewer components | Each registration announces the install to update.googleapis.com; the security-carrying ones are kept and listed |
| 0086 | Stop the cloud-policy Firebase tokens | A fresh profile fetched two FCM tokens as durable identifiers, for enterprise invalidations this build can never receive |
| 0087 | Fix two crashes from patch 0080 | Removing a preference row leaves the Java that looks it up holding null; Privacy and security and Safety check both crashed |
| 0088 | Stop the update dot reappearing | Opening the row cleared it, but the next daily check saw the same release was still newer and put it straight back |
| 0089 | Send the update row to the release it found | It announced a version and then did nothing when tapped; the page for the found tag now opens in a tab, with no download |
| 0090 | Stop settings search crashing | Patch 0080 removed the Safe Browsing row but left the search index rewriting its summary, which threw on Edit homepage and on Search settings |
| 0091 | Stop the bottom bar reacting to a long press | A label repeated what the icon meant, and once that was cleared the gesture fell through and opened a tab or switched to incognito |
| 0092 | Make a second welcome a review, not a reset | The search engine, autofill provider and background media rows live in the profile, which is not up when the welcome is built, so a repeat showing drew defaults over settings the user had chosen and wrote them back on Start |
| 0093 | Stop the startup ListAccounts to accounts.google.com | Two metrics-only services read the cookie jar while the profile was still being built, and reading it fetched from Google whenever the cached answer was stale, on every cold start |
| 0094 | Drop the Safety Hub password check that can never run | The row reported that it could not check passwords in a Google Account and offered a Sign in to Chrome button, in a build with no browser sign-in, and its permanent failure held the whole page at a warning |
| 0095 | Stop shipping the XR module when XR is switched off | chrome_module_descs never consulted the XR buildflags, so about 20 MB of AndroidX XR and ARCore native code was packaged in a build where enable_vr, enable_arcore, enable_openxr and enable_cardboard are all off |
| 0096 | Keep the Start circle off the welcome footer | The column needed more height than a Pixel 3 has, so the spacer collapsed and the circle ran past the padding reserved for the footer, which was pinned to the frame and took no part in the layout |
| 0097 | Give incognito its extension background pages back | The incognito ProcessManager waited for an embedder callback that Android does not have, so a split-mode extension allowed in incognito never got a background page and never filtered |
| 0098 | Let the bundled blocker work in incognito without being asked | uBlock Origin starts with incognito access and nothing else does; the default is applied once, using the same preference the chrome://extensions toggle writes, so turning it off keeps it off |
| 0099 | Let Android retry lower GLES versions instead of losing the GPU | Upstream switches off the ES-version retry as if a software renderer would catch the failure, but Android never builds one, so a driver that refuses an ES3 context left the GPU process dead instead of walking down to 3.0 or 2.0 |
| 0100 | Give the bottom bar slots so its buttons can move later | Fixed positions became named slots, with nothing visible changing yet |
| 0101 | Let the bottom bar show the toolbar buttons it does not have | An adapter drives a bar button from the same provider the toolbar uses, so both stay in step |
| 0102 | Let the toolbar be arranged from settings | Which button sits in which slot, chosen rather than fixed |
| 0103 | Let a sideways drag along the bar change brightness or volume | Off by default; the bar is the only place in reach of a thumb that has nothing else to do |
| 0104 | Let a button do a second thing when it is held | A second action per slot, so one button covers two without a menu |
| 0105 | Keep the app menu where the user can always reach it | Arranging the toolbar could move the menu out of reach, leaving no way back |
| 0106 | Let bookmarks be carried in and out as a file | Import and export without a sync account, which this build has no way to offer |
| 0107 | Let a link open in the app that handles it | Always, Ask or Never, defaulting to Never, the behaviour 0005 applied to everything |
| 0108 | Keep the page in Bare after Stay here without asking again | The question came back on every navigation to the same site |
| 0109 | Leave the navigation blur transition off | A field trial turned on a transition that flashed white between pages |
| 0110 | Judge a web page wrapped in an intent as the page, not the wrapper | An `intent://` carrying an `http(s)` payload was treated as an app link whatever the setting said |
| 0111 | Offer the tab switcher as a list as well as a grid | Thumbnails are a poor index of many tabs; the list shows titles |
| 0112 | Tell the two Appearance shortcut settings apart | Two rows with the same name, one for the address bar and one for the toolbar |
| 0113 | Do not offer AI Mode whatever the search engine is | The button returned when the default search engine changed |
| 0114 | Stop fetching the suggested sites list from Google | The new tab page asked gstatic for tiles it never showed |
| 0115 | Draw the extensions toolbar into the captured toolbar | The composited toolbar bitmap is drawn from a fixed child list, so extensions vanished during a tab switch |
| 0116 | Stop the identity disc offering Google sign-in on the new tab page | A second avatar surface 0020 never covered, uncovered when the field trial config went off |
| 0117 | Hide the Google Password Manager row on the older settings path too | 0009 covered one path; the other one still reached it |
| 0118 | Add Exit to the app menu, and let it clear browsing data first | Off by default; the selection is a profile preference and deletion goes through Chromium's own path |
| 0119 | Say which autofill service is filling, without naming Google | The card was right and the wording was not: the service is whichever one Android has |
| 0120 | Keep the bottom bar on the new tab page | A field trial parameter, not a feature flag, took the bar off the new tab page |
| 0121 | Let the pin setting hide the extensions menu button on a phone | The switch changed its own state and nothing else, because the phone toolbar registers no width consumer |
| 0122 | Add an option for black backgrounds on darkened sites | Auto Dark leaves a white page at `#121212`; this maps eligible backgrounds to black without touching text or images |
| 0123 | Move the update check to the current account and bound what it reads | The three release URLs named the old account, and the feed could say things the parser was not ready for |
| 0124 | Let policy refuse a download before another app is offered it | The external handoff ran above the blocklist check, and the chooser still offered Bare itself |
| 0125 | Keep the page here when there is nowhere to ask about leaving | Ask launched without asking when no Activity could host the dialog |
| 0126 | Clear the pending flag when there is nothing left to delete | An interrupted exit could leave the flag set for good once the selection was emptied |
| 0127 | Put two annotations and a javadoc back on what they describe | An insertion landed between a javadoc and the declaration it belonged to; the second it fixed was in a file Chromium 156 deleted |
| 0128 | Name Google's help centre as Google's | The rename caught the anchor text and left the link pointing at Google |
| 0129 | Say that the update check sends the version, because it does | Two comments claimed the request carried no version; the User-Agent has always carried one |
| 0166 | Report Chromium's version, not Bare's, from version_info | Chromium 156 took the browser version from the APK's version name: a development name crashed startup, and a release would have said Chrome/1.0.0 |
| 0167 | Keep the bundled blocker when its file cannot be prepared | One failed write while unpacking uBlock Origin made Chromium uninstall it, settings and all |
| 0168 | Ship uBlock Origin 1.75.0 and move profiles over to it | The Web Store copy is gone; the author's own build has a different id, so existing settings are carried across and a removal is honoured |
| 0169 | Load the bundled blocker again after Android kills it | Android's memory killer could stop uBlock Origin's background page and leave filtering off until a restart; a blocker that keeps working comes straight back every time |
| 0170 | Stop probing made-up hostnames on every launch | Chromium 156 started sending requests to random hostnames after launch and on every network change |
| 0171 | Keep Glic off on desktop Android, in native code too | A compiled-in override turned Gemini in Chrome on for every Desktop Android build, phones included |
| 0172 | Keep the native new tab page on desktop-class Android | Chromium 156 swapped in a web new tab page on Android PCs |
| 0173 | Do not load restored tabs in the background on a phone | A desktop override loaded restored tabs a few at a time without being opened, and memory pressure is what kills uBlock Origin |
| 0174 | Let an unpinned extension open from the extensions menu on a phone | Tapping an unpinned extension closed the menu and opened nothing |
| 0175 | Keep toolbar shortcuts current, and stop offering Translate | A shortcut kept the state of the page the tab started on; Translate cannot work without a Google API key and is gone from both shortcut screens |
| 0176 | Rename the browser in four strings new in 156 | Four reachable strings new in Chromium 156 said Chrome |
| 0177 | Show the welcome switches as Start will save them | After Android restored the app, the Ad blocker switch could show off while Start saved it on |
| 0178 | Give the incognito window on a phone an extension window controller | windows.getLastFocused() crashed the browser on a window without a controller, after an incognito tab opened or after Android restored the app in incognito |
| 0179 | Open an extension's popup in the incognito tab it was opened from | The popup in an incognito tab described the last regular tab instead |
| 0180 | Do not ask Google's DNS servers about google.com when a site cannot be found | A DNS error made Chromium resolve google.com at 8.8.8.8 over plain UDP, outside the user's Secure DNS setting |
| 0181 | Keep the built-in translate language list instead of fetching Google's | Opening Settings, Languages fetched translate.googleapis.com |
| 0182 | Keep Chrome's tips notifications and their opt-in sheet off | Chromium 156 showed an unasked sheet after four hours away, leading to Safe Browsing settings and Google Lens |
| 0183 | Show a search engine's stored favicon instead of asking Google for one | Settings, Search engine asked Google's favicon server for any engine without a built-in icon |
| 0184 | Give Exit an icon in the app menu | Exit was the only top-level menu row without one |
| 0185 | Open Developer tools on phones too | DevTools was limited to tablet-width windows, and its frontend was laid out too small to read on a phone |
| 0186 | Let a light page keep its own canvas on a dark theme | With a dark theme, pages without a background showed their dark text on black, even with site darkening off |
| 0187 | Do not send hint requests to Google without an API key | Some features sent page hosts to optimizationguide-pa.googleapis.com, which could only refuse them |
| 0188 | Stop registering the Actor Safety Lists component | It only serves the Gemini agent, which this build keeps off |
| 0189 | Keep account preview data off | Chromium 156 turned on a per-profile service that fetches account data from Google |

Patches 0001 and 0002 are bug fixes that happen to be prerequisites. 0003 is a usability fix.
0004 through 0010 are the de-Googling, as are 0014 through 0021. 0011 through 0013 fix
fullscreen video behaviour. 0022 and 0023 add the external download manager option. 0024
through 0028 are usability changes: the Web Store, the AI Mode button, what the new tab page
shows by default, and where the toolbars sit. 0029 through 0033 continue in that vein: choosing
the download manager, the incognito toggle, clearer wording in settings, where the search box
sits, the white flash on a dark theme, which shortcut the toolbar starts with, and adding your
own search engine. 0036 drops the built-in Google AI search shortcuts and 0037 fixes the shape
of the engine icon in the omnibox. 0038 through 0042 are the rebrand to Bare, and 0044 finishes
the naming the first pass missed. 0043 adds background media playback. 0045 and 0046 continue
the de-Googling in autofill: removing the AI sections, and defaulting to whichever password
manager the user already has. 0048 is a small visual fix found by using the build: an icon
that was clipped round rather than drawn round.

**There is no patch 0047.** It animated a new tab from the button that opened it, and it was
dropped during the move to 153.0.8010.27 when upstream changed that animation underneath it. The
numbers after it were already in use elsewhere, so renumbering the series would have broken every
reference to them. The gap is the honest record of a patch that existed and no longer does.

**There are no patches 0018 and 0040 either.** Both were dropped during the move to
156.0.8078.25 because upstream removed what they changed: PwaRestorePromoUtils.java, which 0018
edited, and the "New" labels and their helper, which 0040 took out of the main settings page.
0130 to 0165 are not in this series: those numbers belong to work on other branches, and new
patches start at 0166.

0166 through 0179 came with the move to Chromium 156. 0166 is the one the move itself required:
upstream changed where the browser version comes from, and Bare would not start without it.
0167 through 0169 make the bundled uBlock Origin dependable: it survives a failed unpack, it moves
from the delisted Web Store copy to the author's own build without losing settings, and it comes
back when Android kills its background page. 0170 through 0173 answer new upstream behaviour: a
DNS-interception probe, Gemini in Chrome and a web new tab page switched on for Desktop Android,
and background loading of restored tabs. 0174, 0175 and 0179 fix problems reported against the
previous release, and 0176 finishes the naming for the strings 156 added. 0177 and 0178 fix two
bugs the previous release already had, found while testing this one.

0180 through 0189 came out of checking that work and the requests that followed it. 0180,
0181, 0183 and 0187 each stop a request to Google that nothing in Bare had covered: a DNS
diagnosis, a language list, search engine icons and optimization hints. 0182 and 0189 switch off
two things Chromium 156 turned on, a tips prompt and an account data service, and 0188 drops a
component only the Gemini agent used. 0184 and 0185 are requests: an icon for Exit, and Developer
tools on phones. 0186 fixes how 0033 kept the white flash away, which left light pages without a
background unreadable on a dark theme.

0100 through 0105 build the arrangeable toolbar, one step at a time: slots first, then a way to
drive a bar button from the toolbar's own provider, then the settings screen, then a drag and a
hold, and finally a guard so the app menu can never be arranged out of reach. 0106 through 0114
are a mixture of features and de-Googling found by daily use. 0115 through 0122 came out of
release testing, and four of them exist because
`disable_fieldtrial_testing_config = true` changed what the browser follows. 0123 through 0128
came out of the pre-publication audit, and 0129 from the release that followed it.

Sign-in has no single gate in Chromium. Patches 0009, 0010, 0015, 0016 and 0020 each remove a
different entry point: the settings row, the "You and Google" section, the first-run screen,
the New Tab Page card, and the toolbar avatar. Assume there are more rather than fewer.

0080 through 0087 are the release-hardening pass, driven by a runtime audit rather than by
reading code. 0080 and 0087 belong together: removing the Safe Browsing rows crashed two settings
screens, which only showed up by opening them on a device. 0081 and 0086 are two separate
consumers of the same Firebase machinery, which is why removing one did not cover the other.

0069 through 0079 came out of using the build on a Pixel Fold and a Pixel 10 Pro XL. 0069 and
0071 are the AMOLED theme and the relaunch it triggers. 0070 and 0073 close the last Gemini and
Google account surfaces, and 0072 the last of the naming. 0074 adds Bare's own update check, the
one request the browser makes on Bare's behalf rather than Chromium's. 0075, 0077 and 0078 are all
the same class of bug: something asked a Context, or the build target, a question only the browser
could answer, and got the system's answer back.

## Removed by build flag

These go in `args.gn` rather than a patch:

```gn
use_mlkit_for_aicore = false          # ML Kit + AICore (on-device Gemini Nano bridge)
enable_glic_internal_resources = false # Glic resources only Chrome-branded builds carry; 0070 and 0171 turn Glic off
enable_reporting = false               # Reporting API / Network Error Logging
enable_service_discovery = false       # local device discovery
enable_mdns = false                    # mDNS

chrome_public_manifest_package = "org.barebrowser"  # application id
```

The application id is a build argument rather than a patch, because upstream already exposes
it as one. Note that changing it means the app installs alongside an earlier build rather
than upgrading it: Android identifies apps by package, so tabs, extensions and settings do
not carry over.

## What is deliberately kept

| Kept | Why |
| --- | --- |
| Extensions (`enable_extensions_core`) | The entire point of the Desktop Android target |
| Proprietary codecs (`ffmpeg_branding = "Chrome"`) | H.264/AAC video playback |
| Widevine | DRM. Removing it breaks paid streaming |
| Component updater | Delivers CRLSet certificate revocation data |
| HSTS preload list | Static security asset, no callback |

## Verified on device

Recorded when each of these landed, on a Pixel 10 Pro XL.

Extensions install and run (Bitwarden, uBlock Origin, Dark Reader), popups open and
pinning works. Both crash reproductions behind 0001 are gone, and the shipped
`AndroidManifest.xml` contains no reference to ML Kit or AICore.

**0005** against a real in-page link tap: following a Reddit result from a search page keeps you
in the browser, with Reddit's own "Open App" prompt left unused.

**0011 and 0012**: fullscreen video follows the phone's orientation instead of forcing landscape,
and sits centred in both portrait and landscape. **0013** by geometry read off the running page,
for both a 16:9 video and one taller than the viewport.

**0014 and 0015** on a wiped profile, which is the only honest test for either: the new tab page
shows DuckDuckGo and a query resolves to `duckduckgo.com`, and the browser opens straight to the
new tab page with no first-run screen, including after a force stop and relaunch. If the Terms
of Service acceptance did not persist, that screen would come back.
