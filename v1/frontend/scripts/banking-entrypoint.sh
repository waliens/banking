#!/bin/sh

ENTRYPOINTS_DIR="docker-entrypoint-banking.d"

if /usr/bin/find "/$ENTRYPOINTS_DIR/" -mindepth 1 -maxdepth 1 -type f -print -quit 2>/dev/null | read v; then
  echo >&2 "$0: /$ENTRYPOINTS_DIR/ is not empty, will attempt to perform configuration"

  echo >&2 "$0: Looking for shell scripts in /$ENTRYPOINTS_DIR/"
  find "/$ENTRYPOINTS_DIR/" -follow -type f -print | sort -V | while read -r f; do
    case "$f" in
      *.sh)
        if [ -x "$f" ]; then
          echo >&2 "$0: Launching $f";
          "$f"
        else
          # warn on shell scripts without exec bit
          echo >&2 "$0: Ignoring $f, not executable";
        fi
        ;;
      *) echo >&2 "$0: Ignoring $f";;
    esac
  done

  echo >&2 "$0: Configuration complete; ready for start up"
else
  echo >&2 "$0: No files found in /$ENTRYPOINTS_DIR/, skipping configuration"
fi

# executing next entrypoint
exec "$@"