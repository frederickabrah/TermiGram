from textual.app import ComposeResult
from textual.widgets import DataTable, Static

class ChatList(Static):
    """A widget to display a list of Telegram chats."""

    def compose(self) -> ComposeResult:
        yield DataTable(id="chat_list_table")

    def on_mount(self) -> None:
        """Set up the table columns when the widget is mounted."""
        table = self.query_one(DataTable)
        table.add_column("Chat", width=30)
        table.add_column("Last Message")
