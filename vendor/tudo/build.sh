#!/bin/sh
set -eu

src=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
destination=${1:-"$HOME/.local/bin/tudo"}
version=1.1.0
expected=4698f5ba80679b158bf6667ed4168215028d1c71df061e4e8656741cdce4cf18
url="https://api.github.com/repos/jolleyDesign/tudo/tarball/v$version"

work=$(mktemp -d "${TMPDIR:-/tmp}/kael-tudo.XXXXXX")
staged=
trap 'rm -rf -- "$work"; if [ -n "$staged" ]; then rm -f -- "$staged"; fi' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

archive=${2:-"$work/tudo.tar.gz"}
if [ -z "${2:-}" ]; then
    curl --fail --silent --show-error --location --retry 2 --connect-timeout 15 \
        --output "$archive" "$url"
fi
if ! printf '%s  %s\n' "$expected" "$archive" | sha256sum --check --status; then
    printf 'SHA-256 校验失败：%s\n' "$archive" >&2
    exit 1
fi

mkdir "$work/source"
tar -xzf "$archive" --strip-components=1 -C "$work/source"
for patch in kael-tmux-theme.patch input-cursor.patch; do
    patch --directory "$work/source" --strip=1 --batch --forward --fuzz=0 \
        --input "$src/$patch"
done
cargo build --manifest-path "$work/source/Cargo.toml" --target-dir "$work/target" \
    --release --locked --bin tudo
"$work/target/release/tudo" --version

directory=$(dirname -- "$destination")
mkdir -p "$directory"
staged=$(mktemp "$directory/.tudo.XXXXXX")
install -m 755 "$work/target/release/tudo" "$staged"
mv -fT -- "$staged" "$destination"
staged=
