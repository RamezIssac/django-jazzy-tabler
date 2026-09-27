#!/usr/bin/env bash
# Publish the admin screenshot matrix to GitHub Pages (gh-pages branch).
#
#   scripts/publish-matrix-site.sh            # capture matrix, stage a gh-pages worktree, print preview path
#   scripts/publish-matrix-site.sh --push     # the same, then push the gh-pages branch
#   scripts/publish-matrix-site.sh --skip-capture   # reuse the existing proofs/$RUN output
#
# No CI required: run it locally after a release (or whenever the matrix should
# refresh). Once the gh-pages branch is pushed, enable Pages in the repo
# settings (Source: gh-pages branch, / root) — the site lands at
# https://<owner>.github.io/django-jazzy-tabler/
set -euo pipefail

RUN="${JAZZY_PROOFS_RUN:-final}"
PUSH=0
CAPTURE=1
for arg in "$@"; do
    case "$arg" in
        --push) PUSH=1 ;;
        --skip-capture) CAPTURE=0 ;;
        *) echo "unknown argument: $arg" >&2; exit 2 ;;
    esac
done

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ "$CAPTURE" -eq 1 ]; then
    echo ">> capturing matrix into proofs/$RUN (needs: uv sync --group screenshots)"
    JAZZY_SCREENSHOTS=1 JAZZY_PROOFS_RUN="$RUN" uv run pytest tests/test_screenshots.py -q
fi

[ -f "proofs/$RUN/index.html" ] || { echo "proofs/$RUN/index.html missing"; exit 1; }

WORKTREE="$(mktemp -d)/gh-pages-site"
cleanup() { git worktree remove --force "$WORKTREE" >/dev/null 2>&1 || true; }
trap cleanup EXIT

# base the site on the existing gh-pages branch when there is one
if git rev-parse --verify --quiet origin/gh-pages >/dev/null; then
    git worktree add --detach "$WORKTREE" origin/gh-pages >/dev/null
else
    git worktree add --detach --no-checkout "$WORKTREE" >/dev/null
fi

# root = latest run; previous runs stay archived under their name
mkdir -p "$WORKTREE/runs"
rm -rf "$WORKTREE/light" "$WORKTREE/dark" "$WORKTREE/manifest.json" "$WORKTREE/index.html"
cp -r "proofs/$RUN/." "$WORKTREE/"
rm -rf "$WORKTREE/runs/$RUN"
mkdir -p "$WORKTREE/runs/$RUN"
cp -r "proofs/$RUN/." "$WORKTREE/runs/$RUN/"

git -C "$WORKTREE" add -A
if git -C "$WORKTREE" diff --cached --quiet; then
    echo ">> site unchanged"
else
    git -C "$WORKTREE" -c user.name="${GIT_AUTHOR_NAME:-jazzy-bot}" \
        -c user.email="${GIT_AUTHOR_EMAIL:-noreply@localhost}" \
        commit -q -m "Matrix site: $RUN ($(date -u +%Y-%m-%d))"
    echo ">> staged site commit"
fi

if [ "$PUSH" -eq 1 ]; then
    git -C "$WORKTREE" push origin HEAD:refs/heads/gh-pages
    echo ">> pushed gh-pages — enable Pages (Source: gh-pages / root) if not already:"
    echo "   https://github.com/RamezIssac/django-jazzy-tabler/settings/pages"
else
    PREVIEW="$ROOT/proofs/site-preview"
    rm -rf "$PREVIEW"
    mkdir -p "$PREVIEW"
    cp -r "$WORKTREE/." "$PREVIEW/"
    rm -f "$PREVIEW/.git"
    echo ">> preview staged at: file://$PREVIEW/index.html"
    echo "   (re-run with --push to publish the gh-pages branch)"
fi
