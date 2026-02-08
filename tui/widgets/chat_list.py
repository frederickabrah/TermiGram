from textual.app import ComposeResult
from textual.widgets import DataTable, Static
from textual.binding import Binding
from textual.events import Key

class ChatList(Static):
    """A widget to display a list of Telegram chats."""

    BINDINGS = [
        Binding("enter", "select_chat", "Select Chat", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield DataTable(id="chat_list_table")

    def on_mount(self) -> None:
        """Set up the table columns when the widget is mounted."""
        table = self.query_one(DataTable)
        table.add_column("Chat", width=30)
        table.add_column("Last Message")
        table.cursor_type = "row" # Enable row selection

    async def action_select_chat(self) -> None:
        """Action to select the currently highlighted chat."""
        table = self.query_one(DataTable)
        if table.cursor_row is not None:
            row_key = table.get_row_key_at(table.cursor_row)
            if row_key:
                # Emit a custom event that the parent app can handle
                self.post_message(DataTable.RowSelected(self, row_key=row_key))
        
