---
name: check-ob
description: Use when user says check ob, check OB, save vault, sync vault, or asks to commit/push the Obsidian vault (AshworX-Vault). Stages vault changes and pushes a GPG-signed commit to GitHub.
---

# Check OB — Sync Obsidian Vault

The phrase `check ob` (any casing) means: save the current state of the
Obsidian vault to GitHub now.

Vault: `/Volumes/Data/AshworX-Files/AshworX-Vault`
Remote: `https://github.com/Ashworx-Global/vault.git` (branch `main`)

## Steps

1. Verify the vault is available:
   ```sh
   ls "/Volumes/Data/AshworX-Files/AshworX-Vault/.git" || echo "VAULT NOT MOUNTED"
   ```
   If the `/Volumes/Data` drive is not mounted, stop and tell the user to
   connect it. Do not proceed.
2. Inspect changes:
   ```sh
   git -C "/Volumes/Data/AshworX-Files/AshworX-Vault" status --short
   git -C "/Volumes/Data/AshworX-Files/AshworX-Vault" diff --stat
   ```
   If working tree is clean, report "vault already in sync" and stop.
3. Stage everything:
   ```sh
   git -C "/Volumes/Data/AshworX-Files/AshworX-Vault" add -A
   ```
4. Commit GPG-signed, following the `gpg-signed-commits` skill
   (`$GPG` via wrapper, `GPG_TTY` set, explicit `-S`):
   ```sh
   source ~/.zshrc
   export GPG_TTY=$(tty 2>/dev/null || echo ${TTY:-})
   git -C "/Volumes/Data/AshworX-Files/AshworX-Vault" commit -S -m "vault: <brief summary of what changed>"
   ```
   Write the message from the actual changes (e.g. `vault: add project notes
   for X, update tasks`). Then verify:
   ```sh
   git -C "/Volumes/Data/AshworX-Files/AshworX-Vault" log -1 --show-signature
   ```
5. Push:
   ```sh
   git -C "/Volumes/Data/AshworX-Files/AshworX-Vault" push
   ```

## Rules

- NEVER commit unsigned: always `-S`, NEVER `--no-gpg-sign`.
- NEVER print, echo, or log `$GPG`.
- Commit message prefix is always `vault: `.
- If commit or push fails, report the error and stop — do not retry with an
  unsigned commit or a force push.
