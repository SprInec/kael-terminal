"""Local Dooit text selection with copy on mouse release and clipboard shortcuts."""

from rich.cells import cell_len
from rich.segment import Segment
from rich.style import Style
from textual.binding import Binding
from textual.strip import Strip
from textual.widgets import OptionList, TextArea

from dooit.ui.api import subscribe
from dooit.ui.api.events import Startup
from dooit.ui.screens.index import MainScreen
from dooit.ui.widgets.trees.model_tree import ModelTree


def render_selectable_line(self, y):
    strip = OptionList.render_line(self, y)
    row = self.scroll_offset.y + y
    selection = self.text_selection
    if selection is not None and (span := selection.get_span(row)) is not None:
        start, end = span
        text = strip.text
        left = cell_len(text[:start])
        right = strip.cell_length if end == -1 else cell_len(text[:end])
        strip = Strip.join([
            strip.crop(0, left),
            Strip(Segment.apply_style(
                strip.crop(left, right),
                post_style=Style(bgcolor=self.screen.get_component_rich_style("screen--selection").bgcolor),
            )),
            strip.crop(right),
        ])
    return strip.apply_offsets(0, row)


def get_tree_selection(self, selection):
    # OptionList renders rows directly, so Widget.get_selection has no text.
    style = self.get_visual_style("option-list--option")
    selected = []
    for y in range(len(self._lines)):
        if (span := selection.get_span(y)) is not None:
            start, end = span
            line = self._get_line(style, y).text
            selected.append((line[start:] if end == -1 else line[start:end]).rstrip())
    return "\n".join(selected), "\n"


def copy_screen_selection(self, event):
    if text := self.get_selected_text():
        self.app.copy_to_clipboard(text)


MainScreen.on_text_selected = copy_screen_selection
ModelTree.ALLOW_SELECT = True
ModelTree.render_line = render_selectable_line
ModelTree.get_selection = get_tree_selection


@subscribe(Startup)
def setup_text_selection(api, _):
    app = api.app

    async def copy_or_quit():
        focused = app.focused
        if isinstance(focused, TextArea):
            text = None if focused.selection.is_empty else focused.selected_text
        else:
            text = app.screen.get_selected_text()
        if text is None:
            await app.action_quit()
        elif text:
            app.copy_to_clipboard(text)

    app.action_copy_or_quit = copy_or_quit
    app._bindings.key_to_bindings["ctrl+c"] = [
        Binding("ctrl+c", "copy_or_quit", "复制选中文字 / 无选区时退出", priority=True),
    ]
    app._bindings.key_to_bindings["ctrl+q"] = [
        Binding("ctrl+q", "quit", "退出", priority=True),
    ]
