# kael-terminal

**简体中文** · [English](README_en.md)

[![MIT 许可证](https://img.shields.io/badge/License-MIT-26734D?style=flat-square)](LICENSE)
[![支持 Ubuntu 和 Debian](https://img.shields.io/badge/Linux-Ubuntu%20%2B%20Debian-355E8D?style=flat-square)](#系统要求)
[![支持 x86_64 和 aarch64](https://img.shields.io/badge/Arch-x86__64%20%2B%20aarch64-635B9A?style=flat-square)](#系统要求)

适用于 Ubuntu 和 Debian 的终端工作环境。用 Zsh 和 Starship 导航项目，在定制 tmux 中保留会话，通过 Yazi、Vim、Neovim 和 Gitoui 浏览文件、编辑代码与审查提交。桌面安装提供 Tabby、Sixel 图像显示和配套字体，服务器可使用无桌面模式。

[安装](#安装) · [Shell 与目录导航](#shell-与目录导航) · [文件查找与阅读](#文件查找与阅读) · [tmux 会话](#tmux-会话) · [Tabby 桌面终端](#tabby-桌面终端) · [编辑器](#编辑器) · [Git 与 Gitoui](#git-与-gitoui) · [Codex CLI](#codex-cli) · [任务与笔记](#任务与笔记) · [系统工具与运行时](#系统工具与运行时) · [配置与维护](#配置与维护)

## 安装

### 系统要求

| 项目 | 要求 |
| --- | --- |
| 系统与架构 | 使用 APT 的 Ubuntu 或 Debian，`x86_64` 或 `aarch64` |
| 安装入口 | Git、Bash 和 Python 3.10 或更新版本。用日常账户运行，脚本会在安装系统软件包时调用 `sudo` |
| 网络 | 完整安装需要访问 APT 软件源、GitHub、Node.js 下载站、npm 和 PyPI |
| 桌面环境 | 默认安装 Tabby 和字体。部署前退出正在运行的 Tabby |
| 可选组件 | 自行安装 Neovim 和 Tree-sitter CLI。Gitoui 和 Tudo 提供独立的 Rust 构建脚本。已有 `~/anaconda3` 时可使用 Conda |

### 首次安装

在终端中运行以下命令。先查看预览，再执行与使用场景相符的安装命令。

```sh
git clone https://github.com/SprInec/kael-terminal.git
cd kael-terminal
./bootstrap.sh --dry-run
./bootstrap.sh
./install.sh doctor
exec zsh -l
```

在 SSH 主机或无桌面系统上，使用 `./bootstrap.sh --headless --dry-run` 预览，然后运行 `./bootstrap.sh --headless` 和 `./install.sh doctor --headless`。进入新 Zsh 后，运行 `kael-tmux new-session -A -s dev` 打开第一个命名会话。下文的路径示例以仓库根目录为起点。

| 场景 | 命令 | 结果 |
| --- | --- | --- |
| 完整桌面安装 | `./bootstrap.sh` | 安装系统依赖、固定版本工具、Tabby 和插件，构建 tmux 并部署配置与字体 |
| 无桌面安装 | `./bootstrap.sh --headless` | 安装命令行工具并部署配置，跳过 Tabby、桌面字体和 Yazi 字形插件 |
| 系统依赖已备齐 | `./bootstrap.sh --skip-apt` | 跳过 APT，继续下载、构建和部署。桌面模式要求 `tabby` 已可用 |
| 仅部署配置 | `./install.sh` 或 `./install.sh --headless` | 写入配置。桌面模式部署本地 Tabby 插件，第三方 npm 插件由完整安装提供 |
| 检查安装 | `./install.sh doctor` 或 `./install.sh doctor --headless` | 列出主要可执行文件的位置，并按模式检查定制 tmux 和 Tabby 插件 |

`--dry-run` 适用于安装预览和配置部署。部署会备份要替换的用户文件与链接，包括现有的 Codex 和 Tabby 配置。若需要手动备齐 APT 依赖，先用不带 `--skip-apt` 的预览查看依赖清单。桌面安装完成后运行 `tabby`，打开的本地配置默认使用 Zsh 登录 Shell。

### 组件版本

版本来自仓库中的安装清单。APT 软件包版本由系统软件源决定。

| 来源 | 组件 |
| --- | --- |
| 固定下载包 | Starship 1.26.0、Yazi 和 `ya` 26.9.1、zoxide 0.10.0、fzf 0.75.0、eza 0.23.5、dust 1.2.6、btop 1.4.8、Atuin 18.24.3、bat 0.26.1、Glow 3.0.0、Node.js 22.23.5（含 npm） |
| npm 与 Python 虚拟环境 | Codex CLI 0.171.0、Dooit 3.3.4、Dooit Extras 0.2.1、Textual 8.2.8、Rich 15.0.0、SQLAlchemy 2.0.55 |
| 本地构建 | tmux 使用随仓库分发的独立边框源码快照和 Kael 补丁 |
| 桌面组件 | Tabby 1.0.238、4 个锁定版本的 npm 插件、2 个本地插件、2 套字体 |
| 可选构建 | Gitoui 0.5.0、Tudo 1.1.0 |

安装器校验下载包的 SHA-256。可在 [下载清单](libexec/releases.tsv)、[Python 依赖](libexec/dooit-requirements.txt)和 [Tabby 插件锁文件](config/tabby/plugins/package-lock.json)中查询版本。

## Shell 与目录导航

Zsh 在交互会话中加载 Kael 工具目录、补全和历史设置。Starship 展示主机、时间、当前路径、Git 和当前项目适用的语言或工具模块。GitHub／GitLab 标识依据当前分支的跟踪远端从本地 Git 配置推断。先进入一个已检出的项目，再练习下面的操作。[Zsh 配置](config/zsh/terminal-tools.zsh) · [Starship 配置](config/starship/starship.toml) · [远端标识脚本](config/starship/git-host.py)

| 工具或插件 | 如何使用 | 本项目的设置 |
| --- | --- | --- |
| Zsh 补全 | 输入 `cd conf` 后按 `Tab`，用菜单完成路径 | `compinit` 和补全菜单已启用 |
| zsh-autosuggestions | 输入以前执行过的命令开头，按 `→` 接受建议 | 使用 APT 安装的插件文件 |
| zsh-syntax-highlighting | 输入命令时查看着色，便于识别引号、选项和命令名 | 在其他行编辑插件之后加载 |
| Starship | `starship explain` 查看当前提示符的模块。`git branch -vv` 查看跟踪关系 | 使用自定义图标、Git 状态和分支标识 |
| Atuin | 按 `Ctrl+R`，输入关键词，按 `Tab` 放回命令行编辑，或按 `Enter` 执行选中命令 | 历史默认保存在本机，关闭自动同步。命令行可用 `atuin search 'git'` 搜索 |
| fzf | 按 `Ctrl+T` 选取路径，或运行 `rg --files config \| fzf` 从文件列表选择 | `Ctrl+R` 交给 Atuin，fzf 的 `Alt+C` 被关闭 |
| zoxide | 先用 `cd` 访问项目，再用 `z kael-terminal` 跳回。`zi kael` 交互选择，`zoxide query -l` 列出已记录的目录 | 随 Zsh 启动并跟踪目录访问 |

[Atuin 使用指南](https://docs.atuin.sh/latest/guide/basic-usage/) · [Atuin 配置](config/atuin/config.toml)

## 文件查找与阅读

### Yazi 文件管理器

在 Zsh 中运行 `y config`。按 `→` 进入选中的目录，按 `←` 返回上一级。浏览到目标目录后按 `q`，Shell 会切换到最后所在的目录。按大写 `Q` 退出并停留在启动前的目录。

| 操作 | 按键或命令 |
| --- | --- |
| 查看帮助 | `F1` 或 `~` |
| 打开选中的文件 | `Enter`。按 `O` 查看可用的打开方式，文本编辑使用 `VISUAL`、`EDITOR` 或 Vim |
| 按名称／内容搜索 | `s` 调用 fd，`S` 调用 ripgrep |
| 显示隐藏项、选择文件 | `.` 切换隐藏项，`Space` 切换当前文件的选中状态 |
| 复制、剪切、粘贴 | `y`、`x`、`p` |
| 创建或改名 | `a` 创建文件，名称以 `/` 结尾时创建目录。`r` 重命名 |
| 管理上游插件 | `ya pkg list` 查看包清单，`ya pkg --help` 查看管理命令 |

Kael 主题沿用 tmux 的绿系配色。`init.lua` 调整目录样式并加载 `kael-yazi-icons` 字形别名，桌面部署将该插件与字体配套写入。无桌面模式继续使用 Yazi 原有字形。[打开方式、主题与本地插件](config/yazi/) · [Yazi 按键指南](https://yazi-rs.github.io/docs/quick-start/)

### 命令行速查

| 工具 | 示例 | 用途 |
| --- | --- | --- |
| ls | `ll`、`la`、`l` | 查看详情、隐藏项或多列列表 |
| eza | `lt`、`lgit`、`eza -al --git config` | 看两层目录树，或在列表中查看 Git 状态 |
| tree | `tree -L 2 config` | 输出适合复制和对照的目录结构 |
| fd / fdfind | `fd -e toml . config` | 按文件名或扩展名查找路径。APT 的 `fdfind` 由安装器提供 `fd` 入口 |
| ripgrep | `rg -n -g '*.toml' 'theme' config` | 按文件类型搜索内容并显示行号 |
| bat | `bat --style=numbers bootstrap.sh` | 带语法高亮和行号地阅读文件。分页时按 `q` 返回 |
| Glow | `glow README.md`、`glow -t .`、`glow -p README.md` | 渲染单份 Markdown、打开目录浏览界面或通过分页器阅读 |
| jq | `jq '.dependencies \| keys' config/tabby/plugins/package.json` | 提取 JSON 字段，此例列出 Tabby 插件 |
| file | `file fonts/StarshipPromptIcons/StarshipPromptIcons-Regular.ttf` | 识别文件类型 |
| Chafa | `chafa --format=symbols 路径/图片.png` | 用终端字符预览图片。替换为实际图片路径，桌面模式通过 APT 安装 |

Glow 默认使用自动配色、80 列折行，交互模式开启鼠标，直接输出时默认关闭分页。`glow config` 打开用户配置。[Glow 配置](config/glow/glow.yml)

## tmux 会话

tmux 在一个终端中管理多个窗口与窗格。关闭客户端或暂离后，会话里的进程仍可继续运行。`kael-tmux` 启动本项目构建，读取独立边框配置，并按客户端选择套接字。请从 tmux 外执行第一个命令。

```sh
kael-tmux new-session -A -s dev
kael-tmux list-sessions
kael-tmux attach-session -t dev
```

第一条命令新建或进入 `dev`。按 `Ctrl+B`、`d` 暂离后，再运行其余命令查看和恢复会话。在 tmux 外直接运行 `kael-tmux` 会新建或进入 `work`。已位于 Kael 会话时，启动器复用当前套接字，通常可直接运行 `kael-tmux list-windows` 或 `kael-tmux list-panes`。

| 按 `Ctrl+B` 后再按 | 操作 |
| --- | --- |
| `c`、`n` 或 `p` | 新建窗口，或切换到下一个／上一个窗口 |
| `%` 或 `"` | 在右侧／下方分屏 |
| 方向键 | 切换窗格 |
| `z` | 放大当前窗格，再按一次恢复 |
| `F`（大写） | 在浮动和平铺之间切换当前窗格 |
| `[` | 进入复制模式。可用滚轮浏览历史，用 `q` 退出复制模式 |
| `d` | 暂离会话 |
| `?` | 查看当前键绑定 |

### 边框、状态栏与 Sixel

- 活动窗格带高亮和环绕发光。识别到交互式 SSH、ADB Shell、Mosh 或 Dropbear 会话时，高亮切换为粉色。识别到传输进度时，窗格边框会显示进度。右键窗格可分屏、交换、标记或调整浮动窗格的大小与位置。
- 底部状态栏显示会话、窗口、前缀状态和当前路径，从本机读取 Git 与 CPU、内存、磁盘、主机名和时间信息，窄窗口会压缩字段。前台匹配时会显示 Codex 或 Claude 的标识。
- 普通模式使用 `kael-borders`，Sixel 图像模式使用 `kael-borders-sixel`。Tabby 下自动选择 Sixel。可在 tmux 外用 `KAEL_TMUX_MODE=plain kael-tmux new-session -A -s dev` 强制普通模式，或在支持 Sixel 的客户端用 `KAEL_TMUX_MODE=sixel kael-tmux new-session -A -s dev` 选择图像模式。查看对应会话时须使用相同模式。

在会话内运行下列命令检查图像能力和当前窗格。客户端支持 Sixel 时，第一条输出中的两项应包含 `1` 和 `sixel`。

```sh
kael-tmux display-message -p '#{sixel_support} #{client_termfeatures}'
kael-tmux list-panes -F '#{pane_index} #{pane_title} #{pane_current_command}'
```

主配置开启鼠标、焦点事件和闪烁下划线光标。独立边框配置含浮动窗格菜单、进度与发光开关，状态布局和数据采集分别位于 `status.conf` 和 `status.py`。例如在当前窗口运行 `kael-tmux set-window-option @pane-border-glow off` 可关闭发光。[tmux 配置](config/tmux/) · [定制源码与补丁说明](vendor/tmux/README.md)

Bootstrap 会自动构建 tmux。已有系统构建依赖时，也可单独重建，设置 `KAEL_BUILD_JOBS` 可指定并行任务数。

```sh
./vendor/tmux/build.sh "${XDG_DATA_HOME:-$HOME/.local/share}/kael-terminal/bin/tmux"
kael-tmux -V
```

## Tabby 桌面终端

运行 `tabby`，默认配置会打开 `/usr/bin/zsh -l`。终端使用 xterm Canvas、自动明暗配色、下划线光标和 Sixel。Kael 字体提供彩色工具图标及 tmux、Yazi、Neovim 使用的字形，普通字符可由 Liberation Mono 显示。通过 `Ctrl+,` 打开设置。[Tabby 配置](config/tabby/config.yaml)

| 按键 | 操作 |
| --- | --- |
| `Ctrl+Shift+T` / `Ctrl+Shift+W` | 新建／关闭标签页 |
| `Ctrl+Tab` / `Ctrl+Shift+Tab` | 下一个／上一个标签页 |
| `Alt+1` 至 `Alt+0` | 选择第 1 至第 10 个标签页 |
| `Ctrl+Shift+C` / `Ctrl+Shift+V` | 复制／粘贴 |
| `Ctrl+F` / `Ctrl+Shift+P` | 搜索终端输出／打开命令选择器 |
| `Ctrl+D`、`Ctrl+S`、`Ctrl+A`、`Ctrl+W` | 在右、下、左、上方分割 Tabby 窗格 |
| `Alt+W`、`Alt+A`、`Alt+S`、`Alt+D` | 在 Tabby 窗格间切换焦点 |
| `Ctrl+Alt+Enter` | 最大化或恢复当前 Tabby 窗格 |

### Tabby 插件

桌面 Bootstrap 安装下表中的插件。启动后可在 **设置 → 插件** 核对。终端装饰插件随标签页加载，调整插件启用状态后重启 Tabby。

| 插件 | 用途 | 使用方法 |
| --- | --- | --- |
| `tabby-background` 2.2.4 | 背景图与界面字体 | 在插件设置添加背景。仓库中的背景列表为空，界面字体设为 SauceCodePro Nerd Font |
| `tabby-highlight` 3.0.0 | 关键词着色与文本替换 | 在设置中查看高亮和替换配置，用 `printf '%s\n' 'ERROR WARN INFO' '错误 警告 信息'` 检查输出。按需选择或调整配置 |
| `tabby-sftp-plus` 3.2.1 | SSH 标签页中的双栏文件管理、上传下载、书签和传输日志 | 当前配置禁用了 `sftp-plus`。启用后重启 Tabby，连接 SSH，在标签页工具栏打开 **SFTP+** |
| `tabby-windy-quick-commands` 2.1.4 | 保存、查找并发送常用命令 | 按 `Ctrl+P` 打开抽屉，先保存 `git status --short` 并发送到当前终端。`Ctrl+Alt+H` 切换快捷键提示 |
| `tabby-sync-output` 1.0.0 | 合并 DEC 2026 同步输出，减少 tmux 重绘时的光标闪动 | 自动应用。启动 `kael-tmux` 后切换窗格即可观察效果 |
| `tabby-tmux-capsule-alignment` 1.0.0 | Canvas 下划线位置、状态栏色块、紧凑窗格边框和细线绘制 | 自动应用。在 Tabby 中运行 `kael-tmux` 并分屏，查看底部状态与边框 |

本地插件代码包含同步输出适配器与帧缓冲器，以及分别处理下划线、状态栏、窗格边框和细线的 Canvas 模块。`quick-cmds` 在禁用名单中，快捷命令由 Windy 插件提供。配置也保存了可选插件的键位，单独安装 AgentDeck 后可用 `Ctrl+L` 聚焦列表，使用兼容的 `tmuxPlugin` 时可用 `Ctrl+Shift+[` 或 `Ctrl+Shift+]` 切换窗口。[插件清单与本地代码](config/tabby/plugins/) · [SFTP+ 说明](https://github.com/10D24D/Tabby-SFTP-Plus) · [Windy Quick Commands 说明](https://github.com/windyy0/tabby-windy-quick-commands)

## 编辑器

### Vim

`vim README.md` 打开文件。配置启用行号、语法着色、文件类型缩进、增量搜索和智能大小写。进入 Vim 后按 `i` 开始编辑，用 `Esc` 返回普通模式，输入 `:wq` 并回车保存退出。输入 `/tmux` 搜索，再用 `n` 跳到下一处。只想退出并丢弃未保存的修改时，用 `:q!`。[Vim 配置](config/vim/vimrc)

### Neovim 与 LazyVim

在 `PATH` 中准备带 LuaJIT 的 **Neovim 0.12+** 和 **Tree-sitter CLI 0.26.1+**。插件首次安装需要访问 GitHub，解析器构建需要 C 编译器。

```sh
nvim --version
tree-sitter --version
nvim .
```

在 Neovim 中用 `:Lazy` 查看插件安装状态，`:checkhealth` 查看依赖，`:Mason` 查看语言工具。需要使用锁文件中的版本时运行 `:Lazy restore`。项目启用了 C/C++、Python 和 mini.surround 扩展。已有的 `clangd`、`pyright-langserver`、`lua-language-server` 和 `ruff` 可直接复用，Mason 提供缺少的工具。C/C++、Lua、Python 分别使用 clang-format、StyLua 与 Ruff 格式化。

| 按键或命令 | 操作 |
| --- | --- |
| `Space e` | 打开项目根目录文件树 |
| `Space Space` / `Space s g` | 按文件名查找／搜索项目文本 |
| `gd` / `K` | 跳到定义／查看悬浮信息，需已附加对应的语言服务器 |
| `Space c f` | 格式化当前文件或选区 |
| `Space g g` / `Space g G` | 通过 Gitoui 查看 Git 根目录／当前工作目录，需安装 `gitoui` |
| `Space` 后稍等 | 查看 Which-key 提示 |

Kael 使用 Catppuccin Mocha 的定制配色，定制 Lualine、Snacks、Blink、Which-key 和 Bufferline 的图标与间距。对已有的自定义 LazyVim，部署会提供状态栏、图标清单和 Gitoui 快捷键。较旧的 Neovim 加载本项目入口时使用 `~/.vimrc`。原有受管的 `init.vim` 通过 `kael-init.vim` 转入 Lua 配置。[Neovim 配置与锁文件](config/nvim/) · [Vim 入口](config/vim/) · [LazyVim 按键](https://www.lazyvim.org/keymaps)

| 配置文件 | 用途 |
| --- | --- |
| `init.lua`、`lua/config/lazy.lua` | 检查 Neovim 版本，安装并加载 lazy.nvim、LazyVim 及扩展 |
| `lua/config/options.lua` | 启用自动格式化，隐藏空闲命令行，将已有的 Mason 可执行目录加入 `PATH` |
| `lua/plugins/appearance.lua`、`editor.lua` | 调整主题、光标动画、语言服务器和格式化器 |
| `lua/plugins/kael-statusline.lua`、`lua/kael/statusline-icons.json` | 自定义状态栏和选择器等界面的图标、间距与文件类型字形 |
| `lua/plugins/gitoui.lua`、`lazy-lock.json` | 配置 Gitoui 启动方式与快捷键，记录插件版本 |

### LazyVim 插件速查

下表覆盖 [插件锁文件](config/nvim/lazy-lock.json)的直接条目。按 `Space` 开始的组合键在普通模式下依次按下，语言功能随当前文件类型和已安装的工具启用。

| 插件 | 用途 | 使用入口 |
| --- | --- | --- |
| LazyVim | 编辑器预设与语言扩展 | `:LazyExtras` 查看可用扩展 |
| lazy.nvim | 加载插件、管理版本 | `:Lazy` 查看插件，`:Lazy restore` 对齐锁文件 |
| snacks.nvim | 启动页、文件树、搜索、终端等小工具 | `Space e` 打开文件树，`Space s g` 搜索文本 |
| lualine.nvim | 模式、文件、Git 等状态信息 | 观察底部状态栏。Kael 添加文件类型字形和时钟 |
| bufferline.nvim | 显示缓冲区标签 | `[b` 和 `]b` 切换缓冲区 |
| catppuccin | 当前 Mocha 主题 | `:colorscheme catppuccin-mocha` |
| tokyonight.nvim | 备选主题和首次引导的主题候选 | `:colorscheme tokyonight` |
| smear-cursor.nvim | 移动时平滑光标动画 | 普通模式移动光标即可看到效果 |
| which-key.nvim | 显示多键指令提示 | 按 `Space` 后稍等 |
| noice.nvim | 命令行 UI 与消息记录 | `:Noice history` 查看消息 |
| nui.nvim | 为 Noice 等插件提供弹窗组件 | 在 Noice 命令行或弹窗中使用 |
| plenary.nvim | 供其他插件复用的 Lua 工具库 | 用 `:Lazy` 检查是否安装 |
| mini.icons | 文件、目录和类型图标 | 在文件树或文件选择器中查看图标 |
| blink.cmp | 插入模式补全 | 输入代码时查看候选，`Ctrl+Space` 可手动触发 |
| friendly-snippets | 提供文件类型对应的片段 | 在补全菜单中选择片段 |
| mini.ai | 扩展 Vim 文本对象 | 用 `viq` 选中最近的引号内容 |
| mini.pairs | 自动配对括号和引号 | 插入模式输入 `(`，自动补出 `)` |
| mini.surround | 添加、删除和替换环绕符号 | 用 `gsaiw"` 为当前单词加双引号 |
| ts-comments.nvim | 按语法上下文选择注释格式 | `gcc` 切换当前行注释 |
| flash.nvim | 跳到屏幕上的匹配位置 | 按 `s` 后输入目标文本，再按提示字母跳转 |
| grug-far.nvim | 项目搜索与替换 | `Space s r` 打开界面，先核对匹配结果再替换 |
| gitsigns.nvim | 在边栏标记 Git 改动 | `]h` / `[h` 跳到下一处／上一处改动 |
| trouble.nvim | 汇总诊断与列表 | `Space x x` 打开诊断面板 |
| todo-comments.nvim | 标记并检索 TODO、FIXME 等注释 | `Space s t` 打开 TODO 选择器 |
| persistence.nvim | 保存和恢复编辑会话 | `Space q s` 恢复当前目录的会话 |
| nvim-treesitter | 解析代码语法树 | `:TSInstall lua` 安装 Lua 解析器 |
| nvim-treesitter-textobjects | 用语法树选中结构化代码 | 已安装解析器时，用 `]f` 跳到下一个函数起点 |
| nvim-ts-autotag | 自动闭合和同步重命名标签 | 在支持的文件中输入 `<div>` 观察成对标签 |
| nvim-lspconfig | 配置语言服务器 | 打开源文件后运行 `:checkhealth vim.lsp` |
| mason.nvim | 管理语言工具 | `:Mason` 查看安装情况 |
| mason-lspconfig.nvim | 将 Mason 的语言服务器接入 Neovim | 在 `:Mason` 确认工具已装，再通过 LSP 健康检查确认附加 |
| clangd_extensions.nvim | clangd 的附加功能 | 连接 clangd 后，用 `:ClangdSwitchSourceHeader` 切换源文件与头文件 |
| lazydev.nvim | 为 Lua 配置提供 Neovim API 类型信息 | 编辑 Lua 配置时，输入 `vim.api.` 查看补全 |
| venv-selector.nvim | 切换 Python 虚拟环境 | 打开 Python 文件后运行 `:VenvSelect` |
| conform.nvim | 调用格式化工具 | `:ConformInfo` 查看文件对应的格式化器 |
| nvim-lint | 调用外部 lint 工具并展示诊断 | 编辑已配置的文件类型后，用 `Space c d` 查看当前行诊断 |

## Git 与 Gitoui

### Git 操作

在仓库根目录运行下列命令，依次查看工作区、未暂存改动、已暂存改动和提交历史。`git-local` 始终从 Kael 仓库运行 Git，并支持仓库已有的 `.git-kael` 元数据目录。

```sh
git status --short
git diff
git diff --cached
git log --oneline --graph --decorate -15
./git-local status --short
```

编辑文件后，用 `git add -- README.md README_en.md` 暂存这两份文档，再用 `git diff --cached` 核对，最后运行 `git commit -m "docs: update the manual"` 保存提交。请按实际编辑范围选择文件。[仓库 Git 入口](git-local)

### 安装和使用 Gitoui

Gitoui 是终端 Git 客户端，适合查看分支与提交图、比较文件改动和处理冲突。配置默认使用 `kael-tmux` 主题、自动选择图形后端、增强并排差异与三栏冲突视图。准备好 Rust 和 Cargo **1.88+**，从仓库根目录运行以下命令。

```sh
./vendor/gitoui/build.sh
gitoui --version
gitoui --graph-renderer ascii -n 100
```

安装路径为 `${XDG_DATA_HOME:-$HOME/.local/share}/kael-terminal/bin/gitoui`。支持 Sixel 的客户端可运行 `gitoui --graph-renderer sixel`。LazyVim 的 Gitoui 快捷键会在兼容的 Sixel tmux 会话中打开新窗口，其他会话使用 Snacks 终端与文本图。

| 要做什么 | 操作 |
| --- | --- |
| 审查一次提交 | 在提交列表用方向键选中提交并按 `Enter`，再选中一个文件按 `Enter` 查看差异 |
| 浏览分支与搜索提交 | `Tab` 打开引用面板，`f` 打开搜索 |
| 查看并暂存工作区改动 | 在提交列表首行的未提交改动上按 `Enter`。用方向键浏览，`a` 暂存所选文件，`u` 从已暂存面板撤回 |
| 编辑提交消息 | 核对已暂存的文件后，按 `w` 打开提交消息编辑器，`Ctrl+Enter` 或 `Ctrl+S` 提交 |
| 查看帮助或返回 | `?` 查看当前按键，`Esc` 返回，`q` 退出主视图 |

构建脚本校验 Gitoui 0.5.0 源码包、固定 Cargo 依赖并应用四个补丁。`sixel-node-aspect` 校正节点比例，`tabby-sixel-and-smooth-graph` 调整 Tabby 的 Sixel 与平滑连线，`terminal-graph-antialiasing` 改善绘图边缘，`compact-footer` 缩短底栏。[Gitoui 配置](config/gitoui/) · [构建脚本与补丁](vendor/gitoui/)

## Codex CLI

Codex CLI 在当前工作目录中处理代码任务。首次运行前登录，在仓库中启动会话。

```sh
codex --version
codex login
codex login status
codex
```

可从「列出这个仓库的安装入口，并解释桌面和无桌面模式的区别」开始。之后用 `codex resume` 选择一个历史会话，或用 `codex resume --last` 继续当前目录最近的会话。用 `codex -i /path/to/image.png` 附加本地图片，先把示例路径改为实际文件。

| 集成 | 用途与操作 |
| --- | --- |
| Codex 配置 | 部署到 `${CODEX_HOME:-$HOME/.codex}/config.toml`。随仓库提供 Ada 主题、`gpt-6.2-sol` 和 `xhigh` 推理设置，模型可用性取决于登录账户 |
| Ada 状态栏提供器 | Python MCP 提供器显示当前模型、推理强度、可用的周额度和上下文余量，以及 Git 改动。打开仓库中的交互会话即可查看 |
| Tabby 图片预览 | Zsh 包装器在 Tabby 本地标签页或兼容的 Sixel tmux 窗格中启用全屏预览。用 `command codex` 可直接调用 CLI，用 `codex --no-alt-screen` 可保留终端滚动历史 |

[Codex 配置、状态栏和预览包装器](config/codex/)

## 任务与笔记

### Dooit

运行 `dooit` 打开工作区和任务列表。Dooit 支持任务、子任务、到期日和重复周期。Kael 配置增加底部模式、时钟和工作区状态，随 tmux 焦点变化调整颜色。任务备注保存在本机任务数据库中。

| 按键 | 操作 |
| --- | --- |
| `a` / `c` | 在任务列表创建同级任务／切换完成状态 |
| `n` | 为当前任务编辑多行备注，`Esc` 保存并返回 |
| `Enter` 或 `Ctrl+M` | 在任务列表切换备注面板 |
| `Ctrl+N` | 显示或隐藏工作区列表，由 Dooit Extras 提供 |
| 鼠标拖选 / `Ctrl+C` | 拖选释放时复制，`Ctrl+C` 有选区时复制、无选区时退出 |
| `?` / `Ctrl+Q` | 查看当前按键／退出 |

`config.py` 定义配色、状态栏和子任务标记，`task_notes.py` 实现备注面板，`text_selection.py` 处理复制。Bootstrap 在专用虚拟环境安装 Dooit 与 Dooit Extras，锁定用于 TUI 的 Textual、用于文本渲染的 Rich 及用于存储的 SQLAlchemy。[Dooit 配置与扩展](config/dooit/) · [依赖版本](libexec/dooit-requirements.txt) · [Dooit 使用指南](https://dooit-org.github.io/dooit/getting_started/basics.html)

### Tudo

Tudo 提供多列表待办和独立的 Markdown 笔记本。使用 Rust 和 Cargo **1.95+** 构建 Kael 版本。首次运行时选择本机数据目录。

```sh
./vendor/tudo/build.sh
tudo --version
TUDO_THEME=kael-tmux tudo
```

| 按键 | 操作 |
| --- | --- |
| `1` / `2` | 切换任务／笔记标签页 |
| `Tab`、方向键 | 切换面板、选择条目 |
| `a`、`Space` | 在任务页添加任务、切换完成状态 |
| `n`、`Ctrl+S` | 编辑任务备注并保存。在笔记页用 `Enter` 编辑选中的笔记 |
| `/` | 搜索条目 |
| `T`、`S` | 选择主题、查看应用设置与数据位置 |
| `?`、`q` | 查看当前标签页帮助、退出 |

构建脚本校验 Tudo 1.1.0 源码并安装至 `~/.local/bin/tudo`。`kael-tmux-theme.patch` 添加可通过主题选择器启用的配色，`input-cursor.patch` 改善单行、多行及宽字符的光标定位。Tudo 将列表和笔记分别保存为 JSON 和 Markdown，通过 `S` 可查看配置与存储路径。[构建脚本与补丁](vendor/tudo/) · [Tudo 使用指南](https://github.com/jolleyDesign/tudo)

## 系统工具与运行时

| 工具 | 示例 | 用途 |
| --- | --- | --- |
| btop | `btop`，按 `Esc` 打开菜单，按 `q` 退出 | 查看 CPU、内存、网络、磁盘与进程。配置启用鼠标、进程树和同步刷新，默认每 2 秒更新 |
| dust | `dust -d 2 .` | 按空间占用查看当前目录，逐层定位占用较大的路径 |
| Node.js / npm | `node --version`、`npm --version` | JavaScript 运行时和包管理器。Bootstrap 用 npm 安装 Codex，以 `npm ci` 还原 Tabby 插件依赖 |
| Python / venv | `python3 --version`、`python3 -m venv /tmp/kael-example-venv` | 运行配置部署、状态栏和图标脚本，为 Dooit 等工具隔离依赖 |
| Conda | `conda env list`、`conda activate base`、`conda deactivate` | 管理已有 Anaconda 环境。Zsh 在 `~/anaconda3/bin/conda` 存在时加载初始化 |
| Fontconfig | `fc-match 'Kael Starship Prompt Icons'`、`fc-cache -f` | 检查终端所用字体并刷新缓存 |
| Xclip / wl-clipboard | `xclip -selection clipboard -o`、`wl-paste` | 分别在 X11 与 Wayland 读取剪贴板。由桌面安装提供 |
| ncurses / terminfo | `tic -V`、`infocmp xterm-256color` | 检查终端能力描述。Codex 预览包装器使用 `tic` 编译临时条目 |

系统依赖还包括 APT、证书包与 curl、tar/unzip/xz、校验工具、C 编译器、Autoconf、Automake、Bison、pkg-config、patch 以及 libevent、ncurses、zlib、libpng 的开发包。需要检查构建环境时可运行 `cc --version`、`pkg-config --modversion libevent` 或 `./bootstrap.sh --dry-run`。[btop 配置](config/btop/btop.conf) · [系统依赖声明](bootstrap.sh)

## 配置与维护

### 配置位置

下表使用默认目录。部署接受 `XDG_CONFIG_HOME`、`XDG_DATA_HOME`、`XDG_STATE_HOME`、`XDG_CACHE_HOME`；Zsh 入口跟随 `ZDOTDIR`，Codex 和 Tabby 可使用 `CODEX_HOME`、`TABBY_CONFIG_DIRECTORY`，Atuin 配置路径优先取 `ATUIN_CONFIG_DIR`，其次取 `ATUIN_HOME`。

| 模块 | 仓库入口 | 默认部署位置 |
| --- | --- | --- |
| Zsh | [config/zsh/](config/zsh/) | `~/.zshrc` 加载 `~/.config/kael-terminal/terminal-tools.zsh`，个人设置写入同目录的 `local.zsh` |
| Starship / Atuin | [starship](config/starship/) · [atuin](config/atuin/) | `~/.config/starship.toml`、`~/.config/starship/git-host.py`、`~/.atuin/config.toml` |
| tmux | [config/tmux/](config/tmux/) · [启动器](bin/kael-tmux) | `~/.tmux.conf`、`~/.config/tmux/`、`~/.local/share/kael-terminal/bin/kael-tmux` |
| Tabby | [config/tabby/](config/tabby/) | `~/.config/tabby/config.yaml` 和 `~/.config/tabby/plugins/`，包含插件链接 |
| Vim / Neovim | [vim](config/vim/) · [nvim](config/nvim/) | `~/.vimrc`、`~/.config/nvim/` |
| Yazi / Glow / btop | [yazi](config/yazi/) · [glow](config/glow/) · [btop](config/btop/) | `~/.config/` 下各自的应用目录 |
| Codex | [config/codex/](config/codex/) | `~/.codex/config.toml`、`~/.codex/statusline/ada-usage-statusline/statusline.py`、`~/.local/share/kael-terminal/codex-tabby-preview.py` |
| Dooit / Gitoui | [dooit](config/dooit/) · [gitoui](config/gitoui/) | `~/.config/dooit/`、`~/.config/gitoui/` |
| 字体 | [fonts/](fonts/) | `~/.local/share/fonts/kael-terminal/`，由桌面部署写入 |
| 安装与备份 | [bootstrap.sh](bootstrap.sh) · [install.sh](install.sh) · [deploy.py](libexec/deploy.py) | `~/.local/share/kael-terminal/{bin,opt}`、`~/.cache/kael-terminal/downloads/`、`~/.local/state/kael-terminal/backups/` |

### 字体与资源生成

无需构建即可使用随桌面部署提供的字体。**Kael Starship Prompt Icons** 包含工具图标、单色警告与闪电字形，并补充 tmux、Yazi 和 Neovim 所需的符号。**SauceCodePro Nerd Font Mono** 提供常规和粗体的等宽 Nerd Font 字形，也是部分生成脚本的来源。**Liberation Mono** 是 Tabby 配置中的普通字符后备字体。

如果要改字形，准备 Python 3.11 或更新版本，在虚拟环境中用 `python -m pip install fonttools` 安装依赖。写入仓库字体的脚本执行后，用 `git status --short` 检查生成内容，再重新部署字体并重开 Tabby。

| 脚本 | 用法 | 输出 |
| --- | --- | --- |
| [build-terminal-icons.py](libexec/build-terminal-icons.py) | `python3 libexec/build-terminal-icons.py /tmp/kael-font-preview` | 向指定目录生成带单色警告和闪电的常规与粗体字库 |
| [size-starship-monochrome-icons.py](libexec/size-starship-monochrome-icons.py) | `python3 libexec/size-starship-monochrome-icons.py` | 按 Starship 配置将单色图标调整到参考大小，更新仓库字体 |
| [build-yazi-icons.py](libexec/build-yazi-icons.py) | `python3 libexec/build-yazi-icons.py /path/to/yazi/yazi-config/preset` | 从 Yazi 源码的 preset 生成字形与 Lua 别名，更新仓库字体和插件 |
| [build-nvim-statusline-icons.py](libexec/build-nvim-statusline-icons.py) | 安装 Neovim 和 LazyVim 插件后，运行 `python3 libexec/build-nvim-statusline-icons.py`。用 `--help` 查看如何指定插件路径 | 读取 mini.icons 和 Which-key，更新仓库字体与 Neovim 图标清单 |

图标来源、码位和校验值见 [Starship 图标清单](config/starship/icon-sources.json)。

### 更新、检查与回滚

1. 查看 Git 工作区，保留已有的本地配置修改。更新仓库后，重跑对应模式的 `./bootstrap.sh` 可同步工具。只更新配置时，先用 `./install.sh --dry-run` 查看计划，再用 `./install.sh` 应用。无桌面环境在相应命令中加 `--headless`。
2. 用 `./install.sh doctor` 检查部署，重开应用或运行 `exec zsh -l` 加载新的 Shell 配置。已有 tmux 会话可在会话内运行 `kael-tmux source-file "${XDG_CONFIG_HOME:-$HOME/.config}/tmux/independent-borders.conf"` 重读配置。重编 tmux 后，新服务进程才会加载新二进制。
3. 需要撤销部署时先运行 `./install.sh rollback --dry-run`，确认后运行 `./install.sh rollback`。回滚按最近一份尚未恢复的备份处理被更新或创建的文件、字体与链接。系统软件包和应用数据按各自的方式管理。若配置在部署后被编辑过，先保存这些编辑，再用 `./install.sh rollback --force` 恢复备份。

### 常见问题

| 现象 | 检查方法 |
| --- | --- |
| 新命令找不到 | 用 `./install.sh doctor` 查看安装路径，执行 `exec zsh -l` 后用 `command -v 工具名` 确认。Neovim、Gitoui 和 Tudo 需单独检查版本 |
| 找不到 tmux 会话 | 从启动会话时的终端运行 `kael-tmux list-sessions`，或在 tmux 外用原来的 `KAEL_TMUX_MODE` 选择对应套接字。可用 `KAEL_TMUX_BIN` 指向兼容构建 |
| 图标缺失或边框错位 | 用 `fc-match 'Kael Starship Prompt Icons'` 确认字体。Tabby 设置应使用 xterm Canvas、Kael 字体和本地边框插件。修改后重启 Tabby |
| Gitoui 或 Codex 图片只显示文本或不可用 | 在 Tabby 中启用 Sixel，并在 tmux 中查询 `#{sixel_support}` 和 `#{client_termfeatures}`。Gitoui 可用 `--graph-renderer ascii` 查看文本提交图 |
| Neovim 未加载 LazyVim 或语言功能 | 检查 `nvim --version`、`tree-sitter --version`、`:Lazy`、`:checkhealth` 和 `:Mason`。有自定义 Neovim 配置时先检查部署预览 |
| Tabby 第三方插件缺失 | 退出 Tabby 后运行桌面 `./bootstrap.sh`，再用 `./install.sh doctor` 检查链接与插件文件 |
| TUI 收不到某个组合键 | 在 Tabby **设置 → 快捷键**检查按键是否已绑定。例如 `Ctrl+S` 用于向下分屏，`Ctrl+Space` 用于切换窗口显示。调整冲突项后再试 |
| 下载校验失败 | 检查网络和下载地址，确认架构及清单中的 SHA-256 后重试。已校验的缓存包会复用 |

## 许可证

项目自有代码与配置按 MIT 许可证发布。随仓库分发的第三方材料适用各自的许可。[MIT 许可证](LICENSE) · [tmux 许可](vendor/tmux/COPYING) · [SauceCodePro Nerd Font 许可](fonts/SauceCodeProNF/LICENSE.txt) · [图标来源](config/starship/icon-sources.json)
