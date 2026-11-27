<div align="center">

# kael-terminal

[简体中文](README.md) · **English**

[![MIT license](https://img.shields.io/badge/License-MIT-26734D?style=flat-square)](LICENSE)
[![Ubuntu and Debian support](https://img.shields.io/badge/Linux-Ubuntu%20%2B%20Debian-355E8D?style=flat-square)](#system-requirements)
[![x86_64 and aarch64 support](https://img.shields.io/badge/Arch-x86__64%20%2B%20aarch64-635B9A?style=flat-square)](#system-requirements)

A terminal workspace for Ubuntu and Debian. Navigate projects with Zsh and Starship, keep work running in a customized tmux session, and browse files, edit code, and review commits with Yazi, Vim, Neovim, and Gitoui. Desktop setup includes Tabby, Sixel image rendering, and matching fonts. Headless setup is available for servers.

[Installation](#installation) · [Shell and navigation](#shell-and-navigation) · [Finding and reading files](#finding-and-reading-files) · [tmux sessions](#tmux-sessions) · [Tabby desktop terminal](#tabby-desktop-terminal) · [Editors](#editors) · [Git and Gitoui](#git-and-gitoui) · [Codex CLI](#codex-cli) · [Tasks and notes](#tasks-and-notes) · [System tools and runtimes](#system-tools-and-runtimes) · [Configuration and maintenance](#configuration-and-maintenance)

</div>

## Installation

### System requirements

| Item | Requirement |
| --- | --- |
| OS and architecture | Ubuntu or Debian with APT, on `x86_64` or `aarch64` |
| Installer | Git, Bash, and Python 3.10 or later. Run as your regular user. The script calls `sudo` for system package installation |
| Network | Full installation needs access to APT repositories, GitHub, Node.js downloads, npm, and PyPI |
| Desktop environment | The default installer sets up Tabby and fonts. Quit Tabby before deployment |
| Optional components | Install Neovim and the Tree-sitter CLI separately. Gitoui and Tudo have standalone Rust build scripts. Conda integration uses an existing `~/anaconda3` installation |

### First installation

Run these commands in a terminal. Review the preview, then run the installation command for your environment.

```sh
git clone https://github.com/SprInec/kael-terminal.git
cd kael-terminal
./bootstrap.sh --dry-run
./bootstrap.sh
./install.sh doctor
exec zsh -l
```

On an SSH host or a system without a desktop, preview with `./bootstrap.sh --headless --dry-run`, then run `./bootstrap.sh --headless` and `./install.sh doctor --headless`. In the new Zsh session, run `kael-tmux new-session -A -s dev` to open your first named session. The examples below use paths relative to the repository root.

| Scenario | Command | Result |
| --- | --- | --- |
| Full desktop installation | `./bootstrap.sh` | Installs system dependencies, pinned tools, Tabby, and plugins, builds tmux, and deploys configuration and fonts |
| Headless installation | `./bootstrap.sh --headless` | Installs command-line tools and deploys configuration, skipping Tabby, desktop fonts, and the Yazi glyph plugin |
| System dependencies already installed | `./bootstrap.sh --skip-apt` | Skips APT and continues with downloads, builds, and deployment. Desktop mode requires `tabby` on your PATH |
| Configuration only | `./install.sh` or `./install.sh --headless` | Deploys configuration. Desktop mode deploys the local Tabby plugins. The full installer supplies third-party npm plugins |
| Check installation | `./install.sh doctor` or `./install.sh doctor --headless` | Reports the locations of the main executables and checks the custom tmux build and applicable Tabby plugins |

Use `--dry-run` to preview installation or configuration deployment. Deployment backs up user files and links it replaces, including existing Codex and Tabby configuration. To prepare the APT dependencies manually, run the preview without `--skip-apt` to see the package list. After desktop installation, launch `tabby`. Its default local profile opens a Zsh login shell.

### Component versions

These versions come from the repository's installation manifests. System repositories supply the APT package versions.

| Source | Components |
| --- | --- |
| Pinned downloads | Starship 1.26.0, Yazi and `ya` 26.9.1, zoxide 0.10.0, fzf 0.75.0, eza 0.23.5, dust 1.2.6, btop 1.4.8, Atuin 18.24.3, bat 0.26.1, Glow 3.0.0, Node.js 22.23.5 with npm |
| npm and Python virtual environment | Codex CLI 0.171.0, Dooit 3.3.4, Dooit Extras 0.2.1, Textual 8.2.8, Rich 15.0.0, SQLAlchemy 2.0.55 |
| Local build | tmux built from the bundled independent-borders source snapshot and Kael patch |
| Desktop components | Tabby 1.0.238, four pinned npm plugins, two local plugins, and two bundled font families |
| Optional builds | Gitoui 0.5.0 and Tudo 1.1.0 |

The installer checks the SHA-256 of download archives. See the [download manifest](libexec/releases.tsv), [Python requirements](libexec/dooit-requirements.txt), and [Tabby plugin lockfile](config/tabby/plugins/package-lock.json).

## Shell and navigation

Zsh loads Kael's tool directory, completions, and history settings in interactive sessions. Starship shows the host, time, current directory, Git information, and modules for the current project's languages or tools. It reads local Git configuration to identify the current branch's GitHub or GitLab upstream. Open a checked-out project to try these commands and shortcuts. [Zsh configuration](config/zsh/terminal-tools.zsh) · [Starship configuration](config/starship/starship.toml) · [Git host helper](config/starship/git-host.py)

| Tool or plugin | How to use it | Kael settings |
| --- | --- | --- |
| Zsh completion | Type `cd conf`, press `Tab`, and select a path from the menu | Enables `compinit` and menu selection |
| zsh-autosuggestions | Type the start of a command from your history and press `→` to accept the suggestion | Loads the APT-installed plugin |
| zsh-syntax-highlighting | Watch the colors as you type to identify quotes, flags, and command names | Loads after the other line editor plugins |
| Starship | Run `starship explain` to see the modules in the current prompt. Use `git branch -vv` to see tracking branches | Uses custom glyphs, Git status, and provider icons |
| Atuin | Press `Ctrl+R` and enter a search term. Press `Tab` to edit the selected command or `Enter` to run it | Saves history locally with automatic sync disabled. Use `atuin search 'git'` to search from the command line |
| fzf | Press `Ctrl+T` to insert a path, or run `rg --files config \| fzf` to pick a file from a list | Atuin handles `Ctrl+R`. The fzf `Alt+C` binding is disabled |
| zoxide | Visit a project with `cd`, then use `z kael-terminal` to jump back. Run `zi kael` to choose a match or `zoxide query -l` to list recorded directories | Initializes with Zsh and tracks directory visits |

[Atuin usage guide](https://docs.atuin.sh/latest/guide/basic-usage/) · [Atuin configuration](config/atuin/config.toml)

## Finding and reading files

### Yazi file manager

In Zsh, run `y config`. Press `→` to enter the selected directory and `←` to go back up. Browse to your destination and press `q` to exit and change the shell to that directory. Press uppercase `Q` to exit and stay in your starting directory.

| Action | Key or command |
| --- | --- |
| Show help | `F1` or `~` |
| Open selected files | `Enter`. Use `O` to choose an opener. The edit action uses `VISUAL`, `EDITOR`, or Vim |
| Search filenames or contents | `s` calls fd and `S` calls ripgrep |
| Show hidden items and select files | `.` toggles hidden items and `Space` toggles selection of the current item |
| Copy, cut, and paste | `y`, `x`, and `p` |
| Create or rename | `a` creates a file. End the name with `/` to make a directory. Use `r` to rename |
| Manage upstream plugins | `ya pkg list` lists packages and `ya pkg --help` shows management commands |

The Kael theme uses tmux's green palette. `init.lua` styles directories and loads glyph aliases from `kael-yazi-icons`. Desktop deployment installs the plugin with the matching fonts. Headless mode uses Yazi's original glyphs. [Openers, theme, and local plugin](config/yazi/) · [Yazi key guide](https://yazi-rs.github.io/docs/quick-start/)

### Command reference

| Tool | Example | Purpose |
| --- | --- | --- |
| ls | `ll`, `la`, `l` | Show details, hidden items, or a columnar listing |
| eza | `lt`, `lgit`, `eza -al --git config` | View a two-level tree or a listing with Git status |
| tree | `tree -L 2 config` | Print a directory structure that is easy to copy or compare |
| fd / fdfind | `fd -e toml . config` | Find paths by name or extension. The installer exposes APT's `fdfind` as `fd` |
| ripgrep | `rg -n -g '*.toml' 'theme' config` | Search file contents by file type and display line numbers |
| bat | `bat --style=numbers bootstrap.sh` | Read syntax-highlighted text with line numbers. Press `q` if the pager is active |
| Glow | `glow README_en.md`, `glow -t .`, `glow -p README_en.md` | Render a Markdown file, browse a directory in the TUI, or read with a pager |
| jq | `jq '.dependencies \| keys' config/tabby/plugins/package.json` | Query JSON fields. This example lists the Tabby plugins |
| file | `file fonts/StarshipPromptIcons/StarshipPromptIcons-Regular.ttf` | Identify a file type |
| Chafa | `chafa --format=symbols /path/to/image.png` | Preview an image using terminal characters. Substitute a real path. The desktop installer supplies Chafa through APT |

Glow uses automatic styling and wraps at 80 columns. Its TUI has mouse support and direct output has paging disabled by default. Run `glow config` to edit the user configuration. [Glow configuration](config/glow/glow.yml)

## tmux sessions

tmux manages windows and panes in a single terminal. Processes can keep running after you detach or close the client. `kael-tmux` starts the project build, reads the independent-borders configuration, and selects a socket based on the client. Run the first command from outside tmux.

```sh
kael-tmux new-session -A -s dev
kael-tmux list-sessions
kael-tmux attach-session -t dev
```

The first command creates or attaches to `dev`. Detach with `Ctrl+B`, then `d`. Use the remaining commands to list and resume sessions. Running `kael-tmux` without arguments outside tmux creates or attaches to `work`. Inside a Kael session, the launcher uses the current socket, so `kael-tmux list-windows` and `kael-tmux list-panes` operate on the active server.

| Press after `Ctrl+B` | Action |
| --- | --- |
| `c`, `n`, or `p` | Create a window, or switch to the next or previous one |
| `%` or `"` | Split to the right or below |
| Arrow keys | Switch panes |
| `z` | Zoom the current pane. Press again to restore the layout |
| Uppercase `F` | Toggle the current pane between floating and tiled |
| `[` | Enter copy mode. Scroll through history and press `q` to leave copy mode |
| `d` | Detach |
| `?` | Show the active key bindings |

### Pane borders, status line, and Sixel

- The active pane has a colored border and a moving focus glow. The highlight turns pink when an interactive SSH, ADB Shell, Mosh, or Dropbear session is detected. The border displays transfer progress when recognized. Right-click a pane to split, swap, mark, or move and resize floating panes.
- The bottom status line shows the session, windows, prefix state, and current path. It reads local Git status, CPU, memory, disk, hostname, and time, with a shorter layout for narrow terminals. It displays a Codex or Claude icon when it recognizes the foreground process.
- Plain mode uses `kael-borders`. Sixel mode uses `kael-borders-sixel` and is selected automatically inside Tabby. From outside tmux, run `KAEL_TMUX_MODE=plain kael-tmux new-session -A -s dev` to select plain mode, or `KAEL_TMUX_MODE=sixel kael-tmux new-session -A -s dev` from a Sixel-capable client. Use the same mode to find the session again.

Inside a session, run these commands to check image support and inspect the current panes. For a Sixel-capable client, the first command should report `1` and include `sixel` in the feature list.

```sh
kael-tmux display-message -p '#{sixel_support} #{client_termfeatures}'
kael-tmux list-panes -F '#{pane_index} #{pane_title} #{pane_current_command}'
```

The base configuration enables the mouse, focus events, and a blinking underline cursor. The independent-borders configuration defines the floating-pane menu and the progress and glow settings. `status.conf` defines the status layout, and `status.py` collects its data. To disable the glow in the current window, run `kael-tmux set-window-option @pane-border-glow off`. [tmux configuration](config/tmux/) · [Custom source and patch guide](vendor/tmux/README.md)

Bootstrap builds tmux automatically. With system build dependencies installed, you can also rebuild it separately. Set `KAEL_BUILD_JOBS` to control the number of parallel jobs.

```sh
./vendor/tmux/build.sh "${XDG_DATA_HOME:-$HOME/.local/share}/kael-terminal/bin/tmux"
kael-tmux -V
```

## Tabby desktop terminal

Run `tabby` to open the default `/usr/bin/zsh -l` profile. It uses xterm Canvas, automatic light and dark schemes, an underline cursor, and Sixel. The Kael font supplies color icons and glyphs used by tmux, Yazi, and Neovim. Liberation Mono renders ordinary characters when needed. Press `Ctrl+,` to open Settings. [Tabby configuration](config/tabby/config.yaml)

| Key | Action |
| --- | --- |
| `Ctrl+Shift+T` / `Ctrl+Shift+W` | Open or close a tab |
| `Ctrl+Tab` / `Ctrl+Shift+Tab` | Switch to the next or previous tab |
| `Alt+1` through `Alt+0` | Select tabs 1 through 10 |
| `Ctrl+Shift+C` / `Ctrl+Shift+V` | Copy or paste |
| `Ctrl+F` / `Ctrl+Shift+P` | Search terminal output or open the command selector |
| `Ctrl+D`, `Ctrl+S`, `Ctrl+A`, `Ctrl+W` | Split the Tabby pane right, down, left, or up |
| `Alt+W`, `Alt+A`, `Alt+S`, `Alt+D` | Move focus among Tabby panes |
| `Ctrl+Alt+Enter` | Maximize or restore the current Tabby pane |

### Tabby plugins

Desktop Bootstrap installs the plugins below. Verify them under **Settings → Plugins**. Terminal decorators load with the tab. Restart Tabby after changing which plugins are enabled.

| Plugin | Purpose | How to use it |
| --- | --- | --- |
| `tabby-background` 2.2.4 | Background images and UI font | Add a background in the plugin settings. The repository starts with an empty background list and selects SauceCodePro Nerd Font for the UI |
| `tabby-highlight` 3.0.0 | Keyword highlighting and text replacement | Review the highlight and replacement profiles in Settings. Test the output with `printf '%s\n' 'ERROR WARN INFO' '错误 警告 信息'` and select or adjust the profiles as needed |
| `tabby-sftp-plus` 3.2.1 | Dual-pane file management, uploads, downloads, bookmarks, and transfer logs in SSH tabs | The supplied configuration disables `sftp-plus`. Enable it, restart Tabby, connect over SSH, and open **SFTP+** from the tab toolbar |
| `tabby-windy-quick-commands` 2.1.4 | Save, find, and send reusable commands | Open the drawer with `Ctrl+P`. Try saving `git status --short` and sending it to the active terminal. Use `Ctrl+Alt+H` for shortcut hints |
| `tabby-sync-output` 1.0.0 | Batches DEC 2026 synchronized output to reduce cursor flicker during tmux redraws | Applies automatically. Run `kael-tmux` and switch panes to see it in use |
| `tabby-tmux-capsule-alignment` 1.0.0 | Positions Canvas underlines and renders status backgrounds, compact borders, and thin lines | Applies automatically. Start `kael-tmux` in Tabby and split a pane to see the status line and borders |

The local plugin sources include the synchronized output adapter and frame buffer, plus Canvas modules for underlines, the status line, pane borders, and thin lines. `quick-cmds` is disabled, and Windy provides quick commands. The configuration also includes shortcuts for separately installed plugins. In AgentDeck, `Ctrl+L` focuses the list. With a compatible `tmuxPlugin`, use `Ctrl+Shift+[` or `Ctrl+Shift+]` to change windows. [Plugin manifest and local sources](config/tabby/plugins/) · [SFTP+ guide](https://github.com/10D24D/Tabby-SFTP-Plus/blob/main/README.en.md) · [Windy Quick Commands guide](https://github.com/windyy0/tabby-windy-quick-commands/blob/main/README.en.md)

## Editors

### Vim

Run `vim README_en.md` to open a file. The configuration enables line numbers, syntax highlighting, filetype indentation, incremental search, and smart case. Press `i` to edit, `Esc` to return to Normal mode, and enter `:wq` to save and quit. Enter `/tmux` to search and press `n` to repeat the search forward. Use `:q!` to discard unsaved edits and quit. [Vim configuration](config/vim/vimrc)

### Neovim and LazyVim

Put **Neovim 0.12+** with LuaJIT and **Tree-sitter CLI 0.26.1+** on your PATH. Initial plugin installation needs access to GitHub, and building parsers requires a C compiler.

```sh
nvim --version
tree-sitter --version
nvim .
```

In Neovim, run `:Lazy` to see plugin status, `:checkhealth` to inspect dependencies, and `:Mason` to see language tools. Run `:Lazy restore` to use the lockfile's versions. The project enables C/C++, Python, and mini.surround extras. It reuses `clangd`, `pyright-langserver`, `lua-language-server`, and `ruff` when available. Mason supplies missing tools. C/C++, Lua, and Python formatting use clang-format, StyLua, and Ruff respectively.

| Key or command | Action |
| --- | --- |
| `Space e` | Open the file tree at the project root |
| `Space Space` / `Space s g` | Find a file by name or search project contents |
| `gd` / `K` | Go to definition or show hover information with a language server attached |
| `Space c f` | Format the current file or selection |
| `Space g g` / `Space g G` | Open Gitoui from the Git root or the current working directory. Requires `gitoui` |
| `Space`, then pause | Show Which-key hints |

Kael customizes the Catppuccin Mocha palette and the glyphs and spacing in Lualine, Snacks, Blink, Which-key, and Bufferline. Existing custom LazyVim setups receive the status line extension, glyph manifest, and Gitoui shortcuts. When an older Neovim starts through Kael's entry point, it uses `~/.vimrc`. A previously managed `init.vim` loads the Lua configuration through `kael-init.vim`. [Neovim configuration and lockfile](config/nvim/) · [Vim entry points](config/vim/) · [LazyVim key maps](https://www.lazyvim.org/keymaps)

| Configuration file | Purpose |
| --- | --- |
| `init.lua` and `lua/config/lazy.lua` | Check the Neovim version, then install and load lazy.nvim, LazyVim, and extras |
| `lua/config/options.lua` | Enables automatic formatting, hides the idle command line, and adds an existing Mason binary directory to `PATH` |
| `lua/plugins/appearance.lua` and `editor.lua` | Configure the theme, cursor animation, language servers, and formatters |
| `lua/plugins/kael-statusline.lua` and `lua/kael/statusline-icons.json` | Customize icon sizes and spacing and provide filetype glyphs for the status line and pickers |
| `lua/plugins/gitoui.lua` and `lazy-lock.json` | Define the Gitoui launcher and shortcuts, and record plugin versions |

### LazyVim plugin reference

This table covers the direct entries in the [plugin lockfile](config/nvim/lazy-lock.json). Press `Space` sequences one key at a time in Normal mode. Language features depend on the current filetype and available tools.

| Plugin | Purpose | How to use it |
| --- | --- | --- |
| LazyVim | Editor defaults and language extras | Run `:LazyExtras` to view extras |
| lazy.nvim | Loads plugins and manages their versions | Use `:Lazy` to inspect plugins and `:Lazy restore` to match the lockfile |
| snacks.nvim | Dashboard, file tree, pickers, terminal, and utilities | Press `Space e` for the file tree or `Space s g` to search text |
| lualine.nvim | Mode, file, Git, and other status information | Read the bottom status line. Kael adds filetype glyphs and a clock |
| bufferline.nvim | Displays buffer tabs | Press `[b` or `]b` to switch buffers |
| catppuccin | Active Mocha theme | Run `:colorscheme catppuccin-mocha` |
| tokyonight.nvim | Alternate theme and an initial setup option | Run `:colorscheme tokyonight` |
| smear-cursor.nvim | Animates cursor movement | Move the cursor in Normal mode |
| which-key.nvim | Displays multi-key command hints | Press `Space` and pause |
| noice.nvim | Command-line UI and message history | Run `:Noice history` |
| nui.nvim | Popup components used by Noice and other plugins | See it in Noice's command line or popups |
| plenary.nvim | Shared Lua utility library | Inspect its installation in `:Lazy` |
| mini.icons | Icons for files, directories, and filetypes | See them in the file tree and file pickers |
| blink.cmp | Insert-mode completion | Type code to see suggestions or press `Ctrl+Space` to trigger completion |
| friendly-snippets | Filetype-specific snippets | Select a snippet in the completion menu |
| mini.ai | Extends Vim text objects | Use `viq` to select inside the nearest quotes |
| mini.pairs | Inserts matching brackets and quotes | Type `(` in Insert mode to see the matching `)` |
| mini.surround | Adds, removes, or replaces delimiters | Type `gsaiw"` to wrap a word in double quotes |
| ts-comments.nvim | Chooses comment syntax based on context | Use `gcc` to toggle a line comment |
| flash.nvim | Jumps to a match on screen | Press `s`, type the target, then press a hint letter |
| grug-far.nvim | Project search and replace | Press `Space s r` and review the matches before replacing |
| gitsigns.nvim | Marks Git changes in the gutter | Use `]h` and `[h` to jump to the next or previous hunk |
| trouble.nvim | Presents diagnostics and other lists | Press `Space x x` to open diagnostics |
| todo-comments.nvim | Highlights and finds TODO and FIXME comments | Press `Space s t` to open the TODO picker |
| persistence.nvim | Saves and restores editing sessions | Press `Space q s` to restore the current directory's session |
| nvim-treesitter | Parses syntax trees | Run `:TSInstall lua` to install the Lua parser |
| nvim-treesitter-textobjects | Uses syntax trees to navigate code structures | With a parser installed, press `]f` to jump to the start of the next function |
| nvim-ts-autotag | Closes tags and keeps tag names in sync | Type `<div>` in a supported filetype to see the closing tag |
| nvim-lspconfig | Configures language servers | Open a source file and run `:checkhealth vim.lsp` |
| mason.nvim | Manages language tools | Run `:Mason` to see tools and installation status |
| mason-lspconfig.nvim | Connects Mason-installed language servers to Neovim | Check the server in `:Mason`, then confirm attachment through LSP health checks |
| clangd_extensions.nvim | Adds clangd features | With clangd attached, run `:ClangdSwitchSourceHeader` to switch between source and header files |
| lazydev.nvim | Supplies Neovim API type information for Lua | Type `vim.api.` in a Lua configuration to see completion |
| venv-selector.nvim | Switches Python virtual environments | Open a Python file and run `:VenvSelect` |
| conform.nvim | Runs formatters | Use `:ConformInfo` to see the formatters for the current file |
| nvim-lint | Runs external linters and reports diagnostics | Edit a supported file and press `Space c d` to inspect line diagnostics |

## Git and Gitoui

### Git workflow

Run these commands from the repository root to inspect the worktree, unstaged changes, staged changes, and commit history. `git-local` always runs Git from the Kael repository and supports an existing `.git-kael` metadata directory.

```sh
git status --short
git diff
git diff --cached
git log --oneline --graph --decorate -15
./git-local status --short
```

After editing, use `git add -- README.md README_en.md` to stage the two manuals, review the staged changes with `git diff --cached`, and save the commit with `git commit -m "docs: update the manual"`. Choose the files that belong to your change. [Repository Git entry point](git-local)

### Install and use Gitoui

Gitoui is a Git TUI for browsing branches and commit graphs, comparing changes, and resolving conflicts. The configuration selects the `kael-tmux` theme, automatic graph rendering, enhanced side-by-side diffs, and a three-pane conflict view. Install Rust and Cargo **1.88+**, then run these commands from the repository root.

```sh
./vendor/gitoui/build.sh
gitoui --version
gitoui --graph-renderer ascii -n 100
```

The build installs to `${XDG_DATA_HOME:-$HOME/.local/share}/kael-terminal/bin/gitoui`. In a Sixel-capable client, run `gitoui --graph-renderer sixel`. The LazyVim shortcuts open a separate window in a compatible Sixel tmux session. Other sessions use a Snacks terminal with a text graph.

| Task | Action |
| --- | --- |
| Review a commit | Select a commit with the arrow keys and press `Enter`. Select a file and press `Enter` again to see its diff |
| Browse branches and search commits | Press `Tab` for the references panel or `f` to search |
| Inspect and stage changes | Press `Enter` on the top row for uncommitted changes. Use the arrow keys to browse, `a` to stage a file, and `u` to unstage it from the Staged panel |
| Write a commit message | Review staged files, then press `w` to open the message editor and `Ctrl+Enter` or `Ctrl+S` to commit |
| Get help or go back | Press `?` for active shortcuts, `Esc` to go back, and `q` to quit from the main view |

The build checks the Gitoui 0.5.0 archive, uses locked Cargo dependencies, and applies four patches. `sixel-node-aspect` adjusts node proportions, `tabby-sixel-and-smooth-graph` adjusts Sixel sizing and smooth edges for Tabby, `terminal-graph-antialiasing` smooths drawing edges, and `compact-footer` shortens the footer. [Gitoui configuration](config/gitoui/) · [Build script and patches](vendor/gitoui/)

## Codex CLI

Codex CLI works on coding tasks in the current directory. Sign in on first use and start a session in the repository.

```sh
codex --version
codex login
codex login status
codex
```

Try “List this repository's installation entry points and explain how desktop and headless installation differ.” Later, run `codex resume` to choose a saved session or `codex resume --last` to continue the most recent session for the current directory. To attach a local image, run `codex -i /path/to/image.png` with the actual path.

| Integration | Purpose and usage |
| --- | --- |
| Codex configuration | Deploys to `${CODEX_HOME:-$HOME/.codex}/config.toml`. It selects the Ada theme, `gpt-6.2-sol`, and `xhigh` reasoning. Model availability depends on the signed-in account |
| Ada status line provider | A Python MCP provider displays model and reasoning details, available weekly quota and context, and Git changes. Open an interactive session in a repository to see it |
| Tabby image preview | The Zsh wrapper enables full-screen previews in local Tabby tabs and compatible Sixel tmux panes. Run `command codex` to invoke the CLI directly, or use `codex --no-alt-screen` to keep terminal scrollback |

[Codex configuration, status line, and preview wrapper](config/codex/)

## Tasks and notes

### Dooit

Run `dooit` to open its workspaces and tasks. Dooit supports tasks, subtasks, due dates, and recurrence. Kael adds mode, clock, and workspace indicators with colors that react to tmux focus. Task remarks are stored in the local task database.

| Key | Action |
| --- | --- |
| `a` / `c` | Add a sibling task or toggle completion in the task list |
| `n` | Edit the current task's multiline remark. Press `Esc` to save and return |
| `Enter` or `Ctrl+M` | Toggle the remark panel from the task list |
| `Ctrl+N` | Toggle the workspace list through Dooit Extras |
| Mouse drag / `Ctrl+C` | Drag and release to copy a selection. `Ctrl+C` copies a selection or quits when there is no selection |
| `?` / `Ctrl+Q` | View the active key bindings or quit |

`config.py` defines colors, the status bar, and subtask markers. `task_notes.py` supplies the remarks panel, and `text_selection.py` handles copying. Bootstrap installs Dooit and Dooit Extras in a dedicated virtual environment with pinned versions of Textual for the UI, Rich for text rendering, and SQLAlchemy for storage. [Dooit configuration and extensions](config/dooit/) · [Dependency versions](libexec/dooit-requirements.txt) · [Dooit usage guide](https://dooit-org.github.io/dooit/getting_started/basics.html)

### Tudo

Tudo provides multiple task lists and a separate Markdown notebook. Use Rust and Cargo **1.95+** to build Kael's version. Choose a local data directory on first launch.

```sh
./vendor/tudo/build.sh
tudo --version
TUDO_THEME=kael-tmux tudo
```

| Key | Action |
| --- | --- |
| `1` / `2` | Switch between the Tasks and Notes tabs |
| `Tab` and arrow keys | Switch panes and select items |
| `a` and `Space` | Add a task or toggle completion in the Tasks tab |
| `n` and `Ctrl+S` | Edit and save a task remark. In Notes, press `Enter` to edit the selected note |
| `/` | Search items |
| `T` and `S` | Choose a theme or view application settings and data paths |
| `?` and `q` | Show help for the active tab or quit |

The build checks the Tudo 1.1.0 source archive and installs to `~/.local/bin/tudo`. `kael-tmux-theme.patch` adds a palette to the theme picker. `input-cursor.patch` improves cursor placement in single-line, multiline, and wide-character input. Tudo stores lists as JSON and notes as Markdown. Press `S` to find the configuration and storage paths. [Build script and patches](vendor/tudo/) · [Tudo usage guide](https://github.com/jolleyDesign/tudo)

## System tools and runtimes

| Tool | Example | Purpose |
| --- | --- | --- |
| btop | Run `btop`, press `Esc` for the menu, and `q` to quit | Monitor CPU, memory, network, disks, and processes. Kael enables the mouse, process tree, synchronized updates, and a two-second refresh interval |
| dust | `dust -d 2 .` | Rank disk usage in the current directory and locate large paths |
| Node.js / npm | `node --version`, `npm --version` | JavaScript runtime and package manager. Bootstrap installs Codex with npm and restores Tabby plugin dependencies with `npm ci` |
| Python / venv | `python3 --version`, `python3 -m venv /tmp/kael-example-venv` | Runs deployment, status line, and glyph scripts. Virtual environments isolate dependencies for tools like Dooit |
| Conda | `conda env list`, `conda activate base`, `conda deactivate` | Manage an existing Anaconda setup. Zsh initializes it if `~/anaconda3/bin/conda` is available |
| Fontconfig | `fc-match 'Kael Starship Prompt Icons'`, `fc-cache -f` | Check what font will be used and refresh the font cache |
| Xclip / wl-clipboard | `xclip -selection clipboard -o`, `wl-paste` | Read the clipboard on X11 or Wayland. Supplied by desktop installation |
| ncurses / terminfo | `tic -V`, `infocmp xterm-256color` | Inspect terminal capabilities. The Codex preview wrapper uses `tic` to compile a temporary entry |

System dependencies also include APT, CA certificates and curl, tar/unzip/xz, checksum utilities, a C compiler, Autoconf, Automake, Bison, pkg-config, patch, and the development packages for libevent, ncurses, zlib, and libpng. Check the environment with `cc --version`, `pkg-config --modversion libevent`, or `./bootstrap.sh --dry-run`. [btop configuration](config/btop/btop.conf) · [System dependency list](bootstrap.sh)

## Configuration and maintenance

### Configuration locations

The table uses default paths. Deployment recognizes `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_STATE_HOME`, and `XDG_CACHE_HOME`. The Zsh entry point follows `ZDOTDIR`, Codex and Tabby can use `CODEX_HOME` and `TABBY_CONFIG_DIRECTORY`, and the Atuin path uses `ATUIN_CONFIG_DIR` before `ATUIN_HOME`.

| Component | Repository source | Default deployment location |
| --- | --- | --- |
| Zsh | [config/zsh/](config/zsh/) | `~/.zshrc` sources `~/.config/kael-terminal/terminal-tools.zsh`. Put personal settings in `local.zsh` beside it |
| Starship / Atuin | [starship](config/starship/) · [atuin](config/atuin/) | `~/.config/starship.toml`, `~/.config/starship/git-host.py`, `~/.atuin/config.toml` |
| tmux | [config/tmux/](config/tmux/) · [Launcher](bin/kael-tmux) | `~/.tmux.conf`, `~/.config/tmux/`, `~/.local/share/kael-terminal/bin/kael-tmux` |
| Tabby | [config/tabby/](config/tabby/) | `~/.config/tabby/config.yaml` and `~/.config/tabby/plugins/`, including plugin links |
| Vim / Neovim | [vim](config/vim/) · [nvim](config/nvim/) | `~/.vimrc`, `~/.config/nvim/` |
| Yazi / Glow / btop | [yazi](config/yazi/) · [glow](config/glow/) · [btop](config/btop/) | Each application's directory under `~/.config/` |
| Codex | [config/codex/](config/codex/) | `~/.codex/config.toml`, `~/.codex/statusline/ada-usage-statusline/statusline.py`, `~/.local/share/kael-terminal/codex-tabby-preview.py` |
| Dooit / Gitoui | [dooit](config/dooit/) · [gitoui](config/gitoui/) | `~/.config/dooit/`, `~/.config/gitoui/` |
| Fonts | [fonts/](fonts/) | `~/.local/share/fonts/kael-terminal/`, populated by desktop deployment |
| Installation and backups | [bootstrap.sh](bootstrap.sh) · [install.sh](install.sh) · [deploy.py](libexec/deploy.py) | `~/.local/share/kael-terminal/{bin,opt}`, `~/.cache/kael-terminal/downloads/`, `~/.local/state/kael-terminal/backups/` |

### Fonts and glyph generation

Desktop deployment ships ready-to-use fonts. **Kael Starship Prompt Icons** includes tool logos, monochrome warning and lightning glyphs, and symbols for tmux, Yazi, and Neovim. **SauceCodePro Nerd Font Mono** supplies regular and bold monospace glyphs and serves as a source for glyph scripts. **Liberation Mono** is Tabby's fallback for ordinary text.

To change glyphs, use Python 3.11 or later and install the dependency in a virtual environment with `python -m pip install fonttools`. For generators that modify repository fonts, check the results with `git status --short`, redeploy the fonts, and relaunch Tabby.

| Script | Usage | Output |
| --- | --- | --- |
| [build-terminal-icons.py](libexec/build-terminal-icons.py) | `python3 libexec/build-terminal-icons.py /tmp/kael-font-preview` | Writes regular and bold fonts with monochrome warning and lightning glyphs to the specified directory |
| [size-starship-monochrome-icons.py](libexec/size-starship-monochrome-icons.py) | `python3 libexec/size-starship-monochrome-icons.py` | Sizes monochrome glyphs against a reference and updates the repository fonts |
| [build-yazi-icons.py](libexec/build-yazi-icons.py) | `python3 libexec/build-yazi-icons.py /path/to/yazi/yazi-config/preset` | Generates glyphs and Lua aliases from Yazi's presets. Updates the repository fonts and plugin |
| [build-nvim-statusline-icons.py](libexec/build-nvim-statusline-icons.py) | Run `python3 libexec/build-nvim-statusline-icons.py` after installing Neovim and the LazyVim plugins. Use `--help` to see how to specify plugin paths | Reads mini.icons and Which-key, then updates the repository fonts and Neovim glyph manifest |

The [Starship icon manifest](config/starship/icon-sources.json) records the sources, code points, and checksums.

### Update, check, and roll back

1. Check the Git worktree and save any local configuration changes you want to retain. After updating the checkout, rerun `./bootstrap.sh` in your chosen mode to update tools. For a configuration-only update, preview with `./install.sh --dry-run` and apply with `./install.sh`. Add `--headless` on a headless system.
2. Check with `./install.sh doctor`, then reopen the application or run `exec zsh -l` to load the new shell configuration. Existing tmux sessions can reload with `kael-tmux source-file "${XDG_CONFIG_HOME:-$HOME/.config}/tmux/independent-borders.conf"` from inside the session. A rebuilt tmux binary is used when a new server process starts.
3. To undo a deployment, run `./install.sh rollback --dry-run` and review its output, then run `./install.sh rollback`. It uses the latest unrestored backup to restore or remove affected files, fonts, and links. System packages and application data are managed independently. If you edited deployed files afterward, save those edits before using `./install.sh rollback --force`.

### Troubleshooting

| Symptom | What to check |
| --- | --- |
| A new command is missing | Use `./install.sh doctor` to check installation paths, run `exec zsh -l`, then confirm with `command -v TOOL`. Check Neovim, Gitoui, and Tudo versions separately |
| A tmux session is missing | Run `kael-tmux list-sessions` from the client used to start it, or select the original `KAEL_TMUX_MODE` from outside tmux. Use `KAEL_TMUX_BIN` to select a compatible build |
| Glyphs are missing or borders are misaligned | Run `fc-match 'Kael Starship Prompt Icons'`. In Tabby, check xterm Canvas, the Kael font, and the local border plugin. Restart Tabby after changing these settings |
| Gitoui or Codex image rendering is unavailable | Enable Sixel in Tabby and check `#{sixel_support}` and `#{client_termfeatures}` in tmux. Gitoui supports `--graph-renderer ascii` for a text graph |
| LazyVim or a language feature is missing | Check `nvim --version`, `tree-sitter --version`, `:Lazy`, `:checkhealth`, and `:Mason`. Review the deployment preview if you already have a custom Neovim configuration |
| A third-party Tabby plugin is missing | Quit Tabby and run desktop `./bootstrap.sh`. Then use `./install.sh doctor` to check links and plugin files |
| A TUI misses a key combination | Open Tabby's **Settings → Hotkeys** to check for conflicts. For example, `Ctrl+S` splits the pane below and `Ctrl+Space` toggles window visibility. Change the conflicting binding and try again |
| A download fails verification | Confirm the network, URL, architecture, and expected SHA-256 in the manifest and retry. The installer reuses verified cache entries |

## License

Project code and configuration are released under the MIT license. Bundled third-party components retain their own licenses. [MIT license](LICENSE) · [tmux license](vendor/tmux/COPYING) · [SauceCodePro Nerd Font license](fonts/SauceCodeProNF/LICENSE.txt) · [Icon sources](config/starship/icon-sources.json)
