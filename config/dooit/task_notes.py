"""Dooit task remarks: right-hand panel with inline editing and autosave."""

from pathlib import Path

from rich.text import Text
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
from textual.binding import Binding
from textual.widgets import TextArea

from dooit.api import manager
from dooit.ui.api import subscribe
from dooit.ui.api.api_components.formatters import extra_formatter
from dooit.ui.api.events import (
    Startup, TodoSelected, TodoRemoved, TodoDescriptionChanged,
    WorkspaceSelected, WorkspaceRemoved,
)
from dooit.ui.screens.index import DualSplit, MainScreen


class NoteStore:
    def __init__(self, engine):
        self.engine = engine
        self.path = Path(engine.url.database)
        self.stamp = None
        self.notes = {}
        with engine.begin() as connection:
            connection.exec_driver_sql("""
                CREATE TABLE IF NOT EXISTS dooit_task_notes (
                    todo_id INTEGER PRIMARY KEY REFERENCES todo(id),
                    body TEXT NOT NULL
                )
            """)
            # A trigger also handles deletion by an older, already-running Dooit.
            connection.exec_driver_sql("""
                CREATE TRIGGER IF NOT EXISTS dooit_task_notes_delete
                AFTER DELETE ON todo BEGIN
                    DELETE FROM dooit_task_notes WHERE todo_id = OLD.id;
                END
            """)
        self.refresh()

    def refresh(self):
        stamp = self.path.stat().st_mtime_ns
        if stamp == self.stamp:
            return False
        with self.engine.connect() as connection:
            notes = dict(connection.exec_driver_sql(
                "SELECT todo_id, body FROM dooit_task_notes"
            ).all())
        changed = notes != self.notes
        self.notes = notes
        self.stamp = stamp
        return changed

    def save(self, todo_id, body, original):
        with self.engine.begin() as connection:
            if connection.exec_driver_sql(
                "SELECT id FROM todo WHERE id = ?", (todo_id,)
            ).scalar() is None:
                raise ValueError("任务已被删除，备注未保存。")
            current = connection.exec_driver_sql(
                "SELECT body FROM dooit_task_notes WHERE todo_id = ?", (todo_id,)
            ).scalar() or ""
            if current != original:
                raise ValueError("备注已在其他窗口修改，请复制当前内容后重新打开。")
            if body:
                connection.exec_driver_sql(
                    "INSERT INTO dooit_task_notes (todo_id, body) VALUES (?, ?) "
                    "ON CONFLICT(todo_id) DO UPDATE SET body = excluded.body",
                    (todo_id, body),
                )
            else:
                connection.exec_driver_sql(
                    "DELETE FROM dooit_task_notes WHERE todo_id = ?", (todo_id,)
                )
        self.stamp = None
        self.refresh()


class RemarkPanel(TextArea, can_focus=True):
    BINDINGS = [
        Binding("n", "edit_note", "编辑备注"),
        Binding("escape", "leave_editor", "返回任务列表", priority=True),
        Binding("tab,shift+tab", "leave_editor", "返回任务列表", priority=True),
        Binding("ctrl+m", "toggle_panel", "显示 / 隐藏备注", priority=True),
        Binding("ctrl+n", "toggle_workspaces", "显示 / 隐藏工作区", priority=True),
    ]
    NOTE_CSS = """
    RemarkPanel {
        height: 1fr; width: 1fr; padding: 1;
        border: solid $background3; background: $background1; color: $foreground1;
        border-title-background: $background1; border-title-color: $foreground1;
        border-subtitle-background: $background1; border-subtitle-color: $foreground1;
    }
    RemarkPanel:focus {
        border: solid $primary;
        border-title-background: $primary; border-title-color: $background1;
    }
    """

    def __init__(self, api, store):
        super().__init__(read_only=True, soft_wrap=True, tab_behavior="focus", id="remark-panel")
        self.api = api
        self.store = store
        self.todo = None
        self.todo_id = None
        self.original = ""
        self.editing = False
        self.save_timer = None
        self.save_error = ""
        # ORM identity keeps drafts from leaking to a new task with a reused ID.
        self.drafts = {}
        self.border_title = "Remark"

    def on_mount(self):
        self.update_layout()
        self.sync_selection()

    def update_layout(self):
        split = self.screen.query_one(DualSplit)
        workspace = self.screen.query_one("#workspace_switcher")
        split.styles.grid_size_rows = 2 if self.display else 1
        split.styles.grid_rows = "2fr 1fr" if self.display else "1fr"
        workspace.styles.row_span = 2 if self.display else 1
        self.styles.column_span = 1 if workspace.display else 2

    def remember_draft(self):
        if self.todo is not None:
            if self.text != self.original:
                self.drafts[self.todo] = (self.text, self.original)
            else:
                self.drafts.pop(self.todo, None)

    def update_hint(self):
        keys = "拖选即复制 · Esc/Tab 返回" if self.editing else "拖选即复制 · n 编辑 · Ctrl+M 显隐"
        error = "保存失败，草稿保留 · " if self.save_error else ""
        self.border_subtitle = error + keys

    def on_mouse_up(self, event):
        # TextArea selections do not use Screen.TextSelected. Copy once the
        # mouse selection finishes, in both read-only and editing modes.
        if event.button == 1 and self._selecting and self.selected_text:
            self.app.copy_to_clipboard(self.selected_text)

    def stop_save_timer(self):
        if self.save_timer is not None:
            self.save_timer.stop()
            self.save_timer = None

    def on_text_area_changed(self, event):
        if event.text_area is self and self.editing:
            self.stop_save_timer()
            self.save_timer = self.set_timer(0.3, self.save_pending)
            self.update_hint()

    def save_pending(self):
        self.stop_save_timer()
        self.remember_draft()
        if self.todo is None or self.text == self.original:
            self.save_error = ""
            self.update_hint()
            return True
        if inspect(self.todo).was_deleted:
            self.drafts.pop(self.todo, None)
            return True
        try:
            self.store.save(self.todo_id, self.text, self.original)
        except (SQLAlchemyError, ValueError, OSError) as error:
            message = str(error)
            if message != self.save_error:
                self.app.notify(f"备注未能保存：{message}", severity="error")
            self.save_error = message
            self.update_hint()
            return False
        self.original = self.text
        self.drafts.pop(self.todo, None)
        self.save_error = ""
        self.update_hint()
        self.api.formatter.todos.trigger()
        return True

    def save_before_quit(self):
        success = self.save_pending()
        # Retry any failed save retained when the user switched tasks.
        for todo, (body, original) in list(self.drafts.items()):
            if todo is self.todo:
                continue
            if inspect(todo).was_deleted:
                self.drafts.pop(todo, None)
                continue
            try:
                self.store.save(todo.id, body, original)
            except (SQLAlchemyError, ValueError, OSError) as error:
                self.app.notify(f"备注尚未保存，暂未退出：{error}", severity="error")
                success = False
            else:
                self.drafts.pop(todo, None)
        return success

    def sync_selection(self):
        if not isinstance(self.app.screen, MainScreen):
            return
        todo = self.api.vars.current_todo
        todo_id = todo.id if todo is not None else None
        if todo is not self.todo:
            self.save_pending()
            self.save_error = ""
            self.editing = False
            self.read_only = True
            self.todo = todo
            self.todo_id = todo_id
            saved = self.store.notes.get(todo_id, "")
            body, self.original = self.drafts.get(todo, (saved, saved))
            self.load_text(body)
        elif not self.editing and todo not in self.drafts:
            saved = self.store.notes.get(todo_id, "")
            if self.text != saved:
                self.load_text(saved)
            self.original = saved
        self.placeholder = "选中任务后按 n 添加备注" if todo is None else "暂无备注，按 n 编辑"
        self.tooltip = Text(f"Remark · {todo.description}") if todo is not None else None
        self.update_hint()

    def focus_tasks(self):
        tree = self.api.vars.todos_tree or self.api.vars.workspaces_tree
        tree.focus()

    def action_leave_editor(self):
        self.save_pending()
        self.editing = False
        self.read_only = True
        self.update_hint()
        self.focus_tasks()

    def on_blur(self):
        # Flush mouse focus changes without pulling focus back.
        self.save_pending()
        self.editing = False
        self.read_only = True
        self.update_hint()

    def check_action(self, action, parameters):
        if action == "edit_note":
            return not self.editing
        return super().check_action(action, parameters)

    def action_edit_note(self):
        self.start_edit()

    def start_edit(self):
        self.store.stamp = None
        self.store.refresh()
        self.sync_selection()
        if self.todo_id is None:
            self.api.notify("请先在任务列表中选中一个任务")
            return
        self.display = True
        self.update_layout()
        self.editing = True
        self.read_only = False
        self.update_hint()
        self.focus()

    def action_toggle_panel(self):
        if self.has_focus:
            self.action_leave_editor()
        self.display = not self.display
        self.update_layout()
        if self.display:
            self.sync_selection()

    def action_toggle_workspaces(self):
        self.action_leave_editor()
        self.api.keys.keybinds["NORMAL"]["<ctrl+n>"].callback()



@subscribe(Startup)
def setup_task_notes(api, _):
    store = NoteStore(manager.engine)
    panel = RemarkPanel(api, store)
    screen = api.app.screen
    api.css.inject_css(RemarkPanel.NOTE_CSS, _id="task-notes")
    api.app.refresh_css()
    screen.query_one(DualSplit).mount(panel)

    # Dooit's main key router assumes ModelTree focus. Let TextArea process its
    # own navigation and editing bindings while the remark editor has focus.
    handle_main_key = screen.handle_key

    async def handle_key(event):
        if panel.has_focus:
            return False
        return await handle_main_key(event)

    screen.handle_key = handle_key
    quit_app = api.app.action_quit

    async def quit_after_save():
        if panel.save_before_quit():
            await quit_app()

    api.app.action_quit = quit_after_save
    workspace_binding = api.keys.keybinds["NORMAL"]["<ctrl+n>"]

    def toggle_workspaces():
        workspace_binding.callback()
        panel.update_layout()

    @extra_formatter
    def note_marker(value, todo):
        return value + " [dim]✎[/dim]" if store.notes.get(todo.id) else value

    @subscribe(TodoSelected, TodoRemoved, TodoDescriptionChanged, WorkspaceSelected, WorkspaceRemoved)
    def selection_changed(_api, event):
        if isinstance(event, TodoRemoved):
            panel.drafts.pop(event.todo, None)
            if panel.todo is event.todo:
                panel.stop_save_timer()
                panel.todo = None
                panel.todo_id = None
        api.app.call_later(panel.sync_selection)

    def refresh_notes():
        if isinstance(api.app.screen, MainScreen):
            if store.refresh():
                api.formatter.todos.trigger()
            panel.sync_selection()

    api.plugin_manager.register(selection_changed)
    api.keys.set("n", panel.start_edit, description="编辑 Remark 备注", group="备注")
    # Legacy terminals send Ctrl+M as Enter; only NORMAL mode uses this alias.
    api.keys.set(["<ctrl+m>", "<enter>"], panel.action_toggle_panel,
                 description="显示 / 隐藏 Remark（Ctrl+M）", group="备注")
    api.keys.set("<ctrl+n>", toggle_workspaces, description=workspace_binding.description)
    api.formatter.todos.description.add(note_marker, id="task-note-marker")
    api.app.set_interval(1, refresh_notes)
