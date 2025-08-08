from textual.app import ComposeResult
from textual.widgets import RichLog, Static

class MessageView(Static):
    """A widget to display messages from a selected chat."""

    def compose(self) -> ComposeResult:
        yield RichLog(id="message_log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        """Clear the log and display a welcome message."""
        log = self.query_one(RichLog)
        log.write("Select a chat to view messages.")
