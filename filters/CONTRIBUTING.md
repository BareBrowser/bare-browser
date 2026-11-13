# Contributing to BareFilter

Thanks for helping. BareFilter is a short list of fixes for websites that push people into native apps, including the layout and scrolling problems those prompts cause. See [BareFilter.md](BareFilter.md) for what it is and how Bare uses it.

This page is the policy. Changes are **community-reviewed and maintainer-approved**. Anyone can propose a rule, comment, review and test. It is not a vote: the maintainer makes the final decision on every change. Today the maintainer is the repository owner.

## What belongs here

Rules for sites that nag you to open or install their app, and for the breakage that nag causes (a locked page, a gap where a banner was, a header that no longer fits).

Out of scope for now: ads, trackers, cookie banners, paywall bypasses and general annoyances. Please don't open proposals for those yet.

## Before you propose a rule

- **One site, or one closely related problem, per pull request.** No bulk additions and no speculative rules.
- **Keep rules small and scoped to the site.** Name the domain. Avoid broad selectors that could match other pages.
- **Check for overlap.** Search [`BareFilter.txt`](BareFilter.txt), and look at the uBlock Origin lists that are on by default in Bare, to see whether the problem is already handled.
- **Write your own rules.** Don't copy rules from other lists unless their license allows it, and say where they came from.

## Testing

Test in Bare, with its bundled uBlock Origin, not in another browser. Look at the page with your rules **off** and **on**, and check that nothing else broke: scrolling, navigation, login, playback and anything else the page does. uBlock Origin marks filters it can't parse; fix any it flags before you submit.

### Compare complete lists

BareFilter fixes more than banners: some rules also restore scrolling and fix layouts. If you test by switching the whole subscription off, those fixes disappear too and the result tells you nothing about your change. So test **complete lists** that differ only by your change:

- **Replacing a rule:** current complete list, then the complete list with your replacement, then the complete list with the rule removed.
- **Adding a rule:** current complete list, then the complete list with your addition.
- **Removing a rule:** current complete list, then the complete list without it.

Every other rule stays exactly as it is in each version. Make the versions from the current `BareFilter.txt` and check with `diff` that each differs from the current list only by your change.

To load a complete list without the production subscription getting in the way, put it under My filters:

1. **Save your own My filters.** Copy the text somewhere safe. You will only add a block at the end and take that block out again; your own lines are never edited. If one of your own lines targets the same site, comment it out for the test (in the editor, Tab toggles `! ` on the selected lines) and restore it at the end.
2. **Turn the subscription off.** In Extensions, switch BareFilter off, then close Bare completely and reopen it. Bare removes the subscription and its copy when it starts, so the production list can't run alongside your test copy. Open uBlock Origin's filter lists and check that BareFilter is no longer ticked. Also check that "My filters" is enabled.
3. **Load the current complete list.** At the end of My filters add a block and apply the change:

   ```
   ! TEST BLOCK start
   (the current rules and their comments, without the header lines)
   ! TEST BLOCK end
   ```

   Test the page. This is your baseline.
4. **Swap the block's contents** for the version with your replacement (or addition), apply, and test. Then swap in the version with the rule removed, apply, and test. Check scrolling, navigation, login and playback each time, not only the banner.
5. **Other lists.** For each default uBlock Origin list that could touch the same page, repeat the baseline with that list unticked in the filter lists (apply the change), then tick it again. Note which lists made a difference.
6. **Restore.** Delete the test block, apply, and check that My filters matches what you saved. Switch BareFilter back on in Extensions, close Bare completely and reopen it, then check that BareFilter is ticked again in uBlock Origin's lists. Re-tick any list you unticked.

Cautions:

- Use the Extensions switch, not uBlock Origin's checkbox, to turn BareFilter off. While the switch is on, Bare subscribes again when it starts.
- Don't use the lines `! BareFilter begin` or `! BareFilter end` in My filters. Bare manages the text between them.
- Read any rules you didn't write before pasting them in. uBlock Origin's documentation warns against adding filters from sources you don't trust.

How this was checked: the steps were run end to end on a test phone (Bare 2.0.3 with uBlock Origin 1.75.0) with the current complete list, the list with a rule replaced, and the list with it removed. Switching BareFilter off in Extensions and restarting removed the production subscription from uBlock Origin's lists, and the default lists stayed selected. Each list was entered in the My filters editor and applied with its "Apply changes" button, and the rules that loaded matched the list (11, 11 and 10). A rule left in a subscription kept hiding the old element after it had been replaced or removed, which is why the subscription has to be off. Afterwards the phone was put back as it was.

What was not checked: the page tests ran against a local test page, not the real sites, and some of the dashboard steps were driven through the browser's debugging interface rather than by finger. Unticking and re-ticking the other default lists (step 5) was not run. If a button or label differs in your build, say so in your pull request and we'll correct the guide.

## What to include in the pull request

Use the BareFilter template (it loads from the "Choose a template" link, or add `?template=barefilter.md` to the new pull request URL). It asks for:

- The affected URL and a plain description of the app prompt or problem.
- The rule or rules, and why each one is needed.
- Your Bare version, the page language, and whether you were signed in.
- What you tested with the rules off and on, and what you did not test.
- Screenshots, if they help. Remove anything private first.

You never need to share passwords, cookies, private links or full diagnostic logs. If something is needed to reproduce a problem, describe it instead.

## Review

- **When the clock starts.** A proposal stays open for **at least 72 hours** after it is marked ready for review with the evidence above. Draft pull requests don't start the clock. The maintainer confirms the evidence by applying the `evidence-complete` label; the window can't start before that.
- **Any edit to a rule line restarts the full 72 hours,** even if you believe it changes nothing. That includes additions, removals, exception rules, selector changes and whitespace changes within a rule line, and it applies to changes the maintainer suggests. A rule line is any non-blank line in `BareFilter.txt` that doesn't start with `!`, and any line that starts with `!#`, because uBlock Origin reads lines such as `!#include` and `!#if` as preprocessor directives.
- **Force-pushing, reopening the pull request or changing its base branch** while a window runs also restarts it. Please add commits instead of rewriting history.
- **What doesn't restart it:** edits to comments (lines starting with `!` but not `!#`, with no line break hidden inside them), edits to documentation files, and formatting outside rule lines, such as blank lines.
- **No rule lines, no rule waiting period.** A pull request that only changes comments, blank lines or other files has no 72-hour wait. The maintainer still reads it. If it ever changes a rule line, even in one commit that is later reverted, it becomes a rule proposal and stays one.
- **Silence is not approval.** Approvals from the community are useful feedback, but there is no vote count to reach, and the maintainer still reviews every proposal.
- **The maintainer's own changes follow the same process** and the same waiting time.
- **A concrete breakage report pauses merging** until it has been looked at. If the maintainer decides against a point someone raised, they explain why in the pull request.
- **Urgent rollbacks are the one exception.** A rule that is actively harming people can be removed or reverted without waiting, with a public explanation of what was wrong. This is not a route for ordinary additions.

An automatic check named **BareFilter waiting period** applies all of this on every pull request that changes `BareFilter.txt`. It shows when the window started, why, and the earliest time it can pass, using GitHub's own recorded times, never commit dates. It doesn't turn green by itself when the time is up; the maintainer runs it again before merging. It doesn't merge anything: the maintainer still reads every proposal and makes the final call. How it works is in [.github/barefilter-gate/README.md](../.github/barefilter-gate/README.md).

Once a change is merged into the production list, it reaches Bare users through the daily list update, without a Bare release, so the bar is deliberate.

## Reporting a broken site or asking for a removal

Open an issue with the "BareFilter report" template. Say which site and page, what went wrong, and what you were doing. A report that a rule broke something pauses any pending change to it. Removal requests get the same public discussion as additions, except for urgent rollbacks above.

## Licensing and credit

BareFilter is licensed under BSD-3-Clause, declared in the list header and in the repository's [LICENSE](../LICENSE). By sending a rule you agree it can be shared under that license. Rules that are only available under an incompatible license, such as GPL lists, can't be copied in. Write your own, or open an issue and describe the problem.

Your authorship is preserved when a proposal is merged, so accepted work shows up on your GitHub profile as long as the commit email is linked to your account. Comments, reviews and testing are valued, but GitHub doesn't count them toward the contributors list.

## Contributing with an AI agent

AI-assisted contributions follow the same rules as other contributions, with three additional requirements:

- **Disclose the assistance.** If an AI agent helped produce the change, state that briefly in the pull request description.
- **A human verifies the work.** Before marking the pull request ready for review, a person must read the proposed rules, test them in Bare, and take responsibility for the submission. Agent output without human review and testing is not ready for consideration.
- **Credit people; disclose tools separately.** Commit authorship and co-author credits identify the people responsible for a contribution. Disclose AI assistance in the pull request description, rather than listing an agent or service as an author or co-author. Human co-author credits are welcome. Use of an agent for an individual contribution does not imply project-wide use or endorsement of that tool.

See [AGENTS.md](AGENTS.md).
