# BareFilter waiting-period check

A GitHub Actions check named **BareFilter waiting period**. It tells the maintainer whether a pull request that changes `filters/BareFilter.txt` has waited the full review period (72 hours). The policy is in [filters/CONTRIBUTING.md](../../filters/CONTRIBUTING.md); this page explains how the check applies it. Merging stays a human decision: the check never merges anything.

## What it reports

On the pull request's current head commit:

| Result | Meaning |
|---|---|
| Success, "Not applicable" | No commit in the pull request has changed a rule line of `BareFilter.txt` (comments, blank lines and other files don't count). No rule waiting period. |
| Pending, "Draft" | Drafts don't start a clock. |
| Pending, "Waiting for evidence" | The maintainer hasn't applied the `evidence-complete` label yet. |
| Pending, "Waiting" | The window is running. The check shows when it started, why, and the earliest pass time. |
| Pending, "Paused" | The `breakage-report` label is on the pull request. |
| Success, "Waiting period complete" | 72 hours have passed since the latest relevant change. |
| Success, "Urgent rollback" | The owner-authorized exception below. |
| Failure | The check could not establish the timing safely. It fails closed. |

A comment from the workflow's bot on the pull request repeats the same information and holds the record the check needs.

## When it applies

Only to a pull request that changes a rule line. A pull request that edits only comments, blank lines or other files gets "Not applicable" and no comment. Once a commit has changed a rule line the pull request stays a rule proposal, so reverting the change, or force-pushing it away, does not exempt it.

## When the window starts, and what restarts it

The window starts at the **latest** of:

- the moment the pull request was last marked ready for review (a draft, or ready → draft → ready, uses the last ready event);
- the moment the maintainer applied the `evidence-complete` label, if it is still there;
- the moment the check first saw a commit that changes a rule line (including a commit that is later reverted);
- any force-push, reopen or base-branch change.

A rule line is a non-blank line of `BareFilter.txt` that doesn't start with `!`, or any line that starts with `!#`, because uBlock Origin reads lines such as `!#include` and `!#if` as preprocessor directives. A `!` line that holds a Unicode line or paragraph separator, or a carriage return anywhere but its very end, also counts, because uBlock Origin can start a new line there. Added, removed, edited, moved and whitespace-only changes to one all count. Comments, blank lines and other files don't.

## Times come from GitHub

The check never uses commit author or committer dates, which anyone can set. It uses:

- GitHub's recorded event times for ready, draft, labels, force-pushes, reopening and base changes;
- for commits, the time the check first saw them, taken from GitHub's own clock (the `Date` header of its API responses). A commit the check sees late is charged to the late sighting, so missing an event can only make the wait longer.

The record of first sightings lives in the bot's comment. The gate uses the **oldest** comment written by `github-actions[bot]` that holds a record and ignores later ones; entries it can't read are dropped, so a commit then simply looks newer. If the record is missing, every commit is treated as first seen now. A record holding a time in the future makes the check fail closed, as does any event time in the future.

As a second line of defence the check also reads the pull request's timeline, which lists commits in the order they arrived between events GitHub timestamps. A commit can't have arrived before the event listed just ahead of it, so that event's time is used as a floor for when the commit was seen. Floors only lengthen the wait.

**Limit of the record:** every workflow in a repository that uses the automatic token posts as the same bot. Someone who can push a workflow to a branch of this repository could write a look-alike comment. The floor above narrows what that can achieve, but doesn't remove it. People without write access, such as contributors working from forks, can't.

## Who can confirm evidence or authorize a rollback

Only logins listed in [config.json](config.json) (`owners`). The check reads who applied a label from GitHub's timeline, not from anything the pull request says. A label from anyone else is ignored, and removing the label by anyone cancels it.

## Urgent rollback

The owner applies `urgent-rollback` and posts a comment explaining the problem (at least 30 characters, written after the label). The check then passes immediately, but only if the pull request's net change to the list removes rule lines and adds none. A change that adds anything keeps the normal wait. The label, who applied it and the comment are all on the pull request for anyone to see.

## When it runs

- When a pull request is opened, reopened, pushed to, marked ready or drafted, labeled or unlabeled, or edited.
- On demand, from the Actions tab, for one pull request or all of them.

There is no timer. A pull request that has finished waiting stays pending until the check runs again, so the maintainer runs it from the Actions tab before merging.

Runs are queued one at a time **per pull request**, so one pull request's event can't replace another's. A queued run can be replaced by a newer one for the same pull request; every run reads the current state afresh, so nothing is lost. A manual run picks up anything else that was dropped.

## Two pull requests, one commit

GitHub checks belong to commits. If two open pull requests have the same head commit (for example the same branch opened against two base branches), the check on that commit shows the **stricter** of the two results and names the other pull request.

## Stale results

The check is attached to one exact commit. A new push gets a new, pending check. The success for an older commit stays on that commit and authorizes nothing else. Before it publishes, the check re-reads the pull request and drops its result if the head commit, the draft state or the labels changed. It saves its record before it publishes a result, so a pass is never published without one.

## Security

- The workflow uses `pull_request_target`, so GitHub runs the version of the workflow and script on the pull request's **base** branch. A pull request cannot change the gate it is judged by.
- It checks out the base branch only and never fetches, builds or runs anything from the pull request. Diffs, titles, labels and comments are read through the API as plain text and never put into a shell command or executed.
- Permissions: `contents: read` to check out the base branch; `checks: write` to publish the check; `pull-requests: write` to write the bot's own comment. No other write access and no secrets beyond the automatic `GITHUB_TOKEN`. (It is not a read-only job: it writes a check and a comment.)
- The check has a fixed name and is published by GitHub Actions. The ruleset that requires it should name GitHub Actions as the expected source so another app or account can't supply a look-alike.

## Limits

- Pull requests with more than 250 commits, or a commit or pull request with 3,000 or more changed files, fail closed.
- Only pull requests into the default branch fire the event trigger. A manual run evaluates every open pull request, whatever its base.
- If the check can't publish (an API error), it tries to publish a failure, and otherwise the commit simply has no passing check. A stale pass on the same commit can remain if even that fails, so the required-check rule should be on the commit's latest result.
- A GitHub diff without a patch (very large, or a mode-only change) is treated as a rule change.
- Merging the default branch into a pull request branch brings in whatever rule lines changed there, which restarts the window. So does rebasing and force-pushing.
- A force-push can't be audited for what it replaced, so it restarts the window.
- If the bot's comment is deleted, the wait can only get longer.
- Checks left pending on commits that were replaced stay as they are. Only the head commit matters.

## Tests

```bash
python3 -I -m unittest discover -s .github/barefilter-gate
```

The tests use a controlled clock (nothing waits 72 hours) and a fake GitHub for the policy cases, a local HTTP server for the real client's pagination and clock handling, and static checks of the workflow's security properties.
