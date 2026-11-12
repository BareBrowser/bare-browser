# Agent notes for BareFilter

For AI coding agents helping someone contribute to `filters/`. The policy is in [CONTRIBUTING.md](CONTRIBUTING.md); read it first. This file only adds what an agent needs to work here.

## Layout

- `filters/BareFilter.txt` is the list. There is one copy.
- `filters/BareFilter.md` is the user-facing description.
- `filters/CONTRIBUTING.md` is the policy. `filters/AGENTS.md` is this file.

The list is written in uBlock Origin's filter syntax. What it uses today:

- Header comments (`! Title:`, `! Version:`, `! Expires:` and so on).
- Section comments starting with `! ` that say what each rule does.
- Cosmetic rules: `domain##selector`, with `:has()`, `:has-text()` and `:style()`.

Match the style you find: one comment above each rule or small group, domain-scoped selectors, no network rules.

## How it reaches users

Bare ships uBlock Origin. While BareFilter is on, uBlock Origin fetches the production list from `https://raw.githubusercontent.com/BareBrowser/bare-browser/main/filters/BareFilter.txt` once a day. A merge to the production repository's default branch therefore reaches users without a Bare update.

Bare fetches only that URL. Never point a Bare build, a list URL or documentation at a fork or any other copy of the list.

## Rules for agents

- Same scope, evidence, licensing and review rules as people. App prompts only.
- One site or closely related problem per pull request. No unrelated edits, reformatting or version bumps unless asked.
- Don't push to the default branch, merge your own pull request, or work around review or the 72-hour window. Any edit to a rule line restarts that window; see CONTRIBUTING.md for exactly what counts.
- Don't force-push a branch while its pull request is under review (it restarts the window), and don't add or remove the maintainer's labels (`evidence-complete`, `urgent-rollback`, `breakage-report`). Add commits instead.
- Draft pull requests are fine. Don't mark one ready for review until a person has read the rules, tested them in Bare, and taken responsibility for the submission.
- Say in the pull request description that an agent helped. Use the "AI assistance" field in the template.
- Never invent testing results. In the pull request, say exactly what was tested, on which Bare version, and what still needs a person to check. If you can't run Bare, say so; that part is for the person you are helping.
- Don't copy rules from lists with incompatible licenses.
- Keep personal information, credentials, cookies, private URLs, local paths and internal development material out of rules, comments, commits and pull requests.
- Authorship belongs to people. Commits should be authored by the person responsible, and human co-author credits are welcome. Don't set an agent or service as author or co-author, and don't add attribution trailers that name one (such as `Co-Authored-By`), even if your tooling adds them by default. Remove those lines before committing.

## Checking your work

There is no validator in this repository, and a text search is not one. What you can check:

```bash
git diff --stat                 # only the files you meant to touch
git diff filters/BareFilter.txt # every changed rule, read line by line
```

Real syntax checking happens in uBlock Origin inside Bare: it flags filters it can't parse. Ask the person to load the rules there and report what they see. For testing steps, including how to test a replacement for an existing rule, see the Testing section of CONTRIBUTING.md.
