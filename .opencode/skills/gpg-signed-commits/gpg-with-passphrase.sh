#!/bin/sh
# gpg wrapper for git commit signing.
# Uses passphrase from $GPG env var when it unlocks the key, otherwise
# falls back to plain gpg (gpg-agent / pinentry).
# Single exec with untouched stdin/stdout/stderr so git sees gpg's
# --status-fd output. Passphrase travels on fd 3, never via `ps`.
# Used as: git config gpg.program /path/to/gpg-with-passphrase.sh
set -eu

# Extract signing key: last arg (git calls: gpg --status-fd=2 -bsau KEY)
KEY=""
for a in "$@"; do KEY="$a"; done

VALID=0
if [ -n "${GPG:-}" ] && [ -n "$KEY" ]; then
  if printf 'gpg-wrapper-probe' | gpg --batch --yes --pinentry-mode loopback --passphrase-fd 3 --local-user "$KEY" -abs -o /dev/null 3<<EOFPROBE >/dev/null 2>&1
$GPG
EOFPROBE
  then
    VALID=1
  fi
fi

if [ "$VALID" = "1" ]; then
  exec gpg --batch --yes --pinentry-mode loopback --passphrase-fd 3 "$@" 3<<EOFPASS
$GPG
EOFPASS
else
  exec gpg "$@"
fi
