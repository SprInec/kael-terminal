<div align="center">

# kael-terminal

**简体中文** · [English](README_en.md)

[![MIT 开源许可证](https://img.shields.io/badge/License-MIT-26734D?style=flat-square)](LICENSE) [![支持 Ubuntu 和 Debian](https://img.shields.io/badge/Linux-Ubuntu%20%2B%20Debian-355E8D?style=flat-square)](#快速开始) [![支持 x86_64 和 aarch64](https://img.shields.io/badge/Arch-x86__64%20%2B%20aarch64-635B9A?style=flat-square)](#快速开始)

[快速开始](#快速开始) · [日常工具](#日常工具) · [工作会话](#工作会话) · [自定义和回滚](#自定义和回滚) · [许可证](#许可证)

面向 Linux 工作站和服务器的终端配置。用 Zsh 和 Starship 统一提示符与快捷键，用定制 tmux 保留工作会话，再用一组命令行工具完成文件浏览、搜索、编辑和任务管理。桌面安装还会配置 Tabby、字体和 Sixel 图像预览。

</div>

## 快速开始

准备好 **Git、Bash 和 Python 3.10 或更新版本**。安装脚本面向使用 APT 的 Ubuntu 和 Debian 系统，支持 **x86_64** 与 **aarch64**。完整安装需要访问 APT 软件源、GitHub、Node.js、npm 和 PyPI，系统依赖通过 `sudo` 安装。桌面安装前请退出 Tabby。

```sh
git clone https://github.com/SprInec/kael-terminal.git
cd kael-terminal
./bootstrap.sh --dry-run
./bootstrap.sh
exec zsh -l
```

预览会列出依赖和待变更文件。正式安装会校验下载清单中的 SHA-256、编译定制 tmux，并为当前用户部署配置。默认桌面模式还会安装 Tabby、插件和字体。

| 安装场景 | 命令 |
| --- | --- |
| SSH 或无桌面服务器 | `./bootstrap.sh --headless` |
| 系统依赖已装好 | `./bootstrap.sh --skip-apt` |
| 已有工具，只部署配置 | `./install.sh` 或 `./install.sh --headless` |
| 检查可执行文件和插件 | `./install.sh doctor` 或 `./install.sh doctor --headless` |

`--dry-run` 可与所选安装参数组合，例如 `./bootstrap.sh --headless --dry-run`。跳过 APT 时，可先用预览查看需手动安装的依赖。桌面模式下还需预装 Tabby。配置部署会启用两个仓库自带的 Tabby 插件，第三方 npm 插件由完整安装流程部署。

## 日常工具

下面使用仓库中的文件作为示例。安装后回到仓库目录，在新的 Zsh 会话里试用。

### 补全、历史和目录跳转

- **Zsh + Starship** 提供命令补全、历史建议、语法高亮和带 Git 远端标识的提示符。在命令或路径后按 `Tab` 补全。打开一个 Git 仓库即可看到分支信息。
- **Atuin** 搜索已执行的命令。按 `Ctrl+R` 输入关键词，按 `Tab` 将选中的命令放回编辑行，或按 `Enter` 执行。默认关闭自动同步。 [Atuin 使用文档](https://docs.atuin.sh/main/guide/basic-usage/)
- **fzf** 模糊查找。在 Zsh 中按 `Ctrl+T` 选取文件路径并插入命令行。也可把列表交给 `fzf`，例如 `rg --files config | fzf`。
- **zoxide** 记住访问过的目录。先用 `cd` 访问目录，之后可用 `z kael-terminal` 跳回，或用 `zi kael` 从匹配项中选择。 [zoxide 使用文档](https://github.com/ajeetdsouza/zoxide#getting-started)

### 浏览、搜索和阅读

运行 `y config` 打开 **Yazi**。用方向键浏览，按 `q` 退出，Zsh 会切换到你最后所在的目录。`y` 是 `yazi` 的快捷别名，`ya pkg list` 用来查看 Yazi 插件。 [Yazi 快速入门](https://yazi-rs.github.io/docs/quick-start/)

| 工具 | 示例 | 用途 |
| --- | --- | --- |
| **ls** | `ll`、`la`、`l` | 查看详细列表、包含隐藏项的列表或多列列表 |
| **eza** | `lt`、`lgit` | 查看两层目录树，或在列表里显示 Git 状态 |
| **fd** | `fd -e toml . config` | 按扩展名查找配置文件 |
| **ripgrep** | `rg -n 'starship' config` | 搜索文件内容并显示行号 |
| **bat** | `bat bootstrap.sh` | 带语法高亮和行号地阅读脚本 |
| **Glow** | `glow README.md` | 在终端渲染 Markdown |
| **Vim** | `vim README.md` | 按 `i` 编辑，按 `Esc` 后输入 `:wq` 并回车保存退出 |

用 **jq** 从 JSON 中提取所需字段。运行下面的命令可列出 Tabby 的插件依赖。

```sh
jq '.dependencies | keys' config/tabby/plugins/package.json
```

### 任务、资源和运行环境

- **Dooit** 是终端待办工具。运行 `dooit` 后在任务列表按 `a` 新建同级任务，按 `c` 切换完成状态。选中任务后按 `n` 编辑备注，按 `Esc` 保存并返回。按 `Ctrl+N` 切换工作区列表，按 `?` 查看快捷键。 [Dooit 使用文档](https://dooit-org.github.io/dooit/getting_started/basics.html)
- **dust** 用于定位大目录。运行 `dust .` 查看当前目录下的空间占用。
- **btop** 实时显示 CPU、内存、磁盘、网络和进程。运行 `btop` 打开面板，按 `q` 返回。
- **Node.js + npm** 为 Codex CLI 和 Tabby 插件提供运行环境。运行 `node --version` 和 `npm --version` 检查安装。
- **Conda** 适用于已把 Anaconda 安装在 `~/anaconda3` 的用户。Zsh 会自动加载它的初始化脚本，可用 `conda env list` 查看已有环境。

## 工作会话

### tmux

定制 tmux 提供独立窗格边框、焦点高亮、传输进度、浮动窗格菜单，以及显示 Git 和系统资源的状态栏。在 tmux 外运行下方命令，即可启动一个命名会话。

```sh
kael-tmux new-session -A -s dev
```

`kael-tmux` 不带参数时会新建或进入 `work` 会话。前缀键是 `Ctrl+B`，松开后再按下表的键。

| 前缀后的按键 | 操作 |
| --- | --- |
| `%` / `"` | 左右分屏 / 上下分屏 |
| 方向键 | 在窗格之间移动 |
| `F`（大写） | 在浮动窗格和平铺窗格之间切换 |
| `d` | 暂离会话，保留运行中的程序 |

窗格右键菜单也提供分屏、移动和调整大小。暂离后用同一条启动命令重新进入 `dev`，或运行 `kael-tmux list-sessions` 查看当前套接字中的会话。

### Tabby

`tabby` 启动桌面终端，默认进入 Zsh。按 `Ctrl+Shift+T` 新建标签页，按 `Ctrl+Shift+C` 或 `Ctrl+Shift+V` 复制和粘贴。主题和字体随桌面配置部署，两个本地插件分别处理同步输出批次与 tmux 状态栏的对齐。

在 Tabby 中运行 `kael-tmux` 会自动使用专用的 Sixel 套接字。需要普通会话时，从 tmux 外运行 `KAEL_TMUX_MODE=plain kael-tmux`。可通过 `KAEL_TMUX_BIN` 指定已有的兼容构建。

### Codex CLI

首次使用时运行 `codex login`，或按组织提供的方式登录。进入要操作的项目目录后运行 `codex`，例如输入「解释这个仓库的安装流程，并指出主要入口文件」。

Ada 状态栏显示模型、Git 改动，以及可用的周额度和上下文余量。交互式会话在 Tabby 和兼容的 Sixel tmux 会话中支持图像预览。

## 自定义和回滚

- **个人 Zsh 设置**写在 `${XDG_CONFIG_HOME:-$HOME/.config}/kael-terminal/local.zsh`。安装脚本会在 `.zshrc` 中维护加载片段。
- **应用配置**集中在 [`config/`](config/)。在仓库中修改后，可重新运行相应的 `./install.sh` 命令。Vim 配置部署到 `~/.vimrc`，已有的 Neovim 也可加载随附的 [`init.vim`](config/vim/init.vim)。
- **部署备份**位于 `${XDG_STATE_HOME:-$HOME/.local/state}/kael-terminal/backups/`，包含被更新的 Codex 和 Tabby 活动配置。登录凭据、任务数据库、命令历史和运行缓存存放在各设备本地。

```sh
./install.sh rollback --dry-run
./install.sh rollback
```

回滚会恢复最近一次部署涉及的文件和符号链接，已安装的软件包仍可使用。若部署后修改过配置，脚本会停止。先保存需要保留的编辑，再用 `./install.sh rollback --force` 恢复备份。

### 仓库入口

- [`bootstrap.sh`](bootstrap.sh) 安装依赖和工具。[`install.sh`](install.sh) 部署、检查或回滚配置。
- [`libexec/releases.tsv`](libexec/releases.tsv) 列出固定的下载地址和 SHA-256 校验值。
- [`vendor/tmux/`](vendor/tmux/) 保存定制构建的源码快照、补丁和构建说明。
- [`git-local`](git-local) 从项目目录运行 Git，例如 `./git-local status --short`。

## 许可证

项目自有代码和配置按 [MIT 许可证](LICENSE) 发布。随仓库分发的第三方材料适用各自的条款，详见 [tmux 许可](vendor/tmux/COPYING)、[SauceCodePro Nerd Font 许可](fonts/SauceCodeProNF/LICENSE.txt)和 [Starship 图标来源](config/starship/icon-sources.json)。
