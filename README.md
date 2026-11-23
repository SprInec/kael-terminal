# kael-terminel

**简体中文** · [English](README_en.md)

一套可复用的 Linux 终端配置。用同一套脚本部署 Zsh、Starship、定制 tmux、Tabby 和常用命令行工具，也可以在服务器上只安装命令行环境。

## 包含什么

| 组件 | 配置与集成 |
| --- | --- |
| **Zsh · Starship** | 带 Git 远端标识和定制字形的提示符，配合补全、历史建议、语法高亮和可选的 Conda 初始化。 |
| **tmux** | 独立窗格边框、焦点发光、边框传输进度、浮动窗格菜单，以及显示 Git 和系统资源的状态栏。 |
| **Tabby · Codex CLI** | Tabby 配色、字体和快捷键，两个本地 Tabby 插件，Codex 的 Ada 状态栏，以及在 Tabby 和兼容 tmux 会话中显示 Sixel 图像。 |
| **Yazi · Vim · fzf · zoxide** | Yazi 退出时让 Zsh 切换到当前目录，搭配 Vim 编辑、模糊搜索和目录跳转。 |
| **eza · dust · btop · bat · Glow** | 文件列表与目录树、磁盘用量、系统资源监控、代码高亮和 Markdown 阅读。 |
| **Dooit · Atuin** | Dooit 主题、任务备注和鼠标选中即复制，以及默认关闭自动同步的 Atuin 历史。 |

## 快速开始

安装脚本面向使用 APT 的 Ubuntu 和 Debian 系 Linux，提供 **x86_64** 和 **aarch64** 的下载清单。运行前需要 Git、Bash 和 Python 3.10 或更新版本。完整安装需要访问 APT 软件源、GitHub、Node.js、npm 和 PyPI，系统依赖通过 `sudo` 安装。桌面安装前请退出正在运行的 Tabby。

```sh
git clone https://github.com/SprInec/kael-terminel.git
cd kael-terminel
./bootstrap.sh --dry-run
./bootstrap.sh
exec zsh -l
```

预览会列出依赖和将更新的文件。正式安装会校验固定版本的发行包，编译定制 tmux，再写入当前用户的配置。默认桌面模式还会安装 Tabby、插件和字体。首次使用 Codex 时，运行 `codex login` 或使用组织提供的登录方式。

| 场景 | 命令 |
| --- | --- |
| 无桌面的服务器 | `./bootstrap.sh --headless` |
| 已安装系统依赖 | `./bootstrap.sh --skip-apt` |
| 已有工具，只部署配置 | `./install.sh` 或 `./install.sh --headless` |
| 检查工具和插件是否可用 | `./install.sh doctor` 或 `./install.sh doctor --headless` |

`--skip-apt` 可以与 `--headless` 一起使用。在桌面模式下跳过 APT 时，请先安装 Tabby。只部署配置会启用仓库内的两个本地 Tabby 插件，第三方 npm 插件由完整安装流程部署。

## 自定义与回滚

- **本地 Zsh 设置**放在 `${XDG_CONFIG_HOME:-$HOME/.config}/kael-terminal/local.zsh`。安装脚本会在 `.zshrc` 中维护一个加载片段。
- **tmux** 在定制构建可用时由 `kael-tmux` 启动。Tabby 默认使用单独的 Sixel 套接字。使用 `KAEL_TMUX_MODE=plain kael-tmux` 可启动普通会话，用 `KAEL_TMUX_BIN` 可指定兼容的已有构建。
- **配置备份**位于 `${XDG_STATE_HOME:-$HOME/.local/state}/kael-terminal/backups/`。应用本项目的 Codex 和 Tabby 配置时，原活动配置也会存入备份。登录凭据、任务数据库、命令历史和运行缓存由每台设备独立保存。

```sh
./install.sh rollback --dry-run
./install.sh rollback
```

回滚会恢复最近一次部署涉及的文件和符号链接，已安装的软件包仍可使用。如果某个文件在部署后又被编辑过，脚本会停止。保存需要保留的修改后，可以用 `./install.sh rollback --force` 恢复备份版本。

## 项目结构与来源

- [`config/`](config/) 存放应用配置、本地插件和状态栏脚本。
- [`libexec/releases.tsv`](libexec/releases.tsv) 记录上游下载地址和 SHA-256。
- [`vendor/tmux/`](vendor/tmux/) 包含可重新构建的源码快照、补丁和 [tmux 许可](vendor/tmux/COPYING)。
- [`fonts/`](fonts/) 包含终端字体。[SauceCodePro Nerd Font 许可](fonts/SauceCodeProNF/LICENSE.txt)和 [Starship 图标来源](config/starship/icon-sources.json)随仓库提供。
