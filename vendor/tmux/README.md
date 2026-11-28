# 定制 tmux

`independent-borders.tar.gz` 是本机使用的独立边框源码快照。源码来自 tmux 的独立边框 PR，提交为 `acbcff8b41ca9b8d92c2cc83da0a6592e00115da`。源码许可随档案提供，并在此附上 `COPYING`。 [上游 PR #5433](https://github.com/tmux/tmux/pull/5433)

`kael.patch` 从本机的传输进度版与原始快照比对生成，包含边框发光、进度、图像相关游标和绘制修正。普通和 Sixel 会话使用同一份构建源码，由启动器决定是否声明 Sixel 终端能力。

在独立边框布局中，可用 `kael-tmux set-option -p -t %11 @pane-border-glow pulse-focused` 让指定窗格聚焦时整圈渐亮渐暗、失焦时顺时针流动。使用 `always` 时，两种状态均为顺时针流光。把 `%11` 换成目标窗格的 ID。

默认配置让普通窗格聚焦时以草绿色整圈渐亮渐暗。远程连接窗格采用樱白粉，聚焦时整圈渐亮渐暗，失焦时顺时针流动。Mark 窗格在两种焦点状态下都以阳橙色整圈渐亮渐暗。顺时针亮部扫过标题时会同步提亮文字。

模型训练窗格按前台进程识别，支持常见训练启动器、Python 训练脚本和 Box Avoid 模型评估。识别后采用星光紫，聚焦时整圈渐亮渐暗，失焦时顺时针流动。前台任务结束后恢复普通样式。

用 `kael-tmux task run -- cargo test` 运行编译或测试。运行时边框为天蓝色流光，成功时薄荷绿渐亮一次，失败时珊瑚红短闪两次后常亮。脚本可用 `kael-tmux task start`、`kael-tmux task progress 40`、`kael-tmux task done` 或 `kael-tmux task fail` 明确上报状态。`kael-tmux task clear` 清除状态，可在子命令前用 `--pane %11` 指定窗格。

`tail -F build.log | kael-tmux task watch` 转发日志，并在带 `WARN`、`WARNING`、`ERROR` 或 `CRITICAL` 级别的日志行出现时提示失焦窗格。也可以用 `kael-tmux task warn` 显式上报。琥珀色顶部细线先短亮再转为低亮度，聚焦后清除。Mark 优先显示，任务状态优先于日志告警。

`build.sh` 先校验源码快照，再应用补丁并为目标架构编译。可以通过 `KAEL_BUILD_JOBS` 设置并行任务数。
