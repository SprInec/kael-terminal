<div align="center">

# kael-terminal

[![MIT license](https://img.shields.io/badge/License-MIT-26734D?style=flat-square)](LICENSE) [![Linux support for Ubuntu and Debian](https://img.shields.io/badge/Linux-Ubuntu%20%2B%20Debian-355E8D?style=flat-square)](#quick-start) [![Builds for x86_64 and aarch64](https://img.shields.io/badge/Arch-x86__64%20%2B%20aarch64-635B9A?style=flat-square)](#quick-start)

A terminal setup for Linux workstations and servers. Zsh and Starship give you a consistent prompt and shortcuts, a customized tmux keeps work sessions running, and a set of CLI tools covers browsing, searching, editing, and task management. The desktop setup adds Tabby, fonts, and Sixel image previews.

[简体中文](README.md) · **English**

[Quick start](#quick-start) · [Everyday tools](#everyday-tools) · [Work sessions](#work-sessions) · [Customize and roll back](#customize-and-roll-back) · [License](#license)

</div>

## Quick start

Start with **Git, Bash, and Python 3.10 or newer**. The installer targets APT-based Ubuntu and Debian systems on **x86_64** and **aarch64**. A full install needs access to APT repositories, GitHub, Node.js downloads, npm, and PyPI. It uses `sudo` for system packages. Close Tabby before a desktop install.

```sh
git clone https://github.com/SprInec/kael-terminal.git
cd kael-terminal
./bootstrap.sh --dry-run
./bootstrap.sh
exec zsh -l
```

The dry run lists dependencies and files that would change. The full run verifies the SHA-256 checksums in the download manifest, builds the customized tmux, and applies configuration for the current user. The default desktop mode also installs Tabby, its plugins, and fonts.

| Setup | Command |
| --- | --- |
| SSH or headless server | `./bootstrap.sh --headless` |
| System dependencies already installed | `./bootstrap.sh --skip-apt` |
| Apply configuration to existing tools | `./install.sh` or `./install.sh --headless` |
| Check executables and plugins | `./install.sh doctor` or `./install.sh doctor --headless` |

Add `--dry-run` to the setup you want to preview, for example `./bootstrap.sh --headless --dry-run`. If you skip APT, use the preview to see which dependencies to install manually. For desktop mode, install Tabby first. A configuration-only install enables the two bundled Tabby plugins. The full bootstrap also installs the third-party npm plugins.

## Everyday tools

The examples use files from this repository. After installing, return to the repository in a new Zsh session to try them.

### Completion, history, and directory jumps

- **Zsh + Starship** provide shell completion, history suggestions, syntax highlighting, and a prompt with Git remote icons. Press `Tab` after part of a command or path to complete it. Enter a Git repository to see its branch in the prompt.
- **Atuin** searches previously run commands. Press `Ctrl+R` and type part of a command. Press `Tab` to put the result on the command line for editing, or `Enter` to run it. Automatic sync is disabled by default. [Atuin usage guide](https://docs.atuin.sh/main/guide/basic-usage/)
- **fzf** finds fuzzy matches. Press `Ctrl+T` in Zsh to pick a file path and insert it on the command line. You can also pipe a list into fzf, as in `rg --files config | fzf`.
- **zoxide** remembers directories you visit. Visit a directory with `cd`, then use `z kael-terminal` to jump back or `zi kael` to pick from matching directories. [zoxide usage guide](https://github.com/ajeetdsouza/zoxide#getting-started)

### Browse, search, and read

Run `y config` to open **Yazi**. Browse with the arrow keys and quit with `q`. Zsh moves to the directory you were viewing. `y` is an alias for `yazi`, and `ya pkg list` lists Yazi plugins. [Yazi quick start](https://yazi-rs.github.io/docs/quick-start/)

| Tool | Example | What it does |
| --- | --- | --- |
| **ls** | `ll`, `la`, `l` | Show a detailed listing, include hidden entries, or list in columns |
| **eza** | `lt`, `lgit` | Show a two-level directory tree or a listing with Git status |
| **fd** | `fd -e toml . config` | Find configuration files by extension |
| **ripgrep** | `rg -n 'starship' config` | Search file contents and show line numbers |
| **bat** | `bat bootstrap.sh` | Read a script with syntax highlighting and line numbers |
| **Glow** | `glow README_en.md` | Render Markdown in the terminal |
| **Vim** | `vim README_en.md` | Press `i` to edit, then `Esc` and `:wq` followed by Enter to save and exit |

Use **jq** to extract fields from JSON. The command below lists Tabby's plugin dependencies.

```sh
jq '.dependencies | keys' config/tabby/plugins/package.json
```

### Tasks, system resources, and runtimes

- **Dooit** manages to-do lists in the terminal. Run `dooit` and press `a` in the task list to add a task at the same level. Press `c` to toggle completion. Select a task and press `n` to edit its note, then `Esc` to save and return. Press `Ctrl+N` to toggle the workspace list or `?` to see all shortcuts. [Dooit usage guide](https://dooit-org.github.io/dooit/getting_started/basics.html)
- **dust** helps locate large directories. Run `dust .` to see how much disk space the current directory and its contents use.
- **btop** shows live CPU, memory, disk, network, and process metrics. Run `btop` to open the dashboard and press `q` to exit.
- **Node.js + npm** support Codex CLI and Tabby plugins. Run `node --version` and `npm --version` to check the installation.
- **Conda** loads automatically in Zsh if Anaconda is already installed at `~/anaconda3`. Run `conda env list` to see existing environments.

## Work sessions

### tmux

The customized tmux has separate pane borders, focus highlighting, transfer progress, a menu for floating panes, and a status bar with Git and system metrics. Start a named session from outside tmux.

```sh
kael-tmux new-session -A -s dev
```

Running `kael-tmux` with no arguments creates or attaches to the `work` session. For the shortcuts below, press `Ctrl+B`, release it, then press the next key.

| Key after the prefix | Action |
| --- | --- |
| `%` / `"` | Split side by side / top and bottom |
| Arrow keys | Move between panes |
| `F` (uppercase) | Toggle the active pane between floating and tiled |
| `d` | Detach while programs keep running |

The pane's right-click menu also offers commands to split, move, and resize panes. Use the same startup command to reattach to `dev`, or run `kael-tmux list-sessions` to see sessions on the current socket.

### Tabby

Run `tabby` to launch the desktop terminal with Zsh as its default profile. Press `Ctrl+Shift+T` for a new tab, `Ctrl+Shift+C` to copy, and `Ctrl+Shift+V` to paste. The desktop setup applies themes and fonts. Two local plugins handle synchronized output and tmux status bar alignment.

Inside Tabby, `kael-tmux` automatically uses a dedicated Sixel socket. To start a regular session, run `KAEL_TMUX_MODE=plain kael-tmux` from outside tmux. Set `KAEL_TMUX_BIN` to point to an existing compatible build.

### Codex CLI

Sign in on first use with `codex login` or your organization's sign-in method. Run `codex` from the project directory. As a first prompt, try “Explain how this repository installs its configuration and point me to the main entry points.”

The Ada status line shows the model, Git changes, and remaining weekly quota and context when available. Interactive sessions support image previews in Tabby and compatible Sixel tmux sessions.

## Customize and roll back

- **Personal Zsh settings** go in `${XDG_CONFIG_HOME:-$HOME/.config}/kael-terminal/local.zsh`. The installer maintains a loader block in `.zshrc`.
- **Application configuration** lives in [`config/`](config/). Edit files there and rerun the relevant `./install.sh` command. Vim uses `~/.vimrc`, and an existing Neovim installation can use the bundled [`init.vim`](config/vim/init.vim).
- **Deployment backups** live in `${XDG_STATE_HOME:-$HOME/.local/state}/kael-terminal/backups/` and include any replaced Codex and Tabby configs. Credentials, task databases, shell history, and runtime caches are stored per device.

```sh
./install.sh rollback --dry-run
./install.sh rollback
```

Rollback restores files and symlinks from the latest configuration deployment. Installed packages remain available. Rollback stops if a deployed file was edited afterward. Save any edits you want to keep before using `./install.sh rollback --force` to restore the backup.

### Repository entry points

- [`bootstrap.sh`](bootstrap.sh) installs dependencies and tools. [`install.sh`](install.sh) applies, checks, or rolls back configuration.
- [`libexec/releases.tsv`](libexec/releases.tsv) lists pinned downloads and SHA-256 checksums.
- [`vendor/tmux/`](vendor/tmux/) contains the source snapshot, patch, and build instructions for the customized tmux.
- [`git-local`](git-local) runs Git from the project directory, for example `./git-local status --short`.

## License

The project's original code and configuration are released under the [MIT License](LICENSE). Bundled third-party materials are subject to their respective terms. See the [tmux license](vendor/tmux/COPYING), the [SauceCodePro Nerd Font license](fonts/SauceCodeProNF/LICENSE.txt), and the [Starship icon sources](config/starship/icon-sources.json).
