from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import DataTable, Header, Footer, Static
from textual.containers import Vertical

class SearchResultsScreen(ModalScreen):
    """A modal screen to display search results."""

    def __init__(self, query: str, results: list):
        super().__init__()
        self.query = query
        self.results = results

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Static(f"Search results for: [bold]{self.query}[/bold]")
            yield DataTable(id="search_results_table")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_column("Chat", width=20)
        table.add_column("Sender", width=15)
        table.add_column("Message")

        for result in self.results:
            chat_title = result.chat.title or result.chat.first_name or "Unknown Chat"
            sender_name = result.sender.first_name or result.sender.username or "Unknown Sender"
            message_text = result.message or "[No text]"
            table.add_row(chat_title, sender_name, message_text, key=result.id)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Return the selected message ID when a row is selected."""
        self.dismiss(event.row_key)
