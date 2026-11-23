"""Dooit palette matched to the current Tabby dark terminal theme."""

from dooit.api.theme import DooitThemeBase
from dooit.ui.api import DooitAPI, subscribe
from dooit.ui.api.events import Startup
from dooit_extras.scripts import toggle_workspaces

@subscribe(Startup)
def setup_workspace_toggle(api: DooitAPI, _):
    api.keys.set("<ctrl+n>", toggle_workspaces(api))
    api.vars.always_expand_todos = False  # Allow z to show/hide todo children.


class TabbyTerminalTheme(DooitThemeBase):
    _name = "tabby-terminal"

    background1 = "#171717"
    background2 = "#202020"
    background3 = "#333333"

    foreground1 = "#cacaca"
    foreground2 = "#dedacf"
    foreground3 = "#dedacf"

    red = "#ff615a"
    orange = "#f58c80"
    yellow = "#ebd99c"
    green = "#b1e969"
    blue = "#5da9f6"
    purple = "#ddaaff"
    magenta = "#e86aff"
    cyan = "#82fff7"

    primary = green
    secondary = "#9ab96c"


@subscribe(Startup)
def match_terminal_theme(api: DooitAPI, _: Startup):
    api.css.set_theme(TabbyTerminalTheme)
    api.css.inject_css(
        """
        Dashboard {
            border: solid $background3;
            color: $foreground1;
        }

        ModelTree {
            border: solid $background3;
            border-title-background: $background1;
            border-title-color: $foreground1;
            color: $foreground1;

            .option-list--option-highlighted,
            .option-list--option-hover-highlighted {
                background: #282d22;
                color: $foreground2;
            }

            &:focus {
                border: solid $primary;
                border-title-background: $primary;
                border-title-color: $background1;

                .option-list--option-highlighted,
                .option-list--option-hover-highlighted {
                    background: #344329;
                    color: $foreground3;
                }
            }
        }

        App:blur StatusBar {
            background: $background1;
            color: $foreground1;
        }

        DooitKeyTable .description {
            color: $foreground1;
            text-style: none;
        }
        """,
        _id="tabby-terminal-theme",
    )
    api.app.refresh_css()

# BEGIN managed-tmux-status-tags
# Use the same ANSI green as tmux; the terminal supplies the exact palette color.
from rich.style import Style as _TmuxTagStyle
from dooit.ui.api import timer as _tmux_tag_timer
from dooit.ui.api.events import ModeChanged as _TmuxModeChanged
from dooit.ui.widgets.bars import StatusBarWidget as _TmuxStatusWidget
import dooit.utils.default_config as _tmux_default_status
from rich.text import Text as _WorkspaceLabelText
from textual.css.query import NoMatches as _WorkspaceNoMatches
from dooit.ui.api.events import (
    WorkspaceSelected as _WorkspaceSelected,
    WorkspaceDescriptionChanged as _WorkspaceDescriptionChanged,
    WorkspaceRemoved as _WorkspaceRemoved,
)

_TMUX_STATUS_TAG_BACKGROUND = "green"


def _tmux_tag_background(text):
    text.stylize(_TmuxTagStyle(bgcolor=_TMUX_STATUS_TAG_BACKGROUND))
    return text


@subscribe(_TmuxModeChanged)
def _tmux_status_mode(api: DooitAPI, event):
    return _tmux_tag_background(_tmux_default_status.get_mode(api, event))


@_tmux_tag_timer(1)
def _tmux_status_clock(api: DooitAPI):
    return _tmux_tag_background(_tmux_default_status.get_clock(api))


@subscribe(Startup, _WorkspaceSelected, _WorkspaceDescriptionChanged, _WorkspaceRemoved, _TmuxModeChanged)
def _tmux_status_workspace(api: DooitAPI, event):
    workspace = None
    if isinstance(event, _WorkspaceSelected):
        workspace = event.workspace
    elif not isinstance(event, Startup):
        try:
            workspace = api.vars.current_workspace
        except (_WorkspaceNoMatches, IndexError):
            pass
    name = "NONE"
    if workspace is not None and not workspace.is_root:
        name = workspace.description.replace("\n", " ").replace("\r", " ") or "未命名 Workspace"
    return _tmux_tag_background(
        _WorkspaceLabelText(f" {name} ", style=_TmuxTagStyle(color=api.vars.theme.background1))
    )


class _TmuxFocusStatusWidget(_TmuxStatusWidget):
    def __init__(self, api: DooitAPI, func, width=None):
        super().__init__(func, width=width)
        self._api = api

    def render(self):
        label = super().render()
        if self._api.app.app_focus:
            return label
        theme = self._api.vars.theme
        return _WorkspaceLabelText(
            label.plain,
            style=_TmuxTagStyle(color=theme.foreground1, bgcolor=theme.background1),
        )


class _TmuxWorkspaceWidget(_TmuxFocusStatusWidget):
    def __init__(self, api: DooitAPI):
        super().__init__(api, _tmux_status_workspace)

    def render(self):
        label = super().render()
        label.truncate(max(12, self._api.app.size.width // 3), overflow="ellipsis")
        self.width = label.cell_len
        return label


@subscribe(Startup)
def _tmux_status_bar(api: DooitAPI, _: Startup):
    # Preserve terminal ANSI colors instead of Textual converting them to RGB.
    api.app.ansi_color = True
    api.bar.set([
        _TmuxFocusStatusWidget(api, _tmux_status_mode),
        _TmuxStatusWidget(lambda: "", width=0),
        _TmuxFocusStatusWidget(api, _tmux_status_clock),
        _TmuxStatusWidget(lambda: " ", width=1),
        _TmuxWorkspaceWidget(api),
    ])
    # Repaint cached labels immediately when tmux delivers FocusIn / FocusOut.
    api.app.watch(api.app, "app_focus", lambda: api.app.bar.refresh())
# END managed-tmux-status-tags

# BEGIN managed-task-notes
from task_notes import setup_task_notes
# END managed-task-notes

# BEGIN managed-subtask-markers
from dooit.api import Todo as _SubtaskTodo
from dooit.ui.api.api_components.formatters import extra_formatter as _subtask_formatter
from dooit.ui.widgets.trees import TodosTree as _SubtaskTree


@_subtask_formatter
def _subtask_marker(value, todo, api):
    if not todo.todos:
        return value
    owner = todo.parent
    while isinstance(owner, _SubtaskTodo):
        owner = owner.parent
    tree = next((tree for tree in api.app.screen.query(_SubtaskTree) if tree.model == owner), None)
    expanded = tree is not None and (tree.filter_refresh or tree.is_node_expaned(todo.uuid))
    marker = "▾" if expanded else "▸"
    return f"[{api.vars.theme.primary}]{marker}[/] {value}"


@subscribe(Startup)
def setup_subtask_markers(api: DooitAPI, _):
    api.formatter.todos.description.add(_subtask_marker, id="subtask-marker")
# END managed-subtask-markers

# BEGIN managed-text-selection
from text_selection import setup_text_selection
# END managed-text-selection
