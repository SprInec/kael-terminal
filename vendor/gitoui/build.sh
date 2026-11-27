#!/bin/sh
set -eu

src=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
data=${XDG_DATA_HOME:-"$HOME/.local/share"}
destination=${1:-"$data/kael-terminal/bin/gitoui"}
version=0.5.0
expected=55d66be11bd00f5c50d5727cc94fc9f67e6c61b28dafacd92646d5944143743f
url="https://static.crates.io/crates/gitoui/gitoui-$version.crate"

work=$(mktemp -d "${TMPDIR:-/tmp}/kael-gitoui.XXXXXX")
staged=
trap 'rm -rf -- "$work"; if [ -n "$staged" ]; then rm -f -- "$staged"; fi' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

archive=${2:-"$work/gitoui.crate"}
if [ "$#" -lt 2 ]; then
    curl --fail --silent --show-error --location --retry 2 --connect-timeout 15 \
        --output "$archive" "$url"
fi
if ! printf '%s  %s\n' "$expected" "$archive" | sha256sum --check --status; then
    echo "SHA-256 校验失败：$archive" >&2
    exit 1
fi

mkdir "$work/source"
tar -xzf "$archive" --strip-components=1 -C "$work/source"
for patch in \
    sixel-node-aspect.patch \
    tabby-sixel-and-smooth-graph.patch \
    terminal-graph-antialiasing.patch \
    compact-footer.patch
do
    patch --directory "$work/source" --strip=1 --batch --forward --fuzz=0 --input "$src/$patch"
done
cargo install --path "$work/source" --locked --root "$work/install" --bin gitoui
"$work/install/bin/gitoui" --version

directory=$(dirname -- "$destination")
mkdir -p "$directory"
staged=$(mktemp "$directory/.gitoui.XXXXXX")
install -m 755 "$work/install/bin/gitoui" "$staged"
mv -fT -- "$staged" "$destination"
staged=
