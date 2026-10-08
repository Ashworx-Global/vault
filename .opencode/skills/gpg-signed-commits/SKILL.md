---
name: gpg-signed-commits
description: Use when creating git commits, git commit commands, or signing commits in any project. Enforces GPG-signed commits using passphrase from $GPG env var.
---

# GPG Signed Commits

Every `git commit` performed by the agent in ANY project MUST be GPG-signed.
Prefer the passphrase from `$GPG` via the wrapper below, with gpg-agent as
fallback. Never create an unsigned commit.

## Preconditions

1. Load the passphrase variable if missing (do NOT print its value).
   NOTE: it must be single-quoted in shell profile so `$` is literal:
   `export GPG='...'` not `export GPG="..."`.
   ```sh
   [ -n "${GPG:-}" ] || source ~/.zshrc
   ```
   If still empty, do NOT abort — the wrapper falls back to gpg-agent.
2. Set TTY for pinentry fallback:
   ```sh
   export GPG_TTY=$(tty 2>/dev/null || echo ${TTY:-})
   ```

## Configuration (ensure once per repo, plus global defaults)

```sh
WRAPPER="$PWD/.opencode/skills/gpg-signed-commits/gpg-with-passphrase.sh"
chmod +x "$WRAPPER"

# Global defaults so every project signs by default
git config --global user.signingkey 8CDCD577355815C7
git config --global commit.gpgsign true
git config --global gpg.format openpgp
git config --global gpg.program "$WRAPPER"

# Per-repo enforcement (run inside project)
git config user.signingkey 8CDCD577355815C7
git config commit.gpgsign true
git config gpg.format openpgp
git config gpg.program "$WRAPPER"
```

If the repo already has a different `user.signingkey`, keep the repo's key
but still enforce `commit.gpgsign true` and `gpg.program` to the wrapper.

## Commit

Always sign explicitly, even if `commit.gpgsign` is true:

```sh
git commit -S -m "<message>"
```

For amended / rebased / cherry-picked / merged commits, also add `-S`:
`git commit --amend -S --no-edit`, `git rebase --gpg-sign`, etc.

Verify after commit:

```sh
git log -1 --show-signature
```

Expected: `gpg: Good signature from "LeeRoy Ashworth <leeroya@gmail.com>"`.

## Rules

- NEVER run `git commit` without `-S` / `--gpg-sign`, and NEVER use
  `--no-gpg-sign`.
- NEVER print, echo, log, or embed `$GPG` in messages, files, or tool output.
- NEVER pass the passphrase on the command line (`--passphrase "$GPG"` leaks
  via `ps`). The wrapper feeds it on fd 3, leaving stdin/stdout/stderr
  untouched so git sees gpg's `--status-fd` output.
- The wrapper probe-tests `$GPG` against the signing key, uses loopback
  signing when it unlocks, else falls back to gpg-agent. If signing
  still fails with `gpg: signing failed: No secret key` or
  `Inappropriate ioctl for device`, re-check `GPG_TTY`, `gpg.program`, and
  whether `$GPG` matches the key's real passphrase. Do not fall back to an
  unsigned commit — ask the user instead.
