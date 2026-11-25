#!/usr/bin/env python3
"""BareFilter waiting-period gate.

Decides whether a pull request that changes the BareFilter rules has waited
long enough, and reports the answer as a check run on the PR's exact head
commit. Standard library only. It never checks out or runs pull request code:
everything it knows about a PR comes from the GitHub API and is treated as
untrusted text. See README.md in this folder.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
LOGIN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-\[\]_.]{0,60}$")
STATE_RE = re.compile(r"<!-- barefilter-gate-state:(\{.*?\}) -->", re.S)
COMMENT_RE = re.compile(r"!(?!#)[^\r\u2028\u2029]*\r?")   # a "!" line that is not "!#" and holds no inner line break
BOT_LOGIN = "github-actions[bot]"
MAX_COMMITS = 250          # the API lists at most 250 commits of a PR
FILES_PER_PAGE = 100
MAX_PAGES = 100
MIN_EXPLANATION = 30       # characters in the owner's rollback explanation
MAX_FILES = 3000           # the API shows at most this many files; more could hide the rules
FUTURE_SLACK = timedelta(minutes=5)
RANK = {"success": 0, "pending": 1, "failure": 2}


class GateError(Exception):
    """Something could not be established safely. The gate fails closed."""


# --------------------------------------------------------------- time helpers

def parse_time(text):
    try:
        return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        raise GateError("unreadable time from GitHub")


def fmt_time(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def human(t):
    return t.strftime("%Y-%m-%d %H:%M UTC")


def ceil_second(t):
    """Round up so a time we record is never earlier than the moment seen."""
    if t.microsecond:
        t = t.replace(microsecond=0) + timedelta(seconds=1)
    return t


# --------------------------------------------------------- rule line analysis

def patch_rule_lines(patch):
    """Count (added, removed) rule lines in a unified-diff patch.

    A rule line is any changed line that is neither blank nor a comment. A
    comment starts with "!" but not "!#" (uBlock Origin reads lines such as
    "!#include" and "!#if" as preprocessor directives) and holds no U+2028 or
    U+2029, and no carriage return except one at its very end (a CRLF file):
    uBlock Origin can start a new line at those. Whitespace inside a rule line
    counts, so a whitespace edit is a rule edit. Comment lines, blank lines and
    hunk or no-newline markers do not.
    """
    added = removed = 0
    for line in patch.split("\n"):
        if not line or line[0] not in "+-":
            continue
        body = line[1:]
        if body.strip() == "" or COMMENT_RE.fullmatch(body):
            continue
        if line[0] == "+":
            added += 1
        else:
            removed += 1
    return added, removed


def classify_files(files, path):
    """Return (touched, rule_changed) for one commit's file list."""
    touched = rule_changed = False
    for f in files:
        if f.get("filename") != path and f.get("previous_filename") != path:
            continue
        touched = True
        patch = f.get("patch")
        if f.get("status") == "renamed" or not isinstance(patch, str):
            rule_changed = True          # moved, mode change or too large: assume the worst
            continue
        added, removed = patch_rule_lines(patch)
        if added or removed:
            rule_changed = True
    return touched, rule_changed


# --------------------------------------------------------------- GitHub client

class GitHub:
    def __init__(self, token, base="https://api.github.com"):
        self.token = token
        self.base = base.rstrip("/")

    def _request(self, method, url, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": "Bearer " + self.token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "barefilter-gate",
            "Content-Type": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
                return (json.loads(raw) if raw else None), resp.headers
        except urllib.error.HTTPError as e:
            raise GateError("GitHub API %s %s returned %s" % (method, urllib.parse.urlparse(url).path, e.code))
        except (urllib.error.URLError, OSError, ValueError) as e:
            raise GateError("GitHub API %s failed: %s" % (method, type(e).__name__))

    def _url(self, path, params):
        url = self.base + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        return url

    def get(self, path, **params):
        return self._request("GET", self._url(path, params))[0]

    def post(self, path, body):
        return self._request("POST", self._url(path, None), body)[0]

    def patch(self, path, body):
        return self._request("PATCH", self._url(path, None), body)[0]

    def paginate(self, path, **params):
        """All items of a list endpoint, following Link headers. Fails closed
        on a runaway chain or a next link that leaves the API host."""
        params = dict(params)
        params.setdefault("per_page", 100)
        url = self._url(path, params)
        items = []
        host = urllib.parse.urlparse(self.base).netloc
        for _ in range(MAX_PAGES):
            data, headers = self._request("GET", url)
            if not isinstance(data, list):
                raise GateError("expected a list from " + path)
            items.extend(data)
            nxt = None
            for part in (headers.get("Link") or "").split(","):
                m = re.match(r'\s*<([^>]+)>\s*;\s*rel="next"', part)
                if m:
                    nxt = m.group(1)
            if not nxt:
                return items
            if urllib.parse.urlparse(nxt).netloc != host:
                raise GateError("pagination left the API host")
            url = nxt
        raise GateError("too many pages from " + path)

    def now(self):
        """GitHub's own clock, from the Date header, not the runner's."""
        _, headers = self._request("GET", self._url("/rate_limit", None))
        date = headers.get("Date")
        if not date:
            raise GateError("no server time from GitHub")
        return parsedate_to_datetime(date).astimezone(timezone.utc)


# ------------------------------------------------------------------ the gate

class Result:
    def __init__(self, kind, title, detail, head=None, start=None, deadline=None, reason=None):
        self.kind = kind            # success | pending | failure
        self.title = title
        self.detail = detail
        self.head = head
        self.start = start
        self.deadline = deadline
        self.reason = reason

    def summary(self):
        lines = [self.detail]
        if self.start:
            lines.append("Window started: %s (%s)" % (human(self.start), self.reason))
        if self.deadline:
            lines.append("Earliest pass: %s" % human(self.deadline))
        if self.head:
            lines.append("Checked commit: %s" % self.head)
        return "\n\n".join(lines)


def safe_login(login):
    return login if isinstance(login, str) and LOGIN_RE.match(login) else "unknown"


class Gate:
    def __init__(self, api, repo, cfg):
        self.api = api
        self.repo = repo
        self.cfg = cfg
        self.window = timedelta(hours=float(cfg["window_hours"]))
        self.owners = {o.lower() for o in cfg["owners"]}
        if self.window <= timedelta(0) or not self.owners:
            raise GateError("bad gate configuration")

    # -- helpers
    def r(self, tail):
        return "/repos/%s%s" % (self.repo, tail)

    def authorized(self, actor):
        return (isinstance(actor, dict) and actor.get("type", "User") == "User"
                and isinstance(actor.get("login"), str) and actor["login"].lower() in self.owners)

    def label_names(self, pr):
        return {l.get("name") for l in pr.get("labels", []) if isinstance(l, dict)}

    def commit_files(self, sha):
        files, page = [], 1
        while True:
            data = self.api.get(self.r("/commits/" + sha), per_page=FILES_PER_PAGE, page=page)
            batch = (data or {}).get("files") or []
            files.extend(batch)
            if len(files) >= MAX_FILES:
                raise GateError("a commit changes %d or more files: cannot audit it" % MAX_FILES)
            if len(batch) < FILES_PER_PAGE:
                return files
            page += 1
            if page > 30:
                raise GateError("too many files in one commit")

    # -- state kept in a comment written by the workflow's own bot
    def load_state(self, number):
        """The gate's record, from the OLDEST comment written by the Actions bot.

        Any workflow in this repository that uses the automatic token posts as
        the same bot, so a look-alike comment is possible; the gate writes its
        own first, and later ones are ignored. Bad entries are dropped, which
        only ever makes a commit look newer (a longer wait)."""
        comments = self.api.paginate(self.r("/issues/%d/comments" % number))
        mine = []
        for c in comments:
            user = c.get("user") or {}
            if user.get("login") == BOT_LOGIN and user.get("type") == "Bot" and STATE_RE.search(c.get("body") or ""):
                mine.append(c)
        fresh = {"v": 1, "relevant": False, "commits": {}}
        if not mine:
            return fresh, None, comments
        c = min(mine, key=lambda x: x.get("id", 0))
        state = fresh
        try:
            raw = json.loads(STATE_RE.search(c["body"]).group(1))
            if raw.get("v") == 1 and isinstance(raw.get("commits"), dict):
                state["relevant"] = raw.get("relevant") is True
                for sha, v in raw["commits"].items():
                    if (SHA_RE.match(sha) and isinstance(v, list) and len(v) == 3
                            and isinstance(v[1], bool) and isinstance(v[2], bool)):
                        parse_time(v[0])
                        state["commits"][sha] = [v[0], v[1], v[2]]
        except (ValueError, GateError, KeyError, TypeError, AttributeError):
            pass
        return state, c["id"], comments

    # -- evaluation
    def evaluate(self, number):
        cfg = self.cfg
        pr = self.api.get(self.r("/pulls/%d" % number))
        head = (pr.get("head") or {}).get("sha", "")
        if not SHA_RE.match(head):
            raise GateError("pull request head is not a commit id")
        if pr.get("state") != "open":
            return None
        now = ceil_second(self.api.now())
        state, state_id, comments = self.load_state(number)
        state["head"] = head

        commits = self.api.paginate(self.r("/pulls/%d/commits" % number))
        if pr.get("commits", len(commits)) > MAX_COMMITS or len(commits) > MAX_COMMITS:
            raise GateError("more than %d commits: cannot audit history" % MAX_COMMITS)
        if len(commits) != pr.get("commits", len(commits)):
            raise GateError("commit list does not match the pull request")
        current = []
        for c in commits:
            sha = c.get("sha", "")
            if not SHA_RE.match(sha):
                raise GateError("unexpected commit id")
            current.append(sha)
            if sha not in state["commits"]:
                touched, rule = classify_files(self.commit_files(sha), cfg["path"])
                # first seen now: GitHub's clock, never the commit's own dates
                state["commits"][sha] = [fmt_time(now), rule, touched]
        if head not in current:
            raise GateError("head commit is not in the commit list")

        pr_files = self.api.paginate(self.r("/pulls/%d/files" % number))
        if len(pr_files) >= MAX_FILES:
            raise GateError("a pull request with %d or more files: cannot audit it" % MAX_FILES)
        for sha in current:
            if parse_time(state["commits"][sha][0]) > now + FUTURE_SLACK:
                raise GateError("the gate's record contains a time in the future")
        # Only a change to a rule line makes this a rule proposal. Comment-only,
        # blank-line-only and documentation-only pull requests have no rule wait.
        # Once a commit has changed a rule line the pull request stays a rule
        # proposal, so reverting or force-pushing it away cannot evade the policy.
        state["relevant"] = bool(state.get("relevant") or self.net_rule_change(pr_files)
                                 or any(state["commits"][s][1] for s in current))
        result = self.decide(pr, number, head, now, state, current, pr_files, comments)
        return result, state, state_id, comments, pr

    def net_rule_change(self, pr_files):
        for f in pr_files:
            if f.get("filename") == self.cfg["path"] or f.get("previous_filename") == self.cfg["path"]:
                touched, rule = classify_files([f], self.cfg["path"])
                if rule:
                    return True
        return False

    def decide(self, pr, number, head, now, state, current, pr_files, comments):
        cfg = self.cfg
        if not state["relevant"]:
            return Result("success", "Not applicable",
                          "This pull request has not changed any rule line in %s, so no rule waiting period applies. "
                          "The maintainer still reads every proposal." % cfg["path"], head)
        events = self.api.paginate(self.r("/issues/%d/timeline" % number))
        labels = self.label_names(pr)

        def when_of(text):
            t = parse_time(text)
            if t > now + FUTURE_SLACK:
                raise GateError("GitHub reported an event time in the future")
            return t

        # Defence in depth for the gate's own record: the timeline lists commits
        # in the order they arrived, between events GitHub timestamps. A commit
        # cannot have arrived before the event listed just ahead of it, so that
        # event's time is a floor for when we saw it. Floors only ever lengthen
        # the wait, so a wrong order can't make a pull request pass early.
        floor, last = {}, None
        for e in events:
            if e.get("event") == "committed" and isinstance(e.get("sha"), str):
                if last is not None:
                    floor[e["sha"]] = last
            elif isinstance(e.get("created_at"), str):
                last = when_of(e["created_at"])

        def seen(sha):
            t = parse_time(state["commits"][sha][0])
            return max(t, floor[sha]) if sha in floor else t

        # readiness, from GitHub's recorded events
        ready, ever_draft = None, False
        candidates = []
        evidence = None
        urgent_at = None
        for e in events:
            kind, when = e.get("event"), e.get("created_at")
            if kind == "ready_for_review":
                ready = when_of(when)
            elif kind == "convert_to_draft":
                ready, ever_draft = None, True
            elif kind in ("reopened", "base_ref_changed"):
                candidates.append((when_of(when), "pull request %s" %
                                   ("reopened" if kind == "reopened" else "base branch changed")))
            elif kind == "head_ref_force_pushed":
                candidates.append((when_of(when), "force-push"))
            elif kind in ("labeled", "unlabeled"):
                name = (e.get("label") or {}).get("name")
                if name == cfg["evidence_label"]:
                    if kind == "unlabeled":
                        evidence = None
                    elif self.authorized(e.get("actor")):
                        evidence = when_of(when)
                elif name == cfg["urgent_label"]:
                    if kind == "unlabeled":
                        urgent_at = None
                    elif self.authorized(e.get("actor")):
                        urgent_at = (when_of(when), safe_login(e["actor"]["login"]))
        draft = bool(pr.get("draft"))
        if draft:
            return Result("pending", "Draft",
                          "This is a draft. The waiting period starts when it is marked ready for review.", head)
        if ready is None:
            if ever_draft:
                raise GateError("cannot tell when this pull request was marked ready")
            ready = when_of(pr.get("created_at"))
        candidates.append((ready, "marked ready for review"))

        if evidence is not None and cfg["evidence_label"] not in labels:
            evidence = None
        if urgent_at is not None and cfg["urgent_label"] not in labels:
            urgent_at = None

        # urgent rollback: owner label, a removal-only change, a public explanation
        if urgent_at is not None:
            when, who = urgent_at
            explained = any(
                self.authorized(c.get("user")) and parse_time(c.get("created_at")) > when
                and len((c.get("body") or "").strip()) >= MIN_EXPLANATION for c in comments)
            removal_only = self.removal_only(pr_files)
            pushed_after = any(seen(sha) > when for sha in current)
            if explained and removal_only and not pushed_after:
                return Result("success", "Urgent rollback",
                              "Urgent rollback authorized by @%s at %s. Only rule removals are present, and "
                              "the owner has explained it in a comment. The normal waiting period is skipped."
                              % (who, human(when)), head)
            why = ("the change is not only rule removals in the list file" if not removal_only
                   else "commits were pushed after the owner's label" if pushed_after
                   else "no public explanation from the owner yet")
            note = "An urgent-rollback label is present but does not apply: %s. " % why
        else:
            note = ""

        if evidence is None:
            return Result("pending", "Waiting for evidence",
                          note + "The waiting period starts after the maintainer confirms the required evidence "
                          "with the '%s' label." % cfg["evidence_label"], head)
        candidates.append((evidence, "maintainer confirmed the evidence"))
        for sha in current:
            if state["commits"][sha][1]:
                candidates.append((seen(sha), "rule edit in %s" % sha[:7]))
        start, reason = max(candidates, key=lambda c: c[0])
        deadline = start + self.window
        hours = ("%g" % float(cfg["window_hours"]))
        if cfg["pause_label"] in labels:
            return Result("pending", "Paused",
                          note + "A breakage report is open ('%s' label), so merging is paused until it has "
                          "been investigated." % cfg["pause_label"], head, start, deadline, reason)
        if now < deadline:
            return Result("pending", "Waiting",
                          note + "%s hours after the latest change to the rules or the evidence." % hours,
                          head, start, deadline, reason)
        return Result("success", "Waiting period complete",
                      note + "%s hours have passed with no later change to the rules or the evidence." % hours,
                      head, start, deadline, reason)

    def removal_only(self, pr_files):
        found = False
        for f in pr_files:
            if f.get("filename") != self.cfg["path"] and f.get("previous_filename") != self.cfg["path"]:
                return False        # the exception covers the list file and nothing else
            if f.get("filename") == self.cfg["path"] or f.get("previous_filename") == self.cfg["path"]:
                patch = f.get("patch")
                if f.get("status") == "renamed" or not isinstance(patch, str):
                    return False
                added, removed = patch_rule_lines(patch)
                if added or not removed:
                    return False
                found = True
        return found

    # -- publishing
    def state_comment(self, result, state):
        body = ["**BareFilter waiting period: %s**" % result.title, "", result.summary(), "",
                "<sub>Written by the BareFilter gate workflow. Times are GitHub's own; commit dates are not used. "
                "See `.github/barefilter-gate/README.md`.</sub>",
                "<!-- barefilter-gate-state:%s -->" % json.dumps(state, sort_keys=True, separators=(",", ":"))]
        return "\n".join(body)

    def combine(self, number, result):
        """Checks belong to commits, not pull requests. If another open pull
        request has this same head commit, the stricter of the two results is
        what the shared check must say, or one pull request's pass would
        cover the other."""
        worst, who = result, None
        for other in self.api.paginate(self.r("/commits/%s/pulls" % result.head)):
            n = other.get("number")
            if (not isinstance(n, int) or n == number or other.get("state") != "open"
                    or (other.get("head") or {}).get("sha") != result.head):
                continue
            outcome = self.evaluate(n)
            if outcome is not None and RANK[outcome[0].kind] > RANK[worst.kind]:
                worst, who = outcome[0], n
        if who is None:
            return result
        return Result(worst.kind, "Shared commit: " + worst.title,
                      "Another open pull request (#%d) has this same commit, and GitHub checks belong to commits, "
                      "so the stricter result applies. %s" % (who, worst.detail),
                      result.head, worst.start, worst.deadline, worst.reason)

    def publish(self, number, result, state, state_id, comments, pr, check):
        # Still the same commit, draft state and labels as when we evaluated?
        now_pr = self.api.get(self.r("/pulls/%d" % number))
        if (now_pr["head"]["sha"] != result.head or bool(now_pr.get("draft")) != bool(pr.get("draft"))
                or self.label_names(now_pr) != self.label_names(pr)):
            return "pull request changed during evaluation; the event that changed it will be evaluated by its own run"
        # The record first, then the verdict: if the record can't be saved, no pass is published.
        text = self.state_comment(result, state)
        if state_id is None and not state["relevant"]:
            pass                    # an unrelated pull request gets the check and no comment
        elif state_id is None:
            self.api.post(self.r("/issues/%d/comments" % number), {"body": text})
        elif not any(c.get("id") == state_id and c.get("body") == text for c in comments):
            self.api.patch(self.r("/issues/comments/%d" % state_id), {"body": text})
        name = self.cfg["check_name"]
        runs = self.api.get(self.r("/commits/%s/check-runs" % result.head), check_name=name,
                            per_page=100).get("check_runs", [])
        ours = [c for c in runs if (c.get("app") or {}).get("slug") == "github-actions" and c.get("name") == name]
        existing = max(ours, key=lambda c: c.get("id", 0)) if ours else None
        output = {"title": check.title, "summary": check.summary()}
        body = {"name": name, "head_sha": result.head, "output": output}
        if check.kind == "pending":
            body["status"] = "in_progress"
        else:
            body["status"] = "completed"
            body["conclusion"] = "success" if check.kind == "success" else "failure"
        same = (existing and existing.get("status") == body["status"]
                and existing.get("conclusion") == body.get("conclusion")
                and (existing.get("output") or {}).get("summary") == output["summary"])
        if not same:
            if existing and existing.get("status") != "completed":
                self.api.patch(self.r("/check-runs/%d" % existing["id"]), body)
            else:
                self.api.post(self.r("/check-runs"), body)
        return "%s: %s" % (check.kind, check.title)

    def process(self, number):
        try:
            outcome = self.evaluate(number)
            if outcome is None:
                return "closed: nothing to do"
            result, state, state_id, comments, pr = outcome
            return self.publish(number, result, state, state_id, comments, pr, self.combine(number, result))
        except GateError as e:
            self.fail(number, str(e))
            raise

    def fail(self, number, message):
        """Fail closed: record a failing check on the current head if we can."""
        try:
            head = self.api.get(self.r("/pulls/%d" % number))["head"]["sha"]
            if SHA_RE.match(head):
                self.api.post(self.r("/check-runs"), {
                    "name": self.cfg["check_name"], "head_sha": head, "status": "completed",
                    "conclusion": "failure",
                    "output": {"title": "Cannot establish the waiting period",
                               "summary": "The gate could not safely work out the timing, so it fails closed: "
                                          + message[:300]}})
        except (GateError, KeyError, TypeError):
            pass

    def sweep(self):
        failures = 0
        for pr in self.api.paginate(self.r("/pulls"), state="open"):
            try:
                print("#%d %s" % (pr["number"], self.process(pr["number"])))
            except GateError as e:
                failures += 1
                print("#%d FAILED: %s" % (pr["number"], e))
        return failures


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "config.json")) as fh:
        cfg = json.load(fh)
    token = os.environ.get("GITHUB_TOKEN", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not token or not re.match(r"^[\w.\-]+/[\w.\-]+$", repo):
        print("missing token or repository")
        return 2
    api = GitHub(token, os.environ.get("GITHUB_API_URL", "https://api.github.com"))
    gate = Gate(api, repo, cfg)
    raw = (os.environ.get("PR_NUMBER") or "").strip()
    try:
        if raw:
            if not raw.isdigit():
                print("PR_NUMBER is not a number")
                return 2
            print(gate.process(int(raw)))
            return 0
        return 1 if gate.sweep() else 0
    except GateError as e:
        print("FAILED: %s" % e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
