#!/usr/bin/env bash
# Loop Engineer: shared continuous-learning-v2 data-directory resolver.
#
# Resolution precedence:
#   1. CLV2_INSTINCT_STORE_DIR, when absolute (legacy alias: CLV2_HOMUNCULUS_DIR)
#   2. XDG_DATA_HOME/loop-engineer-instinct-store, when XDG_DATA_HOME is absolute
#   3. HOME/.local/share/loop-engineer-instinct-store

_clv2_resolve_homunculus_dir() {
  if [ -n "${CLV2_HOMUNCULUS_DIR:-}" ]; then
    case "$CLV2_HOMUNCULUS_DIR" in
      /*) printf '%s\n' "$CLV2_HOMUNCULUS_DIR"; return 0 ;;
      *) printf '[loop-engineer] CLV2_HOMUNCULUS_DIR=%s is not absolute; ignoring\n' "$CLV2_HOMUNCULUS_DIR" >&2 ;;
    esac
  fi

  if [ -n "${XDG_DATA_HOME:-}" ]; then
    case "$XDG_DATA_HOME" in
      /*) printf '%s/loop-engineer-homunculus\n' "$XDG_DATA_HOME"; return 0 ;;
      *) printf '[loop-engineer] XDG_DATA_HOME=%s is not absolute; ignoring\n' "$XDG_DATA_HOME" >&2 ;;
    esac
  fi

  case "${HOME:-}" in
    /*) printf '%s/.local/share/loop-engineer-homunculus\n' "$HOME" ;;
    *)
      printf '[loop-engineer] HOME=%s is not absolute; cannot resolve instinct-store dir\n' "${HOME:-}" >&2
      return 1
      ;;
  esac
}
