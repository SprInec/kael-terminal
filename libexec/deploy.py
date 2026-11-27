#!/usr/bin/env python3
"""Install the tracked terminal configuration and keep a per-run rollback journal."""

import argparse
from contextlib import nullcontext
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config"
HOME = Path.home()


def location(variable, default):
    value = os.environ.get(variable)
    return Path(value).expanduser().absolute() if value else default


XDG_CONFIG = location("XDG_CONFIG_HOME", HOME / ".config")
XDG_DATA = location("XDG_DATA_HOME", HOME / ".local/share")
XDG_STATE = location("XDG_STATE_HOME", HOME / ".local/state")
CODEX = location("CODEX_HOME", HOME / ".codex")
TABBY = location("TABBY_CONFIG_DIRECTORY", XDG_CONFIG / "tabby")
ATUIN = location("ATUIN_CONFIG_DIR", location("ATUIN_HOME", HOME / ".atuin"))
ZSHRC = location("ZDOTDIR", HOME) / ".zshrc"
DATA = XDG_DATA / "kael-terminal"
STATE = XDG_STATE / "kael-terminal"
FONT_DIR = XDG_DATA / "fonts" / "kael-terminal"
BEGIN = b"# >>> kael-terminal >>>"
END = b"# <<< kael-terminal <<<"
LEGACY_ZSHRC = "dbb541a13f8cffb9b1ee3f7298bcc7f008b3651b174c33b631e181aa94053073"
PLUGINS = CONFIG / "tabby/plugins"


@dataclass
class File:
    target: Path
    content: bytes = b""
    mode: int = 0o644
    link: str | None = None

    def fingerprint(self):
        if self.link is not None:
            return {"link": self.link}
        return {"sha256": hashlib.sha256(self.content).hexdigest(), "mode": self.mode}

    def install(self):
        self.target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".kael-", dir=self.target.parent) as work:
            temporary = Path(work) / "file"
            if self.link is not None:
                temporary.symlink_to(self.link)
            else:
                temporary.write_bytes(self.content)
                temporary.chmod(self.mode)
            temporary.replace(self.target)


def read_file(path):
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return None
    if stat.S_ISLNK(mode):
        return File(path, link=os.readlink(path))
    if not stat.S_ISREG(mode):
        raise ValueError(f"部署目标不是普通文件或链接：{path}")
    return File(path, path.read_bytes(), stat.S_IMODE(mode))


def file_fingerprint(file):
    return None if file is None else file.fingerprint()


def managed_zshrc():
    original = ZSHRC.read_bytes() if ZSHRC.exists() else b""
    managed = (CONFIG / "zsh/zshrc").read_bytes()
    if hashlib.sha256(original).hexdigest() == LEGACY_ZSHRC:
        return managed
    if BEGIN in original or END in original:
        pattern = re.compile(rb"(?m)^" + re.escape(BEGIN) + rb"\r?\n[\s\S]*?^" +
                             re.escape(END) + rb"(?:\r?\n|\Z)")
        if original.count(BEGIN) != 1 or original.count(END) != 1 or not pattern.search(original):
            raise ValueError(f"配置片段标记不完整：{ZSHRC}")
        return pattern.sub(lambda _: managed, original, count=1)
    if original:
        return original + (b"" if original.endswith(b"\n") else b"\n") + b"\n" + managed
    return managed


def tmux_quote(path):
    escaped = str(path).replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$")
    return '"' + escaped + '"'


def tabby_dependencies():
    return json.loads((PLUGINS / "package.json").read_bytes())["dependencies"]


def nvim_config_files():
    nvim = XDG_CONFIG / "nvim"
    init_lua = nvim / "init.lua"
    init_vim = nvim / "init.vim"
    lazy_config = nvim / "lua/config/lazy.lua"
    extensions = ("lua/plugins/kael-statusline.lua", "lua/kael/statusline-icons.json")
    mapping = {}

    if init_lua.exists() or init_lua.is_symlink():
        entry = init_lua.read_bytes() if init_lua.is_file() and not init_lua.is_symlink() else b""
        lazy_setup = lazy_config.read_bytes() if lazy_config.is_file() else b""
        local_profile = (entry == b'require("config.lazy")\n' and
                         lazy_setup == (CONFIG / "nvim/lua/config/lazy.lua").read_bytes())
        if not (entry.startswith(b"-- Managed by kael-terminal.\n") or local_profile):
            if b"LazyVim/LazyVim" in lazy_setup:
                return {f"nvim/{relative}": nvim / relative for relative in extensions}
            return mapping
        mapping["nvim/init.lua"] = init_lua
    elif init_vim.exists() or init_vim.is_symlink():
        if not init_vim.is_file() or init_vim.is_symlink():
            return mapping
        entry = init_vim.read_bytes()
        if entry != (CONFIG / "vim/init.vim").read_bytes() and not entry.startswith(b'" Managed by kael-terminal.\n'):
            return mapping
        mapping["vim/kael-init.vim"] = init_vim
        mapping["nvim/init.lua"] = nvim / "lua/kael/init.lua"
    else:
        mapping["nvim/init.lua"] = init_lua

    for relative in ("lazy-lock.json", "lua/config/lazy.lua", "lua/config/options.lua",
                     "lua/plugins/appearance.lua", "lua/plugins/editor.lua", *extensions):
        mapping[f"nvim/{relative}"] = nvim / relative
    return mapping


def config_files(headless, tabby_modules):
    zsh = shutil.which("zsh") or "/usr/bin/zsh"
    tokens = {
        "@@TMUX_STATUS@@": tmux_quote(XDG_CONFIG / "tmux/status.conf"),
        "@@TMUX_BASE@@": tmux_quote(HOME / ".tmux.conf"),
        "@@ZSH@@": tmux_quote(zsh),
        "@@ADA_PYTHON@@": json.dumps(shutil.which("/usr/bin/python3") or "python3"),
        "@@ADA_SCRIPT@@": json.dumps(str(CODEX / "statusline/ada-usage-statusline/statusline.py"),
                                    ensure_ascii=False),
    }
    files = [
        File(ZSHRC, managed_zshrc(), 0o600),
        File(DATA / "bin/kael-tmux", (ROOT / "bin/kael-tmux").read_bytes(), 0o755),
    ]
    mapping = {
        "zsh/terminal-tools.zsh": XDG_CONFIG / "kael-terminal/terminal-tools.zsh",
        "tmux/tmux.conf": HOME / ".tmux.conf",
        "tmux/status.conf": XDG_CONFIG / "tmux/status.conf",
        "tmux/independent-borders.conf": XDG_CONFIG / "tmux/independent-borders.conf",
        "tmux/status.py": XDG_CONFIG / "tmux/status.py",
        "starship/starship.toml": XDG_CONFIG / "starship.toml",
        "starship/git-host.py": XDG_CONFIG / "starship/git-host.py",
        "codex/config.toml": CODEX / "config.toml",
        "codex/ada-statusline.py": CODEX / "statusline/ada-usage-statusline/statusline.py",
        "codex/codex-tabby-preview.py": DATA / "codex-tabby-preview.py",
        "yazi/yazi.toml": XDG_CONFIG / "yazi/yazi.toml",
        "yazi/theme.toml": XDG_CONFIG / "yazi/theme.toml",
        "yazi/init.lua": XDG_CONFIG / "yazi/init.lua",
        "btop/btop.conf": XDG_CONFIG / "btop/btop.conf",
        "atuin/config.toml": ATUIN / "config.toml",
        "glow/glow.yml": XDG_CONFIG / "glow/glow.yml",
        "vim/vimrc": HOME / ".vimrc",
    }
    mapping.update(nvim_config_files())
    for name in ("config.py", "task_notes.py", "text_selection.py"):
        mapping[f"dooit/{name}"] = XDG_CONFIG / "dooit" / name
    if not headless:
        mapping["tabby/config.yaml"] = TABBY / "config.yaml"
        yazi_icons = "yazi/plugins/kael-yazi-icons.yazi/main.lua"
        mapping[yazi_icons] = XDG_CONFIG / yazi_icons
        for source in sorted(PLUGINS.rglob("*")):
            relative = source.relative_to(PLUGINS)
            if source.is_file() and "node_modules" not in relative.parts:
                mapping[str(source.relative_to(CONFIG))] = TABBY / "plugins" / relative
        for name, dependency in tabby_dependencies().items():
            target = TABBY / "plugins/node_modules" / name
            if dependency.startswith("file:"):
                if target.is_dir() and not target.is_symlink():
                    raise ValueError(f"本地 Tabby 插件目录与托管链接冲突：{target}")
                files.append(File(target, link=f"../local/{name}"))
            elif tabby_modules and (target.is_symlink() or not target.is_dir()):
                source = tabby_modules.absolute() / name
                if not (source / "package.json").is_file():
                    raise ValueError(f"Tabby 插件未安装：{source}")
                files.append(File(target, link=str(source)))
        for source in sorted((ROOT / "fonts").glob("*/*.ttf")):
            files.append(File(FONT_DIR / source.name, source.read_bytes()))
        license_source = ROOT / "fonts/SauceCodeProNF/LICENSE.txt"
        files.append(File(FONT_DIR / "SauceCodePro-LICENSE.txt", license_source.read_bytes()))
    for relative, target in mapping.items():
        content = (CONFIG / relative).read_bytes()
        for token, replacement in tokens.items():
            content = content.replace(token.encode(), replacement.encode())
        mode = 0o600 if target in (CODEX / "config.toml", TABBY / "config.yaml") else 0o644
        files.append(File(target, content, mode))
    return files


def journal():
    backups = STATE / "backups"
    backups.mkdir(mode=0o700, parents=True, exist_ok=True)
    prefix = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ-")
    return Path(tempfile.mkdtemp(prefix=prefix, dir=backups))


def apply(args):
    changes = []
    for new in config_files(args.headless, args.tabby_modules):
        before = read_file(new.target)
        if file_fingerprint(before) != new.fingerprint():
            changes.append((new, before))
    if not changes:
        print("配置已是当前版本。")
        return
    for new, before in changes:
        print(f"{'更新并备份' if before else '添加'} {new.target}")
    if args.dry_run:
        return

    backup = journal()
    manifest = []
    for index, (new, before) in enumerate(changes):
        snapshot = str(index)
        if before is not None:
            File(backup / snapshot, before.content, before.mode, before.link).install()
        manifest.append({"target": str(new.target), "snapshot": snapshot,
                         "before": file_fingerprint(before), "after": new.fingerprint()})
    File(backup / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2).encode(),
         0o600).install()
    print(f"回滚备份位于 {backup}", flush=True)
    try:
        for new, _ in changes:
            new.install()
    except (OSError, KeyboardInterrupt):
        restore(backup, manifest, force=False, dry_run=False)
        raise
    refresh_fonts(manifest)


def latest_backup():
    for manifest in sorted((STATE / "backups").glob("*/manifest.json"), reverse=True):
        if not (manifest.parent / "restored").exists():
            return manifest
    raise ValueError("没有可回滚的部署。")


def restore(backup, manifest, force, dry_run):
    changes = []
    conflicts = []
    for entry in reversed(manifest):
        target = Path(entry["target"])
        current = file_fingerprint(read_file(target))
        if current == entry["before"]:
            continue
        if current != entry["after"] and not force:
            conflicts.append(str(target))
        snapshot = read_file(backup / entry["snapshot"])
        if file_fingerprint(snapshot) != entry["before"]:
            raise ValueError(f"回滚备份不完整：{target}")
        changes.append((target, snapshot))
    if conflicts:
        raise ValueError("以下配置部署后已被修改，请先保存它们，或显式使用 --force：\n" +
                         "\n".join(conflicts))
    for target, snapshot in changes:
        print(f"{'恢复' if snapshot else '移除'} {target}")
        if dry_run:
            continue
        if snapshot:
            File(target, snapshot.content, snapshot.mode, snapshot.link).install()
        else:
            target.unlink(missing_ok=True)
    if not dry_run:
        File(backup / "restored").install()
        refresh_fonts(manifest)


def refresh_fonts(manifest):
    if shutil.which("fc-cache") and any(Path(entry["target"]).parent == FONT_DIR for entry in manifest):
        subprocess.run(["fc-cache", "-f", str(FONT_DIR)], check=False)


def doctor(headless):
    paths = os.pathsep.join((str(DATA / "bin"), str(HOME / ".local/bin"), os.environ.get("PATH", "")))
    commands = "zsh tmux codex starship yazi ya zoxide vim fzf eza tree dust btop dooit atuin bat glow kael-tmux"
    if not headless:
        commands += " tabby"
    missing = []
    for command in commands.split():
        executable = shutil.which(command, path=paths)
        print(f"{command:12s} {executable or '缺失'}")
        if not executable:
            missing.append(command)
    custom_tmux = location("KAEL_TMUX_BIN", DATA / "bin/tmux")
    if not os.access(custom_tmux, os.X_OK):
        print(f"定制 tmux    缺失（{custom_tmux}）")
        missing.append("custom tmux")
    if not headless:
        for name in tabby_dependencies():
            if not (TABBY / "plugins/node_modules" / name / "package.json").is_file():
                print(f"Tabby 插件   缺失（{name}）")
                missing.append(name)
    return int(bool(missing))


def main():
    parser = argparse.ArgumentParser(description="部署、检查或回滚 Kael 终端配置")
    parser.add_argument("action", nargs="?", default="apply", choices=("apply", "rollback", "doctor"))
    parser.add_argument("--headless", action="store_true", help="跳过 Tabby 与桌面字体")
    parser.add_argument("--dry-run", action="store_true", help="预览将变更的文件")
    parser.add_argument("--force", action="store_true", help="回滚时允许覆盖后来修改过的配置")
    parser.add_argument("--tabby-modules", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.action == "doctor":
        return doctor(args.headless)

    if not args.dry_run:
        STATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    lock = nullcontext() if args.dry_run else (STATE / "install.lock").open("a")
    with lock as handle:
        if handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
        if args.action == "apply":
            apply(args)
        else:
            manifest = latest_backup()
            restore(manifest.parent, json.loads(manifest.read_bytes()), args.force, args.dry_run)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError) as error:
        sys.exit(str(error))
