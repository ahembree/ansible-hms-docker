---
name: cut-release
description: Cut a new hms-docker release — decide the semver bump (new feature/container = minor, bug fix = patch, major never), bump hmsd_current_version, write the release-notes section, verify the release workflow will find it, and commit on a branch. Use when asked to cut a release, release a version, ship a release, or bump the version.
---

# Cutting an hms-docker release

Two files, always the same two:

| | File |
|-|-|
| Required | `hms-docker.yml` — bump `hmsd_current_version` (line 8) |
| Required | `docs-astro/src/content/docs/docs/release-notes/v<major>.<minor>.md` |

The notes file gets a `## v<version>` section. `master` is protected, so the work lands
through a PR, and the **merge commit** that touches `hms-docker.yml` on `master` is what
fires [.github/workflows/release.yml](../../../.github/workflows/release.yml) — it tags
`v<version>` and publishes a public GitHub Release whose body is scraped out of that
section. v1.18.0 through v1.18.5 are all tagged on `Merge pull request #…` commits.

**There is no dry run.** The two failure modes below are silent or leave debris, so step 6
is not optional.

## 1. Establish what is unreleased

```bash
./bin/yq '.[0].vars.hmsd_current_version' hms-docker.yml   # e.g. 1.18.7
git tag --list 'v*' | sort -V | tail -1                     # e.g. v1.18.7
git log --oneline "$(git tag --list 'v*' | sort -V | tail -1)"..HEAD
```

If the version is **already ahead** of the newest tag, a bump is committed but unreleased —
do not bump again. The pending merge releases it. Say so and stop.

Conventional-commit prefixes are the first signal, not the authority. Read the diff when a
`fix:` actually adds a feature, or when a `feat:` is really a tune.

## 2. Decide the bump

| Change | Bump |
|-|-|
| New container, new feature, new user-facing variable or flag | **minor** — `X.Y+1.0` |
| Bug fix, healthcheck/image/port tune, corrected behaviour | **patch** — `X.Y.Z+1` |
| Anything at all | **the major is never bumped** |

- **Mixed batch → the higher wins.** One new container plus three fixes is a minor.
- **A minor resets the patch to `0`** — `1.18.7` → `1.19.0`, never `1.19.1`.
- **Breaking changes still ship as a minor.** Major is off the table by policy. Document the
  break under `### Breaking Changes` and see step 5.
- **Not every commit is a release.** Docs-only, CI-only, README and workflow tweaks get no
  bump — `2025b43` (`fix(docs): update container docs`) and `30e3d79` (workflow_dispatch)
  never appear in `git log -- hms-docker.yml`. If the unreleased set is *only* those, say so
  and stop rather than manufacturing a release.

State the chosen version and why before editing anything.

## 3. Bump the version — `hms-docker.yml`

Line 8, in the play-level `vars:`. Unquoted, **3-part semver**.
[tasks/versioning.yml](../../../roles/hmsdocker/tasks/versioning.yml) compares it with
`version_type='semver'` against each install's on-disk `.hmsd-version`; a 2-part value
breaks that comparison for every existing user.

## 4. Release notes — `release-notes/v<major>.<minor>.md`

One file per **minor series**, all its patches stacked inside, newest at the top.

**Patch bump** — the file already exists. Insert the new `## v<version>` section directly
after the frontmatter's closing `---` and one blank line, above the previous section.

**Minor bump** — **create** the file. Its absence is the worst failure in step 6's list.
Frontmatter is fixed; `order` is the negative minor number, which is what sorts the sidebar
newest-first:

```yaml
---
title: Version 1.19
description: "Release notes for HMS-Docker v1.19 — <short summary>"
sidebar:
  order: -19
---
```

No [astro.config.mjs](../../../docs-astro/astro.config.mjs) edit — the Release Notes section
is `autogenerate`d from the directory (lines 95–99).

**The header must be exactly `## v<version>`**, character for character equal to
`hmsd_current_version`. The workflow matches on whole-line equality (`$0 == "## " v`), so no
date, no trailing text, no trailing whitespace. A `###` sub-heading is safe; the section
runs until the next line starting `## `.

Style — copy [v1.18.md](../../../docs-astro/src/content/docs/docs/release-notes/v1.18.md):

- `###` sub-headings are **topic-named, not a fixed taxonomy**. Real ones in use:
  `New Containers`, `Breaking Changes`, `Required Steps`, `Container changes`, `Traefik`,
  `Homepage`, `Docker daemon`, `Removed container`, `Other changes`.
- A one-line patch needs no `###` at all — a bare sentence is the norm (v1.18.6, v1.18.4).
- `-` bullets. Backticks for variables, paths and ports. Prose first for anything with a
  cause, bullets for the mechanics.
- Write user action in second person: "set `X` in `inventory/group_vars/all/…`".
- **No PR or issue links.** Those live in the commit message. In-repo file references use
  absolute `https://github.com/ahembree/ansible-hms-docker/blob/master/…` URLs.

## 5. Migration prompt — only if the user must act by hand

[tasks/versioning.yml](../../../roles/hmsdocker/tasks/versioning.yml) already pauses on
**every** version increase and points at the release notes. Add a block only when the
release needs manual steps the playbook cannot do itself. Blocks key on the **old** version:

```yaml
when: last_version is version('1.19.0', '<', version_type='semver')
```

Precedent at lines 68 (hardlink paths) and 86 (Authentik upgrade). Do not add one just to
announce a change — that is what the notes are for.

## 6. Verify — read-only, reproduces the workflow exactly

Lifted from [release.yml](../../../.github/workflows/release.yml) lines 38–47. Run it after
editing, before committing:

```bash
VERSION=$(./bin/yq '.[0].vars.hmsd_current_version' hms-docker.yml)
FILE="docs-astro/src/content/docs/docs/release-notes/v$(echo "$VERSION" | cut -d. -f1,2).md"

# the job derives this path; if it is missing, awk fails AFTER the tag is already pushed
test -f "$FILE" || echo "MISSING $FILE"

# must print nothing — the tag must not already exist
git tag --list "v$VERSION"

# this output IS the GitHub Release body. Empty means an empty release, published silently.
awk -v v="v$VERSION" '$0 == "## " v {flag=1; next} /^## / && flag {exit} flag' "$FILE"
```

Read the awk output as the user will see it on the Releases page. If it is empty, the header
does not match — fix it now, because nothing downstream will complain.

## 7. Branch, commit, and hand off

**Never commit to `master`** — it is protected, and commits made there cannot be pushed and
have to be replayed onto a branch later. If `git branch --show-current` prints `master`,
branch off HEAD first:

```bash
git switch -c release/<version>
```

Branching off HEAD carries any local unpushed commits along with it. That is correct — a
branch is how they reach `master`. Existing naming is `claude/<topic>-<hash>` or
`<verb>-<topic>`; `release/<version>` fits a pure version bump.

**Commit as Claude's identity.** Local git config is the human's, so override per-commit
rather than touching repo config:

```bash
git -c user.name=Claude -c user.email=noreply@anthropic.com commit -m "$MSG"
```

Every existing Claude commit here (`843dc5c`, `e5cc4c5`, `aee695b`) has both author and
committer `Claude <noreply@anthropic.com>`.

Conventional Commits, optional scope, `!` for breaking. Put the version bump and the notes
in the **same commit** — both shapes are precedented: a dedicated bump commit (`e5cc4c5`, 2
files) or the fix plus bump plus notes together (`6f93080`).

**Then stop.** Do not push. Do not run `gh pr create` — opening the PR is the user's click
in Claude Code. Print the push command instead:

```bash
git push -u origin release/<version>
```

and push only if the user explicitly asks in this session. Close by saying plainly that the
release publishes when the **PR is merged** to `master` — not when the branch is pushed, and
not when the PR is opened.

## Anti-patterns

Each of these is a real property of
[release.yml](../../../.github/workflows/release.yml) or of this repo's history:

- **A `## v<version>` header that does not match `hmsd_current_version` exactly.** The match
  is whole-line equality. The release is still published — with an empty body, no error, no
  warning.
- **Bumping the minor without creating the new notes file.** `awk` cannot open it, so the
  job fails *after* the tag was pushed. The cleanup step deletes the tag, so this is
  recoverable — but no release is published, and you have to fix the file and merge again.
  If a tag is somehow left behind: `git push --delete origin v<version>`.
- **Bumping the major.** Never, for any change.
- **Bumping for a docs-only or CI-only change.** No bump, no release.
- **Two bumps in one PR.** Only the final value is tagged; the intermediate version gets no
  release at all.
- **Appending the new section to the bottom** of the notes file. Newest goes on top.
- **A 2-part version** (`1.19`). It breaks the semver comparison against `.hmsd-version` on
  every existing install.
- **Committing to `master`.** Branch first, always.
- **Committing as the human.** Author *and* committer must be
  `Claude <noreply@anthropic.com>`.
- **Running `gh pr create`.** The skill stops at the commit.
- **Expecting the pushed branch to release.** The workflow only fires on `master`.
- **Merging the PR to "test" it.** The merge is the publish.
