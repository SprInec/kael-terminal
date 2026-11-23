#!/bin/sh
set -eu
src=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
destination=${1:?Usage: build.sh /path/to/tmux}
archive="$src/independent-borders.tar.gz"
patch="$src/kael.patch"
expected=29bd6d51c7c4624c5bd2705c481eaf1ad01dd63cc34028e5b2e5d4e3ffd09582
printf '%s  %s\n' "$expected" "$archive" | sha256sum --check --status
patch_sum=$(sha256sum "$patch")
build_id="$expected ${patch_sum%% *}"
if [ -x "$destination" ] && [ -r "$destination.build" ] &&
   [ "$(cat "$destination.build")" = "$build_id" ]; then
    exit 0
fi

work=$(mktemp -d "${TMPDIR:-/tmp}/kael-tmux.XXXXXX")
trap 'rm -rf -- "$work"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
tar -xzf "$archive" --strip-components=1 -C "$work"
(
    cd "$work"
    patch --batch -p1 < "$patch"
    sh autogen.sh
    ./configure --disable-utf8proc --disable-debug --enable-images
    make -j "${KAEL_BUILD_JOBS:-$(getconf _NPROCESSORS_ONLN)}"
    ./tmux -V
)
mkdir -p "$(dirname -- "$destination")"
install -m 755 "$work/tmux" "$destination.new"
mv -fT -- "$destination.new" "$destination"
printf '%s\n' "$build_id" > "$destination.build"
