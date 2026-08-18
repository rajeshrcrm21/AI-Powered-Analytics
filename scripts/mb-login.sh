#!/usr/bin/env bash
# Reads ./.env (copied from .env.example) and logs the `mb` CLI into a named
# profile for this project. Run this once per teammate/machine.
#
# Usage: ./scripts/mb-login.sh

set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "No .env found. Copy .env.example to .env and fill in MB_URL / MB_API_KEY first." >&2
  exit 1
fi

# shellcheck disable=SC1091
set -a
source .env
set +a

: "${MB_URL:?Set MB_URL in .env}"
: "${MB_API_KEY:?Set MB_API_KEY in .env}"
: "${MB_PROFILE:=recruitcrm}"

echo "Logging in to ${MB_URL} as profile '${MB_PROFILE}'..."
echo "${MB_API_KEY}" | mb auth login --profile "${MB_PROFILE}" --url "${MB_URL}" --json

echo "Done. Verify with: mb auth status --profile ${MB_PROFILE} --json"
