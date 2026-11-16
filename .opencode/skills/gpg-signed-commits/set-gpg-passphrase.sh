#!/bin/sh
# Prompt for the GPG signing passphrase and store it in a private file.
# The value is never echoed, never passed on a command line, and the file
# is created with mode 600. Source ~/.profile (or the wrapper) then picks it up.
set -eu

FILE="$HOME/.gpg-passphrase"
umask 077

printf 'GPG signing passphrase: ' >&2
# Hide input where a terminal is available; never print the value.
if stty -echo 2>/dev/null; then
  trap 'stty echo 2>/dev/null || true; printf "\n" >&2' EXIT INT TERM
else
  printf '\n(input will be visible - no terminal available)\n' >&2
fi
IFS= read -r pw
if stty echo 2>/dev/null; then
  trap - EXIT INT TERM
fi
printf '\n' >&2

if [ -z "$pw" ]; then
  echo "Empty passphrase - nothing saved." >&2
  exit 1
fi

printf '%s\n' "$pw" > "$FILE"
chmod 600 "$FILE"
unset pw
echo "Saved GPG passphrase to $FILE (mode 600)."
