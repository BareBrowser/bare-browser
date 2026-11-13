# Measured network behaviour

Measured on a Pixel 3 running Android 12, by watching the sockets opened under Bare's own uid
and recording the browser's own network log. For 1.0.0 that covered a wiped profile from first
launch through the welcome screen, a network change and several minutes idle, then several
sites, a page that fails to resolve, and the Languages and Search engine settings. What follows
is what was actually observed, not what was intended. Nothing was captured again for 2.0: what changed since then
is read from the patches, and the paragraphs below say where.

**Chromium's component updater contacts `update.googleapis.com`**, from the first start onwards,
and fetches the components it needs as signed packages over plain HTTP from Google's download
host `edgedl.me.gvt1.com`. It is kept deliberately. These are the components registered in
1.0.0, as `chrome://components` lists them:

| Component | Why it stays |
| --- | --- |
| CRLSet | certificate revocation |
| PKI Metadata | Certificate Transparency |
| Certificate Error Assistant | quality of the TLS interstitial |
| File Type Policies | download danger classification |
| Origin Trials | web compatibility |
| Safety Tips, Crowd Deny | lookalike-domain and abusive-notification lists, applied locally |
| Captcha Providers | left registered: its purpose is not clear enough in the tree to remove it confidently |

Registration tells Google an install exists, along with a component id, a version, an install
date and a cohort. Twelve other components were dropped in patch 0000082 for buying nothing here:
the Privacy Sandbox set, Google's omnibox suggestion model, the optimization-hints feed, shopping
and checkout heuristics, on-device AI history strings, and two Safe Browsing lists that nothing
can consult. Actor Safety Lists, the site lists of the Gemini agent this build keeps off, was
dropped in 0000149. There is no Widevine component on Android; protected video goes through the
system's own DRM, below.

**Widevine provisioning contacts `www.googleapis.com`.** About a minute after startup on a fresh
profile, Chromium has Android's MediaDrm provision two spare Widevine origin identifiers in
advance, so that protected video can start without waiting, and the provisioning request goes to
`www.googleapis.com/certificateprovisioning`. If there is no connection then, it tries again when
the network comes back. It happens whether or not any site ever plays protected video. By the
code, a later start repeats it only once sites have used up the spare identifiers. This is Chromium's default (`kMediaDrmPreprovisioningAtStartup`), and Bare leaves it
as it is.

**On the first run of a fresh profile, most of the rest is uBlock Origin** fetching the filter
lists it ships enabled, from the list maintainers and their CDNs rather than from Google:
`pgl.yoyo.org`, `ublockorigin.github.io`, `ublockorigin.pages.dev`, `malware-filter.pages.dev`,
`cdn.jsdelivr.net` and `publicsuffix.org`. That happens once and then on the extension's own
schedule. uBlock Origin is installed and fetching these while the welcome screen is still asking
whether you want an ad blocker; turning the switch off removes it, with its settings.

**uBlock Origin updates itself from its author.** Its manifest points Chromium's extension updater
at `cdn.jsdelivr.net` (`gh/gorhill/uBlock@master/dist/chromium/update.xml`), which is checked
about every five hours. That request carries what Chromium's extension updater always sends: the
extension's id and version, the browser's version, the operating system and architecture, the
interface language and the User-Agent. A newer release downloads from `github.com`, served from
`release-assets.githubusercontent.com`. Earlier releases shipped the Chrome Web Store copy, which
checked `clients2.google.com` instead.

**BareFilter makes one request a day while it is on.** uBlock Origin fetches
`https://raw.githubusercontent.com/BareBrowser/bare-browser/main/filters/BareFilter.txt` and keeps
that copy as a filter list. The first fetch happens when BareFilter is switched on or first
subscribed. The request is the plain list download uBlock Origin makes for any filter list. Switching
BareFilter off takes effect from the next start; after that nothing is requested and the copy is
removed. Bare carries no built-in copy of the list.

**The update check contacts GitHub**, and only after the welcome screen has been completed and an
update preference stored. It is at most one request a day, to a public release feed. It sends two
headers, `User-Agent: Bare/<version>` and `Accept: application/atom+xml`, so the request does say
which version is asking. The Google Play build has no update check, because Play updates it.
What it carries beyond that is nothing that identifies you or the phone:
no cookies, no installation identifier, no device model, no Android build. The platform default
User-Agent would have carried the model and the build, so it is replaced. Choosing manual means
nothing leaves the device until the Check for updates row is tapped.

**If you make Google your search engine**, more of Chromium's Google-only behaviour switches on
with it. By the code, Chromium preconnects to `www.google.com` from time to time,
prefetches search results, prerenders `www.google.com/search/warmup.html` on focus (`kPrewarm`),
asks `www.google.com/async/folae` whether AI Mode is available, and sends a word you tap on a
page to `www.google.com/s` for Touch to Search. With DuckDuckGo or any other engine none of this
happens.

**Whatever the engine**, focusing the address bar no longer asks for suggestions before you type
anything: an empty address bar shows none (0000245). With Google that request went to
`www.google.com/complete/search`. The new tab page shows Bare's own logo, and no engine's logo is
fetched for it (0000196, 0000199). Both come from reading the patches and were not captured.

**Request desktop site sends a Chrome OS User-Agent** (`X11; CrOS x86_64 14541.0.0`), as
Chromium 156 does, where earlier releases said desktop Linux. Its client hints do not match: the
architecture hint says arm, and the bitness hint says 64 even on the 32-bit build. A site can
notice the difference.

**The Chrome Web Store gets that desktop User-Agent at the phone's width.** With a phone
User-Agent the store swaps "Add to Chrome" for "Add to Desktop", which sends the extension to a
signed-in desktop Chrome instead of installing it. So `chromewebstore.google.com` is asked for its
desktop pages. Extension pages then fit the phone's width. On a screen no wider than 700 pixels
the store's front page, category pages and search are redrawn as a plain list of the extensions
on the page, each row a link to the store's own listing; a button at the foot of the list, "Show
the store's own page", switches back to the store's layout (0000179, read from the patch and not
captured). Earlier releases asked for the desktop pages with a stored desktop-site
setting that covered every `google.com` site; 1.0.1 removes that setting once, on first launch.

**Developer options can change the User-Agent.** Default sends the strings described here. The
other choices are Chrome on five platforms, Edge, Firefox and Safari, or a typed string, and they
apply after a restart. Chrome and Edge send client hints that match; Firefox, Safari and a typed
string send none, as those browsers don't. While one is chosen, Request desktop site is greyed
out. Sites can still tell it isn't really that browser, from `navigator.platform` and similar signals.

**Page translation sends the page's text where you point it.** Translate pages goes to the
server whose address you typed in Settings, Translate pages, after you confirm once for that
server's host name; a different host asks again. The separate Google Translate choice is off by
default and uses Chromium's own Translate when you turn it on. With either, translating a page
also translates the next `http` and `https` pages that tab loads on the same site, without
asking. With Google that stops once the tab has loaded such a page on another site, or is closed;
a failed load, or a page of another kind, does not stop it. With your own server it stops when
the tab loads a page on another site or a page of another kind, when you show the original, when
you turn the server off, or when the tab is closed. This comes from reading patches 0000174,
0000195, 0000220, 0000221, 0000224 and 0000237 and was not captured.

**Help & feedback opens this project's page on GitHub**, `github.com/BareBrowser/bare-browser`,
in a tab, and so does the keyboard shortcut for help. It no longer opens Google's Chrome help
centre at `support.google.com` or checks connectivity against `clients4.google.com` and
`www.google.com` first (0000190, read from the patch and not captured).

**Some things reach Google only when you do them:**

- **A site you allow to send push notifications** registers with Google's push service, through
  Google Play services, as web push does in Chrome, unless you have picked a push distributor app
  in Settings, Push notifications (0000176). Without one, the subscription it gets back names
  `google.com` as its endpoint and the messages themselves are never delivered: patch 0000007 removes
  the receiver they would arrive through. With one, the subscription names the address that app
  gave out, Google is not asked, and delivery depends on that app. Only the intent actions are
  tested, with a stand-in app written for the purpose; no real distributor has been tried.
- **A Google or YouTube page that publishes cross-origin speculation rules** can have Chromium
  prefetch the pages it names through Google's private prefetch proxy, `tunnel.googlezip.net`,
  after checking it can reach `dns-tunnel-check.googlezip.net` and `tls-tunnel-check.googlezip.net`.
  This depends on the page you are on, not on your search engine.
- **A payment form that asks for a shipping address** loads address formats from
  `chromium-i18n.appspot.com` when you edit the address.
- **chrome://metrics-internals** can fetch a variations seed from Google if you open it and ask
  for one.
- **An extension installed from the Chrome Web Store** checks for updates at
  `clients2.google.com`, about every five hours, like any other copy of Chromium. Chromium's daily
  request for Web Store metadata about installed extensions is not made: it needs an API key this
  build does not have.
- **A custom home page** may get its icon from Google's favicon server, `t0.gstatic.com`.

The proxy, the payment form, metrics-internals, the home page icon and Touch to Search above are
read from the code and were not captured.

Extension update checks that do not go to the Chrome Web Store carry any cookies the browser
holds for that host, as upstream Chromium sends them; for uBlock Origin that is `cdn.jsdelivr.net`.
The downloads that follow go without cookies, unless the server refuses one with 401 or 403 and
Chromium tries again with them.

**What no longer happens**, each checked with a capture of the browser's network log:

- No Firebase or InstanceID registration on its own. A fresh profile previously fetched two FCM
  tokens for Chromium's cloud-policy invalidation projects and kept them in shared preferences as
  durable identifiers. Patches 0000078 and 0000083 removed both consumers; the token files are no longer
  created at all. A site you allow to send push notifications still registers, as above.
- No lookup against `accounts.google.com`, from the omnibox or at startup. Typing in the address
  bar used to reach GAIA ListAccounts to decide whether to personalise suggestions. Separately, a
  fresh profile used to POST to ListAccounts about a tenth of a second into every cold start,
  before the welcome screen had been answered. Neither the omnibox nor the account reconcilor was
  behind the startup one: two services asked for the cookie jar while the profile was still being
  built, both only to report metrics, and reading the cookie jar fetched it from Google whenever
  the cached answer was stale. Patch 0000090 stops the read from reaching the network, so the answer
  now comes from the cache. Visiting Google sites and signing in to them is unaffected.
- No Safe Browsing traffic. There was never any: see below.
- No lookup of `google.com` at Google Public DNS when a site cannot be found. Chromium resolved
  it against `8.8.8.8` over plain UDP to diagnose the failure, outside the user's Secure DNS
  setting; 0000141 turns that probe off, and the error page still says the address could not be
  found.
- No request to `translate.googleapis.com` from Settings, Languages, which fetched the list of
  languages Google can translate; 0000142 keeps the list built into Chromium.
- No icons for search engines from Google's favicon server (`t0.gstatic.com`), which Settings,
  Search engine asked for any engine without a built-in icon; 0000144 uses the icon stored from
  visiting the site, or a placeholder.
- No Discover feed and no doodle on the new tab page with Google as the engine. Each new tab
  asked `discover-pa.googleapis.com` for a feed it could not get and `www.google.com/async/ddljson`
  for the day's doodle; 0000154 turns Discover off and 0000155 keeps the built-in logo.
- No hint requests to `optimizationguide-pa.googleapis.com`, which some features sent with the
  hosts of the pages involved even though the request could only be refused; 0000148 stops them
  without an API key.
- No translate ranker model from `www.gstatic.com`. Every tab's translate client could download
  it on a fresh profile, for a decision translation without an API key never asks for; 0000160 gives
  it no URL without a key. A capture from the moment the browser starts showed no request to
  `www.gstatic.com`.
- No translations or CSS documentation for Developer tools from
  `chrome-devtools-frontend.appspot.com`, which the frontend fetched when offered the browser's
  language; 0000146 keeps it to the English files built in.

The 1.0.0 capture reached none of the hosts in this list.

Chromium 156 also started sending HEAD requests to three random hostnames after launch and after
every network change, to detect DNS interception. Patch 0000131 turns that check off.

Traffic from Android itself and from Google Play Services is separate from all of this and is not
affected by anything Bare does.

**Safe Browsing does not work in this build, and no longer claims to.** Chromium Android performs
lookups through a handler that Google injects in its own build and that no public build has. The
settings, the Safety Hub module and the promotional cards all described protection that never
ran, so patch 0000077 removed them. Bare shows no phishing or malware interstitial. Treat unknown
links with the caution you would give a browser with no such feature, because that is what this
is.
