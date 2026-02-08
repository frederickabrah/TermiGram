from textual.app import ComposeResult
from textual.widgets import DataTable, Static

class MessageView(Static):
    """A widget to display messages from a selected chat."""

    def compose(self) -> ComposeResult:
        yield DataTable(id="message_table")

    def on_mount(self) -> None:
        """Set up the table columns when the widget is mounted."""
        table = self.query_one(DataTable)
        table.add_column("Time", width=8)
        table.add_column("Sender", width=15)
        table.add_column("Message")
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.add_row("", "", "Select a chat to view messages.")
