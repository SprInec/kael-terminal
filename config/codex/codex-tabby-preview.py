#!/usr/bin/env python3
"""Run Codex fullscreen with Sixel previews in Tabby and supported tmux panes."""

import fcntl
import os
from pathlib import Path
import re
import select
import signal
import struct
import subprocess
import sys
import tempfile
import termios
import time
import tty


SIXEL_SOCKET = "kael-borders-sixel"
MUX_VARIABLES = ("TMUX", "TMUX_PANE", "STY", "ZELLIJ", "ZELLIJ_SESSION_NAME", "ZELLIJ_VERSION")

CODEX_VALUE_OPTIONS = {
    "-a", "-c", "-C", "-i", "-m", "-p", "-s",
    "--add-dir", "--ask-for-approval", "--cd", "--config", "--disable", "--enable",
    "--image", "--local-provider", "--model", "--profile", "--remote",
    "--remote-auth-token-env", "--sandbox",
}
CODEX_MANAGEMENT_COMMANDS = {
    "a", "app", "app-server", "apply", "archive", "cloud", "completion", "debug", "delete",
    "doctor", "e", "exec", "exec-server", "features", "help", "login", "logout", "mcp",
    "mcp-server", "migrate-nfs-db", "migrate-rollouts", "plugin", "queue", "remote-control",
    "review", "sandbox", "unarchive", "update",
}


def uses_interactive_preview(arguments):
    positional_seen = False
    options = iter(arguments)
    for argument in options:
        if argument == "--":
            break
        if argument in {"-h", "--help", "-V", "--version", "--no-alt-screen"}:
            return False
        if argument in CODEX_VALUE_OPTIONS:
            next(options, None)
        elif not positional_seen and not argument.startswith("-"):
            if argument in CODEX_MANAGEMENT_COMMANDS:
                return False
            positional_seen = True
    return True


def tabby_terminal_mode():
    term_program = os.environ.get("TERM_PROGRAM", "").lower()
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return None
    if any(os.environ.get(key) for key in MUX_VARIABLES[2:]):
        return None
    socket = os.environ.get("TMUX", "").rsplit(",", 2)[0]
    if not (os.environ.get("TABBY_CONFIG_DIRECTORY") or term_program == "tabby" or
            Path(socket).name == SIXEL_SOCKET):
        return None
    if socket:
        return "tmux" if tmux_can_display_sixel(socket) else None
    if term_program != "tmux" and not os.environ.get("TMUX_PANE"):
        return "direct"
    return None


def tmux_can_display_sixel(socket):
    pane = os.environ.get("TMUX_PANE", "")
    if not re.fullmatch(r"%[0-9]+", pane):
        return False
    data = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")
    built_tmux = data / "kael-terminal/bin/tmux"
    tmux = os.environ.get("KAEL_TMUX_BIN") or (built_tmux if built_tmux.is_file() else "tmux")
    try:
        result = subprocess.run(
            [tmux, "-S", socket, "display-message", "-p", "-t", pane,
             "#{sixel_support}\t#{client_termfeatures}"],
            capture_output=True, text=True, timeout=1, check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    enabled, _, features = result.stdout.strip().partition("\t")
    return enabled == "1" and "sixel" in features.split(",")


def query_cell_pixels(fd):
    mode = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd, termios.TCSANOW)
        os.write(fd, b"\x1b[16t")
        deadline = time.monotonic() + 1.5
        reply = b""
        while select.select([fd], [], [], max(0, deadline - time.monotonic()))[0]:
            chunk = os.read(fd, 128)
            if not chunk:
                break
            reply = (reply + chunk)[-256:]
            match = re.search(rb"\x1b\[6;([1-9]\d{0,3});([1-9]\d{0,3})t", reply)
            if match:
                height, width = map(int, match.groups())
                return width, height
            if time.monotonic() >= deadline:
                break
    finally:
        termios.tcsetattr(fd, termios.TCSANOW, mode)
    raise RuntimeError("Tabby 没有返回字符像素尺寸。请启用 Sixel graphics support 并新开标签页。")


def update_window_pixels(fd, cell_width, cell_height):
    size = fcntl.ioctl(fd, termios.TIOCGWINSZ, b"\0" * 8)
    rows, columns, width, height = struct.unpack("HHHH", size)
    if (width and height) or not (rows and columns):
        return
    # Tabby's PTY provides rows and columns, but Codex's Sixel renderer needs pixels.
    width, height = columns * cell_width, rows * cell_height
    if max(width, height) > 65535:
        raise RuntimeError("Tabby 的窗口像素尺寸超出了 PTY 支持范围。")
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, columns, width, height))


def run_with_preview(arguments, mode):
    with tempfile.TemporaryDirectory(prefix="codex-tabby-") as directory:
        # In tmux, keep the pane's key and color capabilities and let tmux parse Sixel natively.
        term = "tmux-sixel" if mode == "tmux" else "xterm-sixel"
        base_term = os.environ.get("TERM", "screen") if mode == "tmux" else "xterm-256color"
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9+_.-]*", base_term) or base_term == term:
            raise RuntimeError("无法读取终端的 terminfo 类型。")
        source = Path(directory) / "sixel.ti"
        source.write_text(
            f"{term}|{base_term} with Sixel,\n\tuse={base_term},\n", encoding="ascii"
        )
        subprocess.run(["tic", "-x", "-o", directory, source], check=True)
        env = os.environ.copy()
        env["TERM"] = term
        env["TERMINFO_DIRS"] = directory + os.pathsep + env.get("TERMINFO_DIRS", "")
        # Codex checks TERM_PROGRAM before consulting the Sixel capability in TERM.
        env.pop("TERM_PROGRAM", None)
        env.pop("TERM_PROGRAM_VERSION", None)
        if mode == "tmux":
            # Codex 0.171.0 disables native Sixel when it detects tmux.
            env.pop("TMUX", None)
            env.pop("TMUX_PANE", None)
        else:
            configure_tabby_window_pixels()

        command = ["codex", "-c", "tui.fullscreen_transcript=true", *arguments]
        result = subprocess.run(command, env=env)
        return result.returncode if result.returncode >= 0 else 128 - result.returncode


def configure_tabby_window_pixels():
    fd = sys.stdin.fileno()
    cell_width, cell_height = query_cell_pixels(fd)
    update_window_pixels(fd, cell_width, cell_height)

    def on_resize(_signum, _frame):
        try:
            update_window_pixels(fd, cell_width, cell_height)
        except (OSError, RuntimeError):
            pass  # The PTY may have closed or be between valid sizes.

    signal.signal(signal.SIGWINCH, on_resize)


def main(arguments):
    if arguments[:1] != ["--tabby-default"]:
        mode = tabby_terminal_mode()
        if mode is None:
            raise RuntimeError("请在 Tabby 的本地标签页或已启用 Sixel 的 tmux 窗格中运行此脚本。")
        return run_with_preview(arguments, mode)

    arguments = arguments[1:]
    mode = tabby_terminal_mode() if uses_interactive_preview(arguments) else None
    if mode:
        try:
            return run_with_preview(arguments, mode)
        except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
            print(f"Tabby 图片预览：{error}", file=sys.stderr)
    os.execvp("codex", ["codex", *arguments])


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
    except KeyboardInterrupt:
        sys.exit(130)
