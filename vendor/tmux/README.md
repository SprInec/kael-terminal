# 定制 tmux

`independent-borders.tar.gz` 是本机使用的独立边框源码快照。源码来自 tmux 的独立边框 PR，提交为 `acbcff8b41ca9b8d92c2cc83da0a6592e00115da`。源码许可随档案提供，并在此附上 `COPYING`。 [上游 PR #5433](https://github.com/tmux/tmux/pull/5433)

`kael.patch` 从本机的传输进度版与原始快照比对生成，包含边框发光、进度、图像相关游标和绘制修正。普通和 Sixel 会话使用同一份构建源码，由启动器决定是否声明 Sixel 终端能力。

`build.sh` 先校验源码快照，再应用补丁并为目标架构编译。可以通过 `KAEL_BUILD_JOBS` 设置并行任务数。
