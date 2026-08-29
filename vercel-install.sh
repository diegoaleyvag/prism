#!/usr/bin/env bash
# Prepare Vercel's Linux build environment for Prism's static Vite export.
set -euo pipefail

readonly UV_VERSION="0.11.11"
readonly UV_ARCHIVE="uv-x86_64-unknown-linux-gnu.tar.gz"
readonly UV_SHA256="a767848254391855c96df271e9ca8b7f72dd172d310460447853d25d907b9ae0"
readonly UV_URL="https://releases.astral.sh/github/uv/releases/download/${UV_VERSION}/${UV_ARCHIVE}"
readonly UV_BIN_DIR="${HOME}/.local/bin"

archive_path="$(mktemp)"
trap 'rm -f "${archive_path}"' EXIT

mkdir -p "${UV_BIN_DIR}"
curl --fail --silent --show-error --location --output "${archive_path}" "${UV_URL}"
printf '%s  %s\n' "${UV_SHA256}" "${archive_path}" | sha256sum --check --status
tar -xzf "${archive_path}" -C "${UV_BIN_DIR}" --strip-components=1 --no-same-owner

export PATH="${UV_BIN_DIR}:${PATH}"
uv sync --frozen
corepack enable
pnpm --dir explorer install --frozen-lockfile
