#!/usr/bin/env bash
set -euo pipefail
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
desktop=1
dry_run=0
use_apt=1
for argument in "$@"; do
    case "$argument" in
        --headless) desktop=0 ;;
        --dry-run) dry_run=1 ;;
        --skip-apt) use_apt=0 ;;
        -h|--help)
            echo '用法：./bootstrap.sh [--headless] [--dry-run] [--skip-apt]'
            exit 0
            ;;
        *) echo "未知参数：$argument" >&2; exit 2 ;;
    esac
done

machine=$(uname -m)
if [[ $(uname -s) != Linux || $machine != x86_64 && $machine != aarch64 ]]; then
    echo 'Bootstrap 支持 Ubuntu / Debian 系 Linux 的 x86_64 和 aarch64。' >&2
    exit 1
fi
if (( use_apt )) && ! command -v apt-get >/dev/null; then
    echo '未找到 apt-get。请按 README 手动安装系统依赖，再使用 --skip-apt。' >&2
    exit 1
fi

sudo_cmd=()
if (( EUID != 0 )); then
    sudo_cmd=(sudo)
fi
packages=(ca-certificates curl git zsh zsh-autosuggestions zsh-syntax-highlighting vim
          python3 python3-venv build-essential autoconf automake bison pkg-config patch
          libevent-dev libncurses-dev zlib1g-dev libpng-dev ncurses-bin ncurses-term
          file fd-find ripgrep jq unzip xz-utils)
if (( desktop )); then
    packages+=(fontconfig fonts-liberation xclip wl-clipboard chafa)
fi
tabby_version=1.0.238
codex_version=0.171.0
release_manifest="$root/libexec/releases.tsv"
deploy_args=()
if (( !desktop )); then
    deploy_args+=(--headless)
fi
if (( dry_run )); then
    if (( use_apt )); then
        printf 'APT 依赖：%s\n' "${packages[*]}"
    fi
    awk -v machine="$machine" -v desktop="$desktop" \
        '$2 == machine && ($1 != "tabby" || desktop) { print $1, $4 }' "$release_manifest"
    printf '构建定制 tmux，安装 Codex %s 和 Dooit。\n' "$codex_version"
    exec "$root/install.sh" --dry-run "${deploy_args[@]}"
fi

if (( use_apt )); then
    "${sudo_cmd[@]}" apt-get update
    "${sudo_cmd[@]}" apt-get install -y "${packages[@]}"
fi

data="${XDG_DATA_HOME:-$HOME/.local/share}/kael-terminal"
cache="${XDG_CACHE_HOME:-$HOME/.cache}/kael-terminal/downloads"
mkdir -p "$data/bin" "$data/opt" "$cache"
exec 9>"$data/bootstrap.lock"
flock 9
work=$(mktemp -d "$data/.bootstrap.XXXXXX")
trap 'rm -rf -- "$work"' EXIT

download() {
    local url=$1 expected=$2 archive=$3
    if [[ -f $archive ]] &&
       printf '%s  %s\n' "$expected" "$archive" | sha256sum --check --status; then
        return
    fi
    echo "下载 ${url##*/}"
    curl --fail --silent --show-error --location --retry 2 --connect-timeout 15 \
        --output "$work/download" "$url"
    if ! printf '%s  %s\n' "$expected" "$work/download" | sha256sum --check --status; then
        echo "SHA-256 校验失败：$url" >&2
        return 1
    fi
    mv -fT -- "$work/download" "$archive"
}

link_command() {
    local target=$1 name=$2
    ln -sfnT -- "$target" "$data/bin/$name"
}

install_binary() {
    local name=$1 destination=$2 build=$3
    local -a matches=()
    mapfile -d '' -t matches < <(find "$build" -type f -name "$name" -print0)
    if (( ${#matches[@]} != 1 )); then
        echo "压缩包中找不到唯一的可执行文件：$name" >&2
        return 1
    fi
    install -m 755 "${matches[0]}" "$destination"
}

while read -r tool architecture checksum url; do
    [[ $architecture == "$machine" ]] || continue
    if [[ $tool == tabby ]]; then
        (( desktop )) || continue
        if [[ $(dpkg-query -W -f='${Version}' tabby-terminal 2>/dev/null || :) == "$tabby_version" ]] &&
           command -v tabby >/dev/null; then
            continue
        fi
        if (( !use_apt )); then
            if command -v tabby >/dev/null; then
                continue
            fi
            echo '使用 --skip-apt 时请预装 Tabby，或同时指定 --headless。' >&2
            exit 1
        fi
    fi
    asset="$cache/${url##*/}"
    if [[ $tool == tabby ]]; then
        download "$url" "$checksum" "$asset"
        "${sudo_cmd[@]}" apt-get install -y "$asset"
        continue
    fi

    release="$data/opt/$tool-$checksum"
    if [[ ! -d $release ]]; then
        download "$url" "$checksum" "$asset"
        extraction="$work/$tool-extracted"
        staged="$work/$tool"
        mkdir "$extraction" "$staged"
        case "$asset" in
            *.zip) unzip -q "$asset" -d "$extraction" ;;
            *) tar -xf "$asset" -C "$extraction" ;;
        esac
        case "$tool" in
            node)
                cp -a "$extraction"/node-v*/. "$staged/"
                ;;
            yazi)
                install_binary yazi "$staged/yazi" "$extraction"
                install_binary ya "$staged/ya" "$extraction"
                ;;
            *) install_binary "$tool" "$staged/$tool" "$extraction" ;;
        esac
        mv -T -- "$staged" "$release"
    fi
    case "$tool" in
        node)
            link_command "$release/bin/node" node
            link_command "$release/bin/npm" npm
            ;;
        yazi)
            link_command "$release/yazi" yazi
            link_command "$release/ya" ya
            ;;
        *) link_command "$release/$tool" "$tool" ;;
    esac
done < "$release_manifest"

if command -v fdfind >/dev/null; then
    link_command "$(command -v fdfind)" fd
fi
export PATH="$data/bin:$PATH"
if [[ $("$data/bin/codex" --version 2>/dev/null || :) != "codex-cli $codex_version" ]]; then
    npm install --global --prefix "$data" --no-audit --no-fund "@openai/codex@$codex_version"
fi

requirements="$root/libexec/dooit-requirements.txt"
requirements_hash=$(sha256sum "$requirements")
venv="$data/opt/dooit-${requirements_hash%% *}"
if [[ ! -f $venv/.ready ]]; then
    /usr/bin/python3 -m venv "$venv"
    "$venv/bin/python" -m pip install --disable-pip-version-check -r "$requirements"
    touch "$venv/.ready"
fi
link_command "$venv/bin/dooit" dooit

"$root/vendor/tmux/build.sh" "$data/bin/tmux"
if (( desktop )); then
    plugins="$root/config/tabby/plugins"
    hash=$(cd "$plugins" && find package.json package-lock.json local -type f -print0 |
        sort -z | xargs -0 sha256sum | sha256sum)
    registry="$data/opt/tabby-plugins-${hash%% *}"
    if [[ ! -d $registry ]]; then
        mkdir "$work/tabby-plugins"
        cp -a "$plugins/package.json" "$plugins/package-lock.json" "$plugins/local" "$work/tabby-plugins/"
        npm ci --prefix "$work/tabby-plugins" --ignore-scripts --no-fund --no-audit
        mv -T -- "$work/tabby-plugins" "$registry"
    fi
    deploy_args+=(--tabby-modules "$registry/node_modules")
fi
"$root/install.sh" "${deploy_args[@]}"
printf '\n安装完成。新开 Tabby 或运行 exec zsh -l 加载配置。\n'
