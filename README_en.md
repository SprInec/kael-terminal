# kael-terminel

[简体中文](README.md) · **English**

A reusable terminal setup for Linux. Set up Zsh, Starship, a customized tmux build, and everyday CLI tools on a workstation or a server. The desktop setup adds Tabby and its plugins.

## What’s included

| Component | Configuration and integration |
| --- | --- |
| **Zsh · Starship** | A prompt with Git remote icons and custom glyphs, plus completions, history suggestions, syntax highlighting, and optional Conda initialization. |
| **tmux** | Separate pane borders, a focus glow, transfer progress on pane borders, floating pane menus, and a status bar with Git and system metrics. |
| **Tabby · Codex CLI** | Tabby colors, fonts, shortcuts, and two local plugins. Codex gets the Ada status line and Sixel image previews in Tabby and compatible tmux sessions. |
| **Yazi · Vim · fzf · zoxide** | Return from Yazi to the directory you browsed to in Zsh, with Vim for editing, fuzzy search, and quick directory jumps. |
| **eza · dust · btop · bat · Glow** | File listings and trees, disk usage, resource monitoring, syntax highlighting, and Markdown rendering. |
| **Dooit · Atuin** | A Dooit theme, task notes, and copy-on-selection, plus Atuin history with automatic sync disabled by default. |

## Quick start

The installer targets APT-based Ubuntu and Debian systems. The download manifest covers **x86_64** and **aarch64**. Start with Git, Bash, and Python 3.10 or newer. A full install needs access to your APT repositories, GitHub, Node.js, npm, and PyPI, and uses `sudo` for system packages. For a desktop install, close any running Tabby windows first.

```sh
git clone https://github.com/SprInec/kael-terminel.git
cd kael-terminel
./bootstrap.sh --dry-run
./bootstrap.sh
exec zsh -l
```

The dry run lists dependencies and the files that would change. A full run verifies checksums for pinned releases, builds the customized tmux, and applies the configuration for the current user. The default desktop mode also installs Tabby, plugins, and fonts. On first use, sign in with `codex login` or your organization’s sign-in method.

| Use case | Command |
| --- | --- |
| Headless server | `./bootstrap.sh --headless` |
| System dependencies are already installed | `./bootstrap.sh --skip-apt` |
| Apply configs to tools you already have | `./install.sh` or `./install.sh --headless` |
| Check available tools and plugins | `./install.sh doctor` or `./install.sh doctor --headless` |

You can combine `--skip-apt` with `--headless`. Install Tabby first if you skip APT in desktop mode. A configuration-only install links the two bundled Tabby plugins. The full bootstrap also installs the third-party npm plugins.

## Customize and roll back

- **Local Zsh settings** go in `${XDG_CONFIG_HOME:-$HOME/.config}/kael-terminal/local.zsh`. The installer maintains a loader block in `.zshrc`.
- **tmux** starts through `kael-tmux` when the custom build is available. Tabby uses a dedicated Sixel socket by default. Run `KAEL_TMUX_MODE=plain kael-tmux` for a regular session or set `KAEL_TMUX_BIN` to use an existing compatible build.
- **Configuration backups** are stored under `${XDG_STATE_HOME:-$HOME/.local/state}/kael-terminal/backups/`. Deploying the Codex and Tabby configs saves their previous active configs there. Login credentials, task databases, shell history, and runtime caches stay on each device.

```sh
./install.sh rollback --dry-run
./install.sh rollback
```

Rollback restores files and symlinks from the most recent configuration deployment. Installed packages remain available. If a deployed file was edited afterward, rollback stops. Save any edits you want to keep before running `./install.sh rollback --force` to restore the previous version.

## Repository layout and credits

- [`config/`](config/) contains application settings, local plugins, and status scripts.
- [`libexec/releases.tsv`](libexec/releases.tsv) records upstream release URLs and SHA-256 checksums.
- [`vendor/tmux/`](vendor/tmux/) contains the buildable source snapshot, the patch, and the [tmux license](vendor/tmux/COPYING).
- [`fonts/`](fonts/) contains the terminal fonts. See the [SauceCodePro Nerd Font license](fonts/SauceCodeProNF/LICENSE.txt) and [Starship icon sources](config/starship/icon-sources.json).
