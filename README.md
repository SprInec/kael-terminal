# kael-terminel

把本机的终端环境搬到另一台设备。完整安装面向 Ubuntu / Debian 系 Linux，提供 x86_64 和 aarch64 的软件包清单。配置来自 Ubuntu 22.04 x86_64。

## 新设备安装

把仓库复制到目标设备，或用随附的 Git bundle 克隆。bundle 可以通过 U 盘或私人文件共享传输。

```sh
git clone /path/to/kael-terminel.bundle kael-terminel
cd kael-terminel
./bootstrap.sh --dry-run
./bootstrap.sh
exec zsh -l
```

`bootstrap.sh` 使用 APT 安装基础依赖，从上游下载并校验固定版本，编译带图像支持的定制 tmux，并部署配置。命令行工具安装在 `${XDG_DATA_HOME:-$HOME/.local/share}/kael-terminal/bin`。桌面模式还安装 Tabby、字体和 Tabby 插件。部署前请退出目标机上运行的 Tabby，以便下次启动读取新配置。

| 用途 | 命令 |
| --- | --- |
| 无桌面的服务器 | `./bootstrap.sh --headless` |
| 系统依赖已经装好 | `./bootstrap.sh --skip-apt` |
| 只应用配置，使用已有工具 | `./install.sh` 或 `./install.sh --headless` |
| 检查工具和 Tabby 插件 | `./install.sh doctor` 或 `./install.sh doctor --headless` |
| 预览和恢复最近一次配置部署 | `./install.sh rollback --dry-run`，确认后运行 `./install.sh rollback` |

完整安装需要访问 GitHub、Node.js、npm、PyPI 以及系统 APT 源。`--skip-apt` 可以复用预装依赖。APT 所需的软件包可用 `./bootstrap.sh --dry-run` 查看。回滚恢复配置文件和受管理的链接，已安装的软件包仍可继续使用。

## 迁移的配置

| 组件 | 内容 |
| --- | --- |
| Zsh、Starship | 原提示符、Git 远端标识、定制字形、补全、建议、高亮和可选 Conda 初始化 |
| tmux | 绿色状态栏、独立边框、焦点发光、传输进度、浮动窗格菜单、下划线光标和焦点事件 |
| Codex CLI | 本机模型与推理参数、Ada Git 与额度状态栏、Tabby／tmux Sixel 图像预览 |
| Tabby | 日夜配色、字体、快捷键、Sixel、本地输出批处理与 tmux 胶囊对齐插件，以及已配置的四个 npm 插件 |
| Yazi、Vim、fzf、zoxide | Yazi 退出后切换目录，默认编辑器为 Vim，fzf 文件选择，zoxide 跳转 |
| eza、dust、btop、bat、Glow | `lt` 和 `lgit` 别名、磁盘用量、btop 显示设置、语法高亮及 Markdown 阅读 |
| Dooit、Atuin | Dooit 的主题、任务备注和鼠标文本复制，Atuin 的本地历史和回车确认 |

Tabby 的默认启动配置改用 Zsh，并安装 Starship Prompt Icons 和 SauceCodePro Nerd Font Mono。已有 Tabby npm 插件的普通目录会继续被使用。只使用 `install.sh` 时，直接启用仓库内的两个本地 Tabby 插件。其余四个插件由 `bootstrap.sh` 安装。

Zsh 在定制构建可用时把 `tmux` 指向 `kael-tmux`。Tabby 使用独立的 Sixel 套接字，其他终端使用普通套接字。原有 tmux 会话可用各自的原启动命令访问。`KAEL_TMUX_MODE=plain kael-tmux` 可以显式选择普通套接字。只部署配置时，可以用 `KAEL_TMUX_BIN=/path/to/tmux` 复用支持独立边框、发光和传输进度的已有构建。

新设备首次使用 Codex 时，运行 `codex login`，或使用该设备现有的组织登录方式。Atuin 默认使用本地历史。

## 本地修改和备份

`install.sh` 更新目标文件前，把原文件或符号链接放在 `${XDG_STATE_HOME:-$HOME/.local/state}/kael-terminal/backups/`。它保留普通 `.zshrc` 的现有内容并维护一个加载片段。本机原始的纯加载配置会直接换成等效入口。主机专属的 Zsh 定制可以放到 `${XDG_CONFIG_HOME:-$HOME/.config}/kael-terminal/local.zsh`。

Codex 和 Tabby 的便携配置会替换各自的活动配置。登录凭据、Dooit 任务数据库、Atuin 历史和运行缓存留在各自设备。原 Codex 项目信任记录和 Tabby SSH 连接资料随原配置保存在部署备份中。回滚遇到部署后修改过的文件时会停止，保存后可指定 `--force`。

部署支持 `XDG_CONFIG_HOME`、`XDG_DATA_HOME`、`XDG_CACHE_HOME`、`XDG_STATE_HOME`，以及各应用使用的 `ZDOTDIR`、`CODEX_HOME`、`TABBY_CONFIG_DIRECTORY`、`ATUIN_HOME` 和 `ATUIN_CONFIG_DIR`。部署与使用时请保持这些变量一致。

## Git 与来源

在当前受限工作区使用 `./git-local status`、`./git-local log -1` 等命令。工作区的 `.git` 挂载为只读，Git 元数据存放在 `.git-kael`。从 bundle 克隆后的目录使用标准 `git`。本地仓库可由用户关联到自己的私人远端。

- [上游下载地址与 SHA-256](libexec/releases.tsv)
- [定制 tmux 的源码与本机补丁](vendor/tmux/README.md)
- [Starship 字形来源](config/starship/icon-sources.json)
- [SauceCodePro Nerd Font 许可](fonts/SauceCodeProNF/LICENSE.txt)
